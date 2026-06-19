from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ci_vibe_lab.db import insert_run
from ci_vibe_lab.scenarios import (
    TEST_COMMAND,
    get_scenario,
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


def write_artifact(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path.resolve())


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


def run_one(
    *,
    scenario_id: str,
    model: str | None,
    agent: str | None,
    db_path: Path,
    runs_dir: Path,
    opencode_bin: str,
    timeout: int,
    auto_approve: bool,
    no_opencode: bool,
    json_format: bool,
) -> str:
    scenario = get_scenario(scenario_id)
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
            prompt=scenario.prompt,
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
    write_hidden_test(scenario_id, workdir)
    hidden = run_command(TEST_COMMAND, workdir, timeout=timeout)

    prompt_path = write_artifact(artifact_dir / "prompt.txt", scenario.prompt + "\n")
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
        "prompt": scenario.prompt,
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
    }
    insert_run(db_path, row)
    return run_id


def expand_scenarios(value: str) -> list[str]:
    if value == "all":
        return scenario_ids()
    get_scenario(value)
    return [value]


def print_scenarios() -> None:
    for scenario_id in scenario_ids():
        scenario = get_scenario(scenario_id)
        print(f"{scenario.id}: {scenario.title}")
        print(f"  {scenario.description}")


def prepare_scenario(args: argparse.Namespace) -> None:
    if not args.scenario:
        raise SystemExit("prepare requires --challenge or --scenario")
    scenario = write_scenario(args.scenario, Path(args.out))
    print(f"Wrote {scenario.id} scenario to {Path(args.out).resolve()}")
    print(f"CI command: {' '.join(TEST_COMMAND)}")


def run_scenarios(args: argparse.Namespace) -> None:
    if not args.scenario:
        raise SystemExit("run requires --challenge or --scenario")
    db_path = Path(args.db)
    runs_dir = Path(args.runs_dir)
    selected = expand_scenarios(args.scenario)
    run_ids = []
    for index in range(args.runs):
        for scenario_id in selected:
            print(f"Running {scenario_id} ({index + 1}/{args.runs})...")
            run_id = run_one(
                scenario_id=scenario_id,
                model=args.model,
                agent=args.agent,
                db_path=db_path,
                runs_dir=runs_dir,
                opencode_bin=args.opencode_bin,
                timeout=args.timeout,
                auto_approve=args.auto_approve,
                no_opencode=args.no_opencode,
                json_format=not args.default_format,
            )
            run_ids.append(run_id)
            print(f"  stored run_id={run_id}")
    print(f"Saved {len(run_ids)} run(s) to {db_path.resolve()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local OpenCode CI vibe eval challenges.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available challenges.")

    prepare = subparsers.add_parser("prepare", help="Write a challenge repo without running OpenCode.")
    prepare.add_argument("--challenge", "--scenario", dest="scenario", choices=scenario_ids())
    prepare.add_argument("--out", required=True, help="Destination directory.")

    run = subparsers.add_parser("run", help="Run one or more challenges.")
    run.add_argument("--challenge", "--scenario", dest="scenario", help="Challenge id or 'all'.")
    run.add_argument("--model", help="OpenCode provider/model. Omit to use OpenCode's default.")
    run.add_argument("--agent", default="build", help="OpenCode agent name.")
    run.add_argument("--db", default=os.environ.get("CI_VIBE_DB", str(DEFAULT_DB)))
    run.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    run.add_argument("--opencode-bin", default=os.environ.get("OPENCODE_BIN", "opencode"))
    run.add_argument("--timeout", type=int, default=900)
    run.add_argument("--runs", type=int, default=1)
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "list":
        print_scenarios()
        return 0
    if args.command == "prepare":
        prepare_scenario(args)
        return 0
    if args.command == "run":
        run_scenarios(args)
        return 0
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
