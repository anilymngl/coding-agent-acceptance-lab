from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ci_vibe_lab.db import connect, insert_run
from ci_vibe_lab.scenarios import (
    PROMPT_MODES,
    TEST_COMMAND,
    get_scenario,
    pack_ids,
    scenario_ids,
    write_hidden_test,
    write_scenario,
)


DEFAULT_DB = Path("data/results.sqlite")
DEFAULT_RUNS_DIR = Path("runs")


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    output: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class PatchStats:
    files_touched: int
    added_lines: int
    deleted_lines: int

    @property
    def changed_lines(self) -> int:
        return self.added_lines + self.deleted_lines


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_command(command: list[str], cwd: Path, *, timeout: int) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = completed.stdout
        if completed.stderr:
            output += ("\n" if output else "") + completed.stderr
        return CommandResult(command=command, returncode=completed.returncode, output=output)
    except subprocess.TimeoutExpired as exc:
        output = ""
        if exc.stdout:
            output += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", "replace")
        if exc.stderr:
            output += ("\n" if output else "")
            output += exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", "replace")
        output += f"\nCommand timed out after {timeout} seconds."
        return CommandResult(command=command, returncode=124, output=output)


def git_diff(workdir: Path) -> str:
    completed = subprocess.run(
        ["git", "diff", "--binary"],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout + completed.stderr


def git_patch_stats(workdir: Path) -> PatchStats:
    names = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    files_touched = len([line for line in names.stdout.splitlines() if line.strip()])
    numstat = subprocess.run(
        ["git", "diff", "--numstat"],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    added = 0
    deleted = 0
    for line in numstat.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        try:
            added += int(parts[0])
            deleted += int(parts[1])
        except ValueError:
            # Binary or unknown numstat rows use "-"; count the file but not line churn.
            continue
    return PatchStats(files_touched=files_touched, added_lines=added, deleted_lines=deleted)


def estimate_review_minutes(stats: PatchStats) -> float:
    estimate = 3.0 + (1.5 * stats.files_touched) + (0.15 * stats.changed_lines)
    return round(max(4.0, min(30.0, estimate)), 2)


def write_artifact(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path.resolve())


def read_artifact(path_value: object) -> str:
    if not path_value:
        return ""
    path = Path(str(path_value))
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def artifact_line(label: str, path_value: object) -> str:
    if not path_value:
        return f"- {label}: <missing path>"
    path = Path(str(path_value))
    if not path.exists():
        return f"- {label}: {path} (missing)"
    return f"- {label}: {path} ({path.stat().st_size} bytes)"


def build_opencode_command(
    *,
    opencode_bin: str,
    workdir: Path,
    prompt: str,
    model: str | None,
    agent: str | None,
    auto_approve: bool,
    json_format: bool,
) -> list[str]:
    command = [opencode_bin, "run", "--dir", str(workdir)]
    if json_format:
        command.extend(["--format", "json"])
    if model:
        command.extend(["--model", model])
    if agent:
        command.extend(["--agent", agent])
    if auto_approve:
        command.append("--dangerously-skip-permissions")
    command.append(prompt)
    return command


def run_opencode(command: list[str], workdir: Path, *, timeout: int) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if not isinstance(stdout, str):
            stdout = stdout.decode("utf-8", "replace")
        if not isinstance(stderr, str):
            stderr = stderr.decode("utf-8", "replace")
        stderr += f"\nOpenCode timed out after {timeout} seconds."
        return 124, stdout, stderr


def load_scenario_audit(db_path: Path, scenario_id: str) -> dict[str, object]:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM scenario_audits WHERE scenario = ?",
            (scenario_id,),
        ).fetchone()
    return dict(row) if row else {}


def run_one(
    *,
    scenario_id: str,
    experiment_id: str,
    model: str | None,
    agent: str | None,
    db_path: Path,
    runs_dir: Path,
    opencode_bin: str,
    timeout: int,
    auto_approve: bool,
    no_opencode: bool,
    json_format: bool,
    prompt_mode: str,
) -> str:
    scenario = get_scenario(scenario_id)
    prompt = scenario.render_prompt(prompt_mode)  # type: ignore[arg-type]
    audit = load_scenario_audit(db_path, scenario_id)
    started_at = utc_now()
    start = time.monotonic()
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{scenario_id}-{uuid.uuid4().hex[:8]}"
    workdir = (runs_dir / "worktrees" / run_id).resolve()
    artifact_dir = (runs_dir / "artifacts" / run_id).resolve()
    write_scenario(scenario_id, workdir)

    baseline = run_command(TEST_COMMAND, workdir, timeout=timeout)

    if no_opencode:
        opencode_command: list[str] = ["<skipped>", "--no-opencode"]
        opencode_exit_code: int | None = None
        opencode_stdout = ""
        opencode_stderr = "OpenCode invocation skipped by --no-opencode."
    else:
        opencode_command = build_opencode_command(
            opencode_bin=opencode_bin,
            workdir=workdir,
            prompt=prompt,
            model=model,
            agent=agent,
            auto_approve=auto_approve,
            json_format=json_format,
        )
        opencode_exit_code, opencode_stdout, opencode_stderr = run_opencode(
            opencode_command,
            workdir,
            timeout=timeout,
        )

    public = run_command(TEST_COMMAND, workdir, timeout=timeout)
    patch = git_diff(workdir)
    patch_stats = git_patch_stats(workdir)
    estimated_review_minutes = estimate_review_minutes(patch_stats)
    write_hidden_test(scenario_id, workdir)
    hidden = run_command(TEST_COMMAND, workdir, timeout=timeout)

    prompt_path = write_artifact(artifact_dir / "prompt.txt", prompt + "\n")
    baseline_output_path = write_artifact(artifact_dir / "baseline.txt", baseline.output)
    opencode_stdout_path = write_artifact(artifact_dir / "opencode_stdout.jsonl", opencode_stdout)
    opencode_stderr_path = write_artifact(artifact_dir / "opencode_stderr.txt", opencode_stderr)
    public_output_path = write_artifact(artifact_dir / "public.txt", public.output)
    hidden_output_path = write_artifact(artifact_dir / "hidden.txt", hidden.output)
    patch_path = write_artifact(artifact_dir / "patch.diff", patch)

    ended_at = utc_now()
    duration = time.monotonic() - start
    manifest = scenario.manifest()
    row = {
        "run_id": run_id,
        "experiment_id": experiment_id,
        "prompt_mode": prompt_mode,
        "contract_visibility": str(audit.get("contract_visibility", "")),
        "scenario_audit_status": str(audit.get("audit_status", "")),
        "scenario_audit_version": str(audit.get("audit_version", "")),
        "scenario": scenario.id,
        "scenario_title": scenario.title,
        "challenge_pack": scenario.pack,
        "category": scenario.category,
        "difficulty": scenario.difficulty,
        "vibe": scenario.vibe,
        "tags": json.dumps(manifest["tags"]),
        "trap": scenario.trap,
        "expected_behavior": json.dumps(manifest["expected_behavior"]),
        "success_signals": json.dumps(manifest["success_signals"]),
        "failure_modes": json.dumps(manifest["failure_modes"]),
        "rubric": json.dumps(manifest["rubric"]),
        "model": model or "<opencode-default>",
        "agent": agent or "",
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration,
        "workdir": str(workdir),
        "prompt": prompt,
        "opencode_command": json.dumps(opencode_command),
        "opencode_exit_code": opencode_exit_code,
        "baseline_pass": int(baseline.passed),
        "public_pass": int(public.passed),
        "hidden_pass": int(hidden.passed),
        "baseline_output": baseline.output,
        "opencode_stdout": opencode_stdout,
        "opencode_stderr": opencode_stderr,
        "public_output": public.output,
        "hidden_output": hidden.output,
        "patch": patch,
        "artifact_dir": str(artifact_dir),
        "prompt_path": prompt_path,
        "baseline_output_path": baseline_output_path,
        "opencode_stdout_path": opencode_stdout_path,
        "opencode_stderr_path": opencode_stderr_path,
        "public_output_path": public_output_path,
        "hidden_output_path": hidden_output_path,
        "patch_path": patch_path,
        "patch_files_touched": patch_stats.files_touched,
        "patch_added_lines": patch_stats.added_lines,
        "patch_deleted_lines": patch_stats.deleted_lines,
        "patch_changed_lines": patch_stats.changed_lines,
        "estimated_review_minutes": estimated_review_minutes,
        "manual_review_minutes": None,
        "review_decision": "",
    }
    insert_run(db_path, row)
    return run_id


def expand_scenarios(value: str, *, pack: str | None = None) -> list[str]:
    if value == "all":
        selected = scenario_ids(pack)
        if not selected:
            valid = ", ".join(pack_ids())
            raise ValueError(f"Unknown or empty pack {pack!r}. Valid packs: {valid}")
        return selected
    get_scenario(value)
    if pack and get_scenario(value).pack != pack:
        raise ValueError(f"Challenge {value!r} is not in pack {pack!r}.")
    return [value]


def print_scenarios(*, pack: str | None = None) -> None:
    for scenario_id in scenario_ids(pack):
        scenario = get_scenario(scenario_id)
        print(f"{scenario.id} [{scenario.pack}]: {scenario.title}")
        print(f"  {scenario.description}")


def prepare_scenario(args: argparse.Namespace) -> None:
    if not args.scenario:
        raise SystemExit("prepare requires --challenge or --scenario")
    if args.pack and get_scenario(args.scenario).pack != args.pack:
        raise SystemExit(f"Challenge {args.scenario!r} is not in pack {args.pack!r}.")
    scenario = write_scenario(args.scenario, Path(args.out))
    print(f"Wrote {scenario.id} scenario to {Path(args.out).resolve()}")
    print(f"CI command: {' '.join(TEST_COMMAND)}")


def _completed_attempts(
    db_path: Path, *, model: str, experiment_id: str, prompt_mode: str, scenario_ids_: list[str]
) -> set[tuple[str, int]]:
    """Return a set of (scenario_id, attempt_index) pairs already stored for this experiment.

    Scoped to experiment_id so different experiment runs never collide.
    """
    if not db_path.exists():
        return set()
    try:
        conn = connect(db_path)
        done: set[tuple[str, int]] = set()
        for sid in scenario_ids_:
            rows = conn.execute(
                """
                SELECT opencode_exit_code
                FROM runs
                WHERE scenario = ?
                  AND model = ?
                  AND experiment_id = ?
                  AND prompt_mode = ?
                ORDER BY rowid
                """,
                (sid, model, experiment_id, prompt_mode),
            ).fetchall()
            for attempt_index, _row in enumerate(rows):
                done.add((sid, attempt_index))
        conn.close()
        return done
    except Exception:
        return set()


def run_scenarios(args: argparse.Namespace) -> None:
    if not args.scenario:
        raise SystemExit("run requires --challenge or --scenario")
    db_path = Path(args.db)
    runs_dir = Path(args.runs_dir)
    selected = expand_scenarios(args.scenario, pack=args.pack)
    model_key = args.model or "<opencode-default>"

    # Mint or reattach to an experiment ID.
    pack_slug = args.pack or "custom"
    if getattr(args, "experiment_id", None):
        experiment_id = args.experiment_id
        print(f"Experiment: {experiment_id} (reattached)")
    else:
        experiment_id = (
            f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            f"-{pack_slug}-{uuid.uuid4().hex[:8]}"
        )
        print(f"Experiment: {experiment_id}")

    completed: set[tuple[str, int]] = set()
    if args.resume:
        completed = _completed_attempts(
            db_path,
            model=model_key,
            experiment_id=experiment_id,
            prompt_mode=args.prompt_mode,
            scenario_ids_=selected,
        )
        if completed:
            print(f"Resume: skipping {len(completed)} already-completed attempt(s).")

    skipped_timeout: set[str] = set()
    if getattr(args, "skip_timeouts", False) and db_path.exists():
        try:
            conn = connect(db_path)
            rows = conn.execute(
                """
                SELECT DISTINCT scenario
                FROM runs
                WHERE model = ?
                  AND experiment_id = ?
                  AND prompt_mode = ?
                  AND opencode_exit_code = 124
                """,
                (model_key, experiment_id, args.prompt_mode),
            ).fetchall()
            conn.close()
            skipped_timeout = {r[0] for r in rows}
            if skipped_timeout:
                print(f"Skip-timeouts: skipping {len(skipped_timeout)} scenario(s) that previously timed out.")
        except Exception:
            pass

    run_ids = []
    skipped = 0
    for index in range(args.runs):
        for scenario_id in selected:
            if scenario_id in skipped_timeout:
                print(f"Skipping {scenario_id} ({index + 1}/{args.runs}) — previous timeout.")
                skipped += 1
                continue
            if (scenario_id, index) in completed:
                print(f"Skipping {scenario_id} ({index + 1}/{args.runs}) — already complete.")
                skipped += 1
                continue
            print(f"Running {scenario_id} ({index + 1}/{args.runs})...")
            run_id = run_one(
                scenario_id=scenario_id,
                experiment_id=experiment_id,
                model=args.model,
                agent=args.agent,
                db_path=db_path,
                runs_dir=runs_dir,
                opencode_bin=args.opencode_bin,
                timeout=args.timeout,
                auto_approve=args.auto_approve,
                no_opencode=args.no_opencode,
                json_format=not args.default_format,
                prompt_mode=args.prompt_mode,
            )
            run_ids.append(run_id)
            print(f"  stored run_id={run_id}")
    if skipped:
        print(f"Skipped {skipped} attempt(s).")
    print(f"Saved {len(run_ids)} run(s) to {db_path.resolve()}")


def load_inspection_row(
    db_path: Path,
    *,
    run_id: str | None,
    latest: bool,
    scenario: str | None,
    model: str | None,
) -> sqlite3.Row:
    connection = connect(db_path)
    clauses = []
    params: list[object] = []
    if run_id:
        clauses.append("run_id = ?")
        params.append(run_id)
    if scenario:
        clauses.append("scenario = ?")
        params.append(scenario)
    if model:
        clauses.append("model = ?")
        params.append(model)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    ordering = "ORDER BY id DESC" if latest else "ORDER BY id ASC"
    rows = list(connection.execute(f"SELECT * FROM runs {where} {ordering} LIMIT 2", params))
    connection.close()
    if not rows:
        raise SystemExit("No run matched the inspection filters.")
    if not latest and not run_id and len(rows) > 1:
        raise SystemExit("Multiple runs matched. Use --run-id or --latest.")
    return rows[0]


def print_artifact_section(title: str, content: str) -> None:
    print(f"\n## {title}")
    print(content if content else "<empty>")


def inspect_run(args: argparse.Namespace) -> None:
    if not args.run_id and not args.latest:
        raise SystemExit("inspect requires --run-id or --latest")
    row = load_inspection_row(
        Path(args.db),
        run_id=args.run_id,
        latest=args.latest,
        scenario=args.scenario,
        model=args.model,
    )
    print(f"# Run Inspection: {row['run_id']}")
    print("")
    print(f"- Scenario: {row['scenario']} [{row['challenge_pack']}]")
    print(f"- Prompt mode: {row['prompt_mode']}")
    print(f"- Contract visibility: {row['contract_visibility']}")
    print(f"- Scenario audit: {row['scenario_audit_status']} ({row['scenario_audit_version']})")
    print(f"- Model: {row['model']}")
    print(f"- Agent: {row['agent']}")
    print(f"- Workdir: {row['workdir']}")
    print(f"- Artifact dir: {row['artifact_dir']}")
    print(f"- OpenCode exit code: {row['opencode_exit_code']}")
    print(f"- Baseline/Public/Hidden pass: {row['baseline_pass']}/{row['public_pass']}/{row['hidden_pass']}")
    print(f"- Duration seconds: {float(row['duration_seconds']):.1f}")
    print("")
    print("## OpenCode Command")
    try:
        command = json.loads(str(row["opencode_command"]))
    except json.JSONDecodeError:
        command = row["opencode_command"]
    print(json.dumps(command, indent=2) if isinstance(command, list) else str(command))
    print("")
    print("## Artifact Files")
    for label, column in [
        ("agent prompt", "prompt_path"),
        ("baseline test output", "baseline_output_path"),
        ("raw OpenCode stdout JSONL", "opencode_stdout_path"),
        ("OpenCode stderr", "opencode_stderr_path"),
        ("public test output", "public_output_path"),
        ("hidden test output", "hidden_output_path"),
        ("patch diff", "patch_path"),
    ]:
        print(artifact_line(label, row[column]))
    if not args.full:
        print("")
        print("Use --full to print complete prompt, raw OpenCode output, test output, and patch.")
        return

    print_artifact_section("Agent Prompt", read_artifact(row["prompt_path"]))
    print_artifact_section("Baseline Test Output", read_artifact(row["baseline_output_path"]))
    print_artifact_section("OpenCode Stdout JSONL", read_artifact(row["opencode_stdout_path"]))
    print_artifact_section("OpenCode Stderr", read_artifact(row["opencode_stderr_path"]))
    print_artifact_section("Public Test Output", read_artifact(row["public_output_path"]))
    print_artifact_section("Hidden Test Output", read_artifact(row["hidden_output_path"]))
    print_artifact_section("Patch Diff", read_artifact(row["patch_path"]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local OpenCode CI vibe eval challenges.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available challenges.")
    list_parser.add_argument("--pack", choices=pack_ids(), help="Only list challenges in this pack.")

    prepare = subparsers.add_parser("prepare", help="Write a challenge repo without running OpenCode.")
    prepare.add_argument("--challenge", "--scenario", dest="scenario", choices=scenario_ids())
    prepare.add_argument("--pack", choices=pack_ids(), help="Require the challenge to belong to this pack.")
    prepare.add_argument("--out", required=True, help="Destination directory.")

    run = subparsers.add_parser("run", help="Run one or more challenges.")
    run.add_argument("--challenge", "--scenario", dest="scenario", help="Challenge id or 'all'.")
    run.add_argument("--pack", choices=pack_ids(), help="When --challenge all, run only this pack.")
    run.add_argument("--model", help="OpenCode provider/model. Omit to use OpenCode's default.")
    run.add_argument("--agent", default="build", help="OpenCode agent name.")
    run.add_argument("--db", default=os.environ.get("CI_VIBE_DB", str(DEFAULT_DB)))
    run.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    run.add_argument("--opencode-bin", default=os.environ.get("OPENCODE_BIN", "opencode"))
    run.add_argument("--timeout", type=int, default=900)
    run.add_argument("--runs", type=int, default=1)
    run.add_argument(
        "--prompt-mode",
        choices=PROMPT_MODES,
        default="sparse",
        help="Prompt contract exposure lane: sparse, contract_visible, or audit_visible.",
    )
    run.add_argument(
        "--auto-approve",
        action="store_true",
        help="Pass OpenCode --dangerously-skip-permissions for unattended generated worktrees.",
    )
    run.add_argument("--no-opencode", action="store_true", help="Skip OpenCode and only record test state.")
    run.add_argument(
        "--default-format",
        action="store_true",
        help="Use OpenCode formatted output instead of raw JSON events.",
    )
    run.add_argument(
        "--experiment-id",
        default=None,
        metavar="EXPERIMENT_ID",
        help=(
            "Reattach to an existing experiment by ID (printed at the start of every run). "
            "Use with --resume to continue exactly where that experiment left off."
        ),
    )
    run.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Skip (scenario, attempt) pairs already stored in the DB for the same model. "
            "Safe to re-run the same command after an interruption."
        ),
    )
    run.add_argument(
        "--skip-timeouts",
        action="store_true",
        help="Skip scenarios that timed out (exit code 124) in a previous run.",
    )

    inspect = subparsers.add_parser("inspect", help="Inspect saved run inputs, outputs, and artifacts.")
    inspect.add_argument("--db", default=os.environ.get("CI_VIBE_DB", str(DEFAULT_DB)))
    inspect.add_argument("--run-id", help="Exact run_id to inspect.")
    inspect.add_argument("--latest", action="store_true", help="Inspect the latest row matching filters.")
    inspect.add_argument("--scenario", help="Optional scenario filter for --latest.")
    inspect.add_argument("--model", help="Optional model filter for --latest.")
    inspect.add_argument("--full", action="store_true", help="Print full artifact contents.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "list":
        print_scenarios(pack=args.pack)
        return 0
    if args.command == "prepare":
        prepare_scenario(args)
        return 0
    if args.command == "run":
        run_scenarios(args)
        return 0
    if args.command == "inspect":
        inspect_run(args)
        return 0
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
