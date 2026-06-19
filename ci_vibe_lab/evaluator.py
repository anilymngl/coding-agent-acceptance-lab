from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent


DEFAULT_DB = Path("data/results.sqlite")
DEFAULT_OUT_DIR = Path("runs/evaluator-agent")

VERDICTS = {"pass", "public_green_hidden_red", "public_red", "blocked"}
ROOT_CAUSE_CATEGORIES = {
    "no_issue_detected",
    "missed_hidden_contract",
    "incomplete_domain_policy",
    "edge_case_gap",
    "wrong_fix_strategy",
    "insufficient_verification",
    "public_failure",
    "evaluator_blocked",
}
SEVERITIES = {"low", "medium", "high"}
EVIDENCE_SOURCES = {
    "challenge_contract",
    "patch",
    "public_test_output",
    "hidden_test_output",
    "final_worktree",
    "evaluator_validation",
}
REVIEW_SOURCES = {"evaluator_agent", "deterministic_fallback"}
VALIDATION_STATUSES = {"valid", "invalid", "not_run"}


@dataclass(frozen=True)
class ReviewResult:
    run_id: str
    scenario: str
    review_dir: Path
    agent_exit_code: int | None
    duration_seconds: float


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def load_rows(db_path: Path, *, hidden_only: bool, pack: str | None) -> list[sqlite3.Row]:
    clauses = []
    params: list[object] = []
    if hidden_only:
        clauses.append("hidden_pass = 0")
    if pack:
        clauses.append("challenge_pack = ?")
        params.append(pack)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect(db_path) as connection:
        return list(connection.execute(f"SELECT * FROM runs {where} ORDER BY id", params))


def json_list(value: object) -> list[str]:
    if value is None:
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def read_text(path_value: object, fallback: str = "") -> str:
    if not path_value:
        return fallback
    path = Path(str(path_value))
    if not path.exists():
        return fallback
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def snapshot_files(workdir: Path, *, max_chars: int = 18000) -> str:
    if not workdir.exists():
        return "Workdir not found."
    chunks: list[str] = []
    total = 0
    for path in sorted(workdir.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix not in {".py", ".json", ".md", ".log", ".txt"}:
            continue
        relative = path.relative_to(workdir)
        text = path.read_text(encoding="utf-8", errors="replace")
        chunk = f"\n--- {relative} ---\n{text}"
        if total + len(chunk) > max_chars:
            chunks.append("\n--- snapshot truncated ---\n")
            break
        chunks.append(chunk)
        total += len(chunk)
    return "".join(chunks).strip()


def compact_test_failures(output: str) -> list[str]:
    markers = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(("FAIL:", "ERROR:")):
            markers.append(stripped)
    return markers


def make_packet(row: sqlite3.Row) -> str:
    patch = read_text(row["patch_path"], str(row["patch"] or ""))
    public_output = read_text(row["public_output_path"], str(row["public_output"] or ""))
    hidden_output = read_text(row["hidden_output_path"], str(row["hidden_output"] or ""))
    workdir = Path(str(row["workdir"]))
    expected = "\n".join(f"- {item}" for item in json_list(row["expected_behavior"])) or "- n/a"
    success = "\n".join(f"- {item}" for item in json_list(row["success_signals"])) or "- n/a"
    failure_modes = "\n".join(f"- {item}" for item in json_list(row["failure_modes"])) or "- n/a"
    hidden_markers = "\n".join(f"- {item}" for item in compact_test_failures(hidden_output)) or "- n/a"

    return dedent(
        f"""
        # Evaluation Packet

        ## Run Metadata

        - Run ID: `{row['run_id']}`
        - Challenge: `{row['scenario']}` - {row['scenario_title']}
        - Pack: `{row['challenge_pack']}`
        - Category: `{row['category']}`
        - Difficulty: `{row['difficulty']}`
        - Model under test: `{row['model']}`
        - Public pass: `{row['public_pass']}`
        - Hidden pass: `{row['hidden_pass']}`
        - Duration seconds: `{float(row['duration_seconds']):.1f}`

        ## Challenge Intent

        {row['vibe']}

        ## Trap / Hidden Contract

        {row['trap']}

        ## Expected Behavior

        {expected}

        ## Success Signals

        {success}

        ## Failure Modes This Challenge Is Meant To Catch

        {failure_modes}

        ## Hidden Failure Markers

        {hidden_markers}

        ## Patch Produced By Model Under Test

        ```diff
        {patch}
        ```

        ## Public Test Output

        ```text
        {public_output}
        ```

        ## Hidden Test Output

        ```text
        {hidden_output}
        ```

        ## Final Worktree Snapshot

        ```text
        {snapshot_files(workdir)}
        ```
        """
    ).strip() + "\n"


def evaluator_prompt(review_dir: Path | None = None) -> str:
    if review_dir is None:
        packet_path = "./EVALUATION_PACKET.md"
        json_path = "./evaluation.json"
        markdown_path = "./evaluation.md"
    else:
        resolved = review_dir.resolve()
        packet_path = str(resolved / "EVALUATION_PACKET.md")
        json_path = str(resolved / "evaluation.json")
        markdown_path = str(resolved / "evaluation.md")
    return dedent(
        f"""
        You are the evaluator agent for a coding-agent benchmark.

        Non-negotiable constraints:
        - Do not fix code.
        - Read only `{packet_path}`.
        - Write only `{json_path}` and `{markdown_path}`.
        - Do not search parent directories.
        - Do not use or write any other `runs/...` path.
        - Do not edit EVALUATION_PACKET.md.
        - Use only evidence present in `{packet_path}`.
        - Every evidence.quote must be an exact contiguous substring copied from `{packet_path}`.
        - Keep evidence.quote short: prefer one exact line or one exact bullet.
        - For patch evidence, quote one exact added/removed/context line, not a reconstructed diff hunk.
        - If the model under test passed public tests but failed hidden tests, the verdict must be public_green_hidden_red.
        - If public tests failed, the verdict must be public_red.
        - Do not invent missing tests, hidden intent, source files, or facts.

        Your job is to analyze the run in EVALUATION_PACKET.md and write two files:

        1. evaluation.json
        2. evaluation.md

        Use this JSON shape exactly, with no extra top-level keys:

        {{
          "schema_version": "ci-vibe-evaluator/v1",
          "review_source": "evaluator_agent",
          "validation_status": "valid",
          "verdict": "pass" | "public_green_hidden_red" | "public_red" | "blocked",
          "root_cause_category": "no_issue_detected" | "missed_hidden_contract" | "incomplete_domain_policy" | "edge_case_gap" | "wrong_fix_strategy" | "insufficient_verification" | "public_failure" | "evaluator_blocked",
          "root_cause": "one concise sentence",
          "missed_contract": "one concise sentence",
          "patch_quality": 1-5,
          "debug_discipline": 1-5,
          "severity": "low" | "medium" | "high",
          "confidence": 0.0-1.0,
          "evidence": [
            {{
              "source": "challenge_contract" | "patch" | "public_test_output" | "hidden_test_output" | "final_worktree",
              "quote": "exact quote from EVALUATION_PACKET.md",
              "interpretation": "why this quote matters"
            }}
          ],
          "recommendation": "what the model under test should have done",
          "review_limits": "briefly state any uncertainty or limits"
        }}

        Scoring:
        - patch_quality: 1 means harmful or superficial, 3 means plausible but incomplete,
          5 means production-quality and contract-complete.
        - debug_discipline: 1 means random or no verification, 3 means ran tests but stopped
          too early, 5 means inspected the contract and verified the right behavior.

        Evidence requirements:
        - For a hidden failure, include at least two evidence objects.
        - At least one hidden-failure evidence object must cite hidden_test_output.
        - At least one hidden-failure evidence object must cite patch or challenge_contract.
        - Before writing evaluation.json, verify every evidence.quote appears verbatim in `{packet_path}`.

        evaluation.md should be short but useful:
        - verdict
        - missed contract
        - evidence
        - recommendation

        Before writing, check your own JSON against the schema above.
        """
    ).strip()


def clamp_int(value: object, *, low: int = 1, high: int = 5, default: int = 3) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def clamp_float(value: object, *, low: float = 0.0, high: float = 1.0, default: float = 0.5) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def evidence_item(source: str, quote: str, interpretation: str) -> dict[str, str]:
    return {
        "source": source,
        "quote": quote,
        "interpretation": interpretation,
    }


def deterministic_review(row: sqlite3.Row) -> dict[str, object]:
    public_pass = int(row["public_pass"])
    hidden_pass = int(row["hidden_pass"])
    if public_pass and hidden_pass:
        verdict = "pass"
        severity = "low"
        patch_quality = 4
        root_cause_category = "no_issue_detected"
        root_cause = "The patch satisfied both visible and hidden acceptance checks."
        missed_contract = "No missed hidden contract was detected by this challenge."
        recommendation = "Keep this as a passing reference trace; human review can still assess taste."
    elif public_pass and not hidden_pass:
        verdict = "public_green_hidden_red"
        severity = "medium"
        patch_quality = 3
        root_cause_category = "missed_hidden_contract"
        root_cause = "The patch fixed the visible failure but missed part of the challenge contract."
        missed_contract = str(row["trap"] or "Hidden acceptance defines the missed contract.")
        recommendation = "Use hidden output plus challenge success signals to extend the patch beyond the public test."
    else:
        verdict = "public_red"
        severity = "high"
        patch_quality = 1
        root_cause_category = "public_failure"
        root_cause = "The patch did not get the visible CI check green."
        missed_contract = "Visible CI failure remains unresolved."
        recommendation = "Re-run public tests, inspect the failing source, and repair the visible failure first."

    hidden_output = read_text(row["hidden_output_path"], str(row["hidden_output"] or ""))
    markers = compact_test_failures(hidden_output)
    evidence = [
        evidence_item("hidden_test_output", marker, "Unittest failure marker from hidden acceptance.")
        for marker in markers
    ]
    if not evidence:
        evidence = [
            evidence_item(
                "evaluator_validation",
                f"public_pass={public_pass}, hidden_pass={hidden_pass}",
                "Stored pass/fail flags from the result database.",
            )
        ]

    return {
        "schema_version": "ci-vibe-evaluator/v1",
        "review_source": "deterministic_fallback",
        "validation_status": "not_run",
        "verdict": verdict,
        "root_cause_category": root_cause_category,
        "root_cause": root_cause,
        "missed_contract": missed_contract,
        "patch_quality": patch_quality,
        "debug_discipline": 3 if public_pass else 1,
        "severity": severity,
        "confidence": 0.7 if public_pass != hidden_pass else 0.8,
        "evidence": evidence,
        "recommendation": recommendation,
        "review_limits": "Deterministic fallback used; no evaluator-agent semantic review was available.",
    }


def review_markdown(row: sqlite3.Row, review: dict[str, object]) -> str:
    evidence = review.get("evidence") if isinstance(review.get("evidence"), list) else []
    evidence_lines = []
    for item in evidence:
        if isinstance(item, dict):
            evidence_lines.append(
                f"- `{item.get('source', '')}`: {item.get('quote', '')} — {item.get('interpretation', '')}"
            )
        else:
            evidence_lines.append(f"- {item}")
    evidence_text = "\n".join(evidence_lines) or "- n/a"
    return "\n".join(
        [
            f"# Evaluation Review: {row['scenario']}",
            "",
            f"- Verdict: **{review.get('verdict')}**",
            f"- Source: **{review.get('review_source')}**",
            f"- Validation: **{review.get('validation_status')}**",
            f"- Severity: **{review.get('severity')}**",
            f"- Patch quality: **{review.get('patch_quality')}/5**",
            f"- Debug discipline: **{review.get('debug_discipline')}/5**",
            f"- Confidence: **{review.get('confidence')}**",
            "",
            "## Root Cause",
            "",
            str(review.get("root_cause", "")),
            "",
            "## Missed Contract",
            "",
            str(review.get("missed_contract", "")),
            "",
            "## Evidence",
            "",
            evidence_text,
            "",
            "## Recommendation",
            "",
            str(review.get("recommendation", "")),
            "",
            "## Review Limits",
            "",
            str(review.get("review_limits", "")),
            "",
        ]
    )


def validation_error_review(row: sqlite3.Row, errors: list[str]) -> dict[str, object]:
    quote = "; ".join(errors[:4])
    return {
        "schema_version": "ci-vibe-evaluator/v1",
        "review_source": "deterministic_fallback",
        "validation_status": "invalid",
        "verdict": "blocked",
        "root_cause_category": "evaluator_blocked",
        "root_cause": "The evaluator-agent output failed schema or evidence validation.",
        "missed_contract": "The evaluator review cannot be trusted until validation errors are fixed.",
        "patch_quality": 1,
        "debug_discipline": 1,
        "severity": "high",
        "confidence": 1.0,
        "evidence": [
            evidence_item("evaluator_validation", quote or "unknown validation error", "Evaluator validation failure.")
        ],
        "recommendation": "Rerun the evaluator with a stricter prompt or inspect evaluation.agent.json manually.",
        "review_limits": "This review is about evaluator validity, not model-under-test patch quality.",
    }


def validate_review(review: dict[str, object], packet: str, row: sqlite3.Row) -> list[str]:
    errors: list[str] = []
    expected_keys = {
        "schema_version",
        "review_source",
        "validation_status",
        "verdict",
        "root_cause_category",
        "root_cause",
        "missed_contract",
        "patch_quality",
        "debug_discipline",
        "severity",
        "confidence",
        "evidence",
        "recommendation",
        "review_limits",
    }
    extra = set(review) - expected_keys
    missing = expected_keys - set(review)
    if extra:
        errors.append(f"extra top-level keys: {sorted(extra)}")
    if missing:
        errors.append(f"missing top-level keys: {sorted(missing)}")
    if review.get("schema_version") != "ci-vibe-evaluator/v1":
        errors.append("schema_version must be ci-vibe-evaluator/v1")
    if review.get("review_source") not in REVIEW_SOURCES:
        errors.append("review_source enum violation")
    if review.get("validation_status") not in VALIDATION_STATUSES:
        errors.append("validation_status enum violation")
    if review.get("verdict") not in VERDICTS:
        errors.append("verdict enum violation")
    if review.get("root_cause_category") not in ROOT_CAUSE_CATEGORIES:
        errors.append("root_cause_category enum violation")
    if review.get("severity") not in SEVERITIES:
        errors.append("severity enum violation")
    for key in ["root_cause", "missed_contract", "recommendation", "review_limits"]:
        if not isinstance(review.get(key), str) or not str(review.get(key)).strip():
            errors.append(f"{key} must be non-empty text")
    for key in ["patch_quality", "debug_discipline"]:
        value = review.get(key)
        if not isinstance(value, int) or not 1 <= value <= 5:
            errors.append(f"{key} must be integer 1-5")
    confidence = review.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        errors.append("confidence must be number 0.0-1.0")

    public_pass = int(row["public_pass"])
    hidden_pass = int(row["hidden_pass"])
    verdict = review.get("verdict")
    if public_pass and not hidden_pass and verdict != "public_green_hidden_red":
        errors.append("public green + hidden red rows must use verdict public_green_hidden_red")
    if not public_pass and verdict != "public_red":
        errors.append("public red rows must use verdict public_red")
    if public_pass and hidden_pass and verdict not in {"pass", "blocked"}:
        errors.append("public+hidden pass rows should use verdict pass unless evaluator blocked")

    evidence = review.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a non-empty list")
        evidence = []
    hidden_cited = False
    patch_or_contract_cited = False
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"evidence[{index}] must be an object")
            continue
        source = item.get("source")
        quote = item.get("quote")
        interpretation = item.get("interpretation")
        if source not in EVIDENCE_SOURCES:
            errors.append(f"evidence[{index}].source enum violation")
        if source == "hidden_test_output":
            hidden_cited = True
        if source in {"patch", "challenge_contract"}:
            patch_or_contract_cited = True
        if not isinstance(quote, str) or not quote.strip():
            errors.append(f"evidence[{index}].quote must be non-empty")
        elif quote not in packet and source != "evaluator_validation":
            errors.append(f"evidence[{index}].quote is not an exact packet substring")
        if not isinstance(interpretation, str) or not interpretation.strip():
            errors.append(f"evidence[{index}].interpretation must be non-empty")
    if public_pass and not hidden_pass:
        if len(evidence) < 2:
            errors.append("hidden failures require at least two evidence objects")
        if not hidden_cited:
            errors.append("hidden failures require hidden_test_output evidence")
        if not patch_or_contract_cited:
            errors.append("hidden failures require patch or challenge_contract evidence")
    return errors


def normalize_review(review: dict[str, object]) -> dict[str, object]:
    normalized = dict(review)
    normalized["patch_quality"] = clamp_int(normalized.get("patch_quality"))
    normalized["debug_discipline"] = clamp_int(normalized.get("debug_discipline"))
    normalized["confidence"] = clamp_float(normalized.get("confidence"))
    return normalized


def build_opencode_evaluator_command(
    *,
    review_dir: Path | None,
    model: str,
    agent: str | None,
    opencode_bin: str,
    auto_approve: bool,
) -> list[str]:
    command = [
        opencode_bin,
        "run",
        "--dir",
        str(review_dir.resolve()) if review_dir is not None else ".",
        "--format",
        "json",
        "--model",
        model,
    ]
    if agent:
        command.extend(["--agent", agent])
    if auto_approve:
        command.append("--dangerously-skip-permissions")
    command.append(evaluator_prompt(review_dir))
    return command


def run_opencode_evaluator(
    *,
    review_dir: Path,
    model: str,
    agent: str | None,
    opencode_bin: str,
    timeout: int,
    auto_approve: bool,
) -> tuple[int, str, str]:
    command = build_opencode_evaluator_command(
        review_dir=review_dir,
        model=model,
        agent=agent,
        opencode_bin=opencode_bin,
        auto_approve=auto_approve,
    )
    try:
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        stderr += f"\nEvaluator timed out after {timeout} seconds."
        return 124, stdout, stderr


def ensure_review_workspace(review_dir: Path) -> None:
    # OpenCode anchors tools to the nearest git workspace. The evaluator packet
    # must be isolated from the parent repo so model runs cannot drift into old
    # run artifacts or write to a sibling review directory.
    subprocess.run(
        ["git", "init", "-q"],
        cwd=review_dir,
        capture_output=True,
        text=True,
        check=False,
    )


def evaluate_row(
    row: sqlite3.Row,
    *,
    out_dir: Path,
    model: str | None,
    agent: str | None,
    opencode_bin: str,
    timeout: int,
    auto_approve: bool,
) -> ReviewResult:
    start = time.monotonic()
    review_dir = out_dir / str(row["run_id"])
    review_dir.mkdir(parents=True, exist_ok=True)
    ensure_review_workspace(review_dir)
    packet = make_packet(row)
    write_text(review_dir / "EVALUATION_PACKET.md", packet)
    write_text(review_dir / "prompt.txt", evaluator_prompt(review_dir) + "\n")

    agent_exit_code: int | None = None
    stderr = ""
    if model:
        for filename in ["evaluation.json", "evaluation.md", "evaluation.agent.json", "validation_errors.json"]:
            path = review_dir / filename
            if path.exists():
                path.unlink()
        agent_exit_code, stdout, stderr = run_opencode_evaluator(
            review_dir=review_dir,
            model=model,
            agent=agent,
            opencode_bin=opencode_bin,
            timeout=timeout,
            auto_approve=auto_approve,
        )
        write_text(review_dir / "evaluator_stdout.jsonl", stdout)
        write_text(review_dir / "evaluator_stderr.txt", stderr)

    agent_review_path = review_dir / "evaluation.json"
    if model and agent_review_path.exists():
        finalize_agent_review(review_dir, row, packet)
    elif model:
        errors = agent_missing_errors(agent_exit_code=agent_exit_code, stderr=stderr)
        write_text(review_dir / "validation_errors.json", json.dumps(errors, indent=2) + "\n")
        review = validation_error_review(row, errors)
        write_text(review_dir / "evaluation.json", json.dumps(review, indent=2, sort_keys=True) + "\n")
        write_text(review_dir / "evaluation.md", review_markdown(row, review))
    elif not (review_dir / "evaluation.json").exists():
        review = deterministic_review(row)
        write_text(review_dir / "evaluation.json", json.dumps(review, indent=2, sort_keys=True) + "\n")
        write_text(review_dir / "evaluation.md", review_markdown(row, review))

    return ReviewResult(
        run_id=str(row["run_id"]),
        scenario=str(row["scenario"]),
        review_dir=review_dir,
        agent_exit_code=agent_exit_code,
        duration_seconds=time.monotonic() - start,
    )


def finalize_agent_review(review_dir: Path, row: sqlite3.Row, packet: str) -> None:
    agent_review_path = review_dir / "evaluation.json"
    try:
        raw_review = agent_review_path.read_text(encoding="utf-8")
        agent_review = json.loads(raw_review)
    except json.JSONDecodeError as exc:
        raw_review = agent_review_path.read_text(encoding="utf-8", errors="replace")
        agent_review = {}
        errors = [f"invalid JSON: {exc}"]
    else:
        if not isinstance(agent_review, dict):
            errors = ["evaluation.json top-level value must be an object"]
        else:
            agent_review = normalize_review(agent_review)
            errors = validate_review(agent_review, packet, row)

    write_text(review_dir / "evaluation.agent.json", raw_review)
    if errors:
        write_text(review_dir / "validation_errors.json", json.dumps(errors, indent=2) + "\n")
        review = validation_error_review(row, errors)
        write_text(review_dir / "evaluation.json", json.dumps(review, indent=2, sort_keys=True) + "\n")
        write_text(review_dir / "evaluation.md", review_markdown(row, review))
        return

    agent_review["validation_status"] = "valid"
    agent_review["review_source"] = "evaluator_agent"
    write_text(review_dir / "evaluation.json", json.dumps(agent_review, indent=2, sort_keys=True) + "\n")
    if not (review_dir / "evaluation.md").exists():
        write_text(review_dir / "evaluation.md", review_markdown(row, agent_review))


def agent_missing_errors(
    *,
    agent_exit_code: int | None,
    stderr: str,
) -> list[str]:
    errors = ["evaluation.json was not created by evaluator agent"]
    if agent_exit_code is not None:
        errors.append(f"agent_exit_code={agent_exit_code}")
    first_error_line = next((line.strip() for line in stderr.splitlines() if line.strip()), "")
    if first_error_line:
        errors.append(first_error_line[:300])
    return errors


def load_review(review_dir: Path) -> dict[str, object]:
    path = review_dir / "evaluation.json"
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def extract_scenario_from_packet(packet_text: str, fallback: str) -> str:
    match = re.search(r"-\s*Challenge:\s*`([^`]+)`", packet_text)
    return match.group(1) if match else fallback


def load_validation_errors(review_dir: Path) -> list[str]:
    path = review_dir / "validation_errors.json"
    if not path.exists():
        return []
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["validation_errors.json is not valid JSON"]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return ["validation_errors.json top-level value is not a list"]


def build_summary_report(review_root: Path, out_path: Path) -> None:
    rows = []
    for review_dir in sorted(path for path in review_root.iterdir() if path.is_dir()):
        review = load_review(review_dir)
        if not review:
            continue
        packet = review_dir / "EVALUATION_PACKET.md"
        scenario = review_dir.name
        if packet.exists():
            scenario = extract_scenario_from_packet(packet.read_text(encoding="utf-8"), review_dir.name)
        rows.append((scenario, review_dir.name, review, load_validation_errors(review_dir)))

    lines = [
        "# Evaluator Agent Summary",
        "",
        f"Review root: `{review_root}`",
        f"Generated at: {utc_now()}",
        "",
        "| Challenge | Verdict | Source | Validation | Severity | Patch Quality | Debug Discipline | Root Cause |",
        "|---|---|---|---|---|---:|---:|---|",
    ]
    for scenario, run_id, review, _errors in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{scenario}`",
                    str(review.get("verdict", "")),
                    str(review.get("review_source", "")),
                    str(review.get("validation_status", "")),
                    str(review.get("severity", "")),
                    str(review.get("patch_quality", "")),
                    str(review.get("debug_discipline", "")),
                    str(review.get("root_cause", "")).replace("|", "/"),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Details", ""])
    for scenario, run_id, review, errors in rows:
        evidence = review.get("evidence")
        evidence_count = len(evidence) if isinstance(evidence, list) else 0
        lines.extend(
            [
                f"### `{scenario}`",
                "",
                f"- Run ID: `{run_id}`",
                f"- Verdict: **{review.get('verdict', '')}**",
                f"- Source: **{review.get('review_source', '')}**",
                f"- Validation: **{review.get('validation_status', '')}**",
                f"- Evidence objects: {evidence_count}",
                f"- Confidence: {review.get('confidence', '')}",
                f"- Missed contract: {review.get('missed_contract', '')}",
                f"- Recommendation: {review.get('recommendation', '')}",
                "",
            ]
        )
        if errors:
            lines.extend(["Validation errors:", ""])
            lines.extend([f"- {error}" for error in errors])
            lines.append("")
    write_text(out_path, "\n".join(lines) + "\n")


def run_reviews(args: argparse.Namespace) -> None:
    rows = load_rows(Path(args.db), hidden_only=args.hidden_only, pack=args.pack)
    if not rows:
        print("No rows matched.")
        return
    out_dir = Path(args.out)
    results = []
    for row in rows:
        print(f"Evaluating {row['scenario']} ({row['run_id']})...")
        result = evaluate_row(
            row,
            out_dir=out_dir,
            model=args.model,
            agent=args.agent,
            opencode_bin=args.opencode_bin,
            timeout=args.timeout,
            auto_approve=args.auto_approve,
        )
        results.append(result)
        print(f"  wrote {result.review_dir}")
    if args.report:
        build_summary_report(out_dir, Path(args.report))
        print(f"Wrote {Path(args.report).resolve()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run evaluator-agent analysis over saved CI Vibe Lab runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Create evaluation packets and optional evaluator-agent reviews.")
    run.add_argument("--db", default=str(DEFAULT_DB))
    run.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    run.add_argument("--pack", help="Only evaluate rows from this challenge pack.")
    run.add_argument("--hidden-only", action="store_true", help="Only evaluate hidden-test failures.")
    run.add_argument("--model", help="Optional OpenCode model for evaluator-agent review.")
    run.add_argument("--agent", help="Optional OpenCode agent name for evaluator-agent review.")
    run.add_argument("--opencode-bin", default="opencode")
    run.add_argument("--timeout", type=int, default=900)
    run.add_argument("--auto-approve", action="store_true")
    run.add_argument("--report", help="Write a Markdown summary report after reviews.")

    report = subparsers.add_parser("report", help="Build summary report from existing evaluator review directory.")
    report.add_argument("--reviews", required=True)
    report.add_argument("--out", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        run_reviews(args)
        return 0
    if args.command == "report":
        build_summary_report(Path(args.reviews), Path(args.out))
        print(f"Wrote {Path(args.out).resolve()}")
        return 0
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
