from __future__ import annotations

import argparse
import json
import re
import selectors
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ci_vibe_lab.db import upsert_evaluator_review
from ci_vibe_lab.scenarios import TEST_COMMAND, get_scenario, write_hidden_test, write_scenario


DEFAULT_DB = Path("data/results.sqlite")
DEFAULT_OUT_DIR = Path("runs/evaluator-agent")

class EvaluationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal[
        "challenge_contract",
        "patch",
        "public_test_output",
        "hidden_test_output",
        "final_worktree",
        "evaluator_validation",
    ]
    quote: str = Field(min_length=1)
    interpretation: str = Field(min_length=1)


class EvaluationReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["ci-vibe-evaluator/v1"]
    review_source: Literal["evaluator_agent", "deterministic_fallback"]
    validation_status: Literal["valid", "invalid", "not_run"]
    verdict: Literal["pass", "public_green_hidden_red", "public_red", "blocked"]
    root_cause_category: Literal[
        "no_issue_detected",
        "missed_hidden_contract",
        "incomplete_domain_policy",
        "edge_case_gap",
        "wrong_fix_strategy",
        "insufficient_verification",
        "public_failure",
        "evaluator_blocked",
    ]
    root_cause: str = Field(min_length=1)
    missed_contract: str = Field(min_length=1)
    patch_quality: int = Field(ge=1, le=5)
    debug_discipline: int = Field(ge=1, le=5)
    severity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvaluationEvidence] = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    review_limits: str = Field(min_length=1)


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


def load_rows(
    db_path: Path,
    *,
    hidden_only: bool,
    pack: str | None,
    target_model: str | None,
    public_green_only: bool,
) -> list[sqlite3.Row]:
    clauses = []
    params: list[object] = []
    if hidden_only:
        clauses.append("hidden_pass = 0")
    if public_green_only:
        clauses.append("public_pass = 1")
    if pack:
        clauses.append("challenge_pack = ?")
        params.append(pack)
    if target_model:
        clauses.append("model = ?")
        params.append(target_model)
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


def build_budget_note(
    *,
    timeout: int,
    budget_minutes: int | None,
    token_budget: int | None,
    tool_call_budget: int | None,
    shadow_fix_mode: str,
    shadow_fix_budget_minutes: int | None,
    loose: bool,
) -> str:
    lines = [
        "# Evaluator Budget",
        "",
        f"- Hard process timeout: {timeout} seconds.",
        f"- Loose mode: {'on' if loose else 'off'}.",
    ]
    if budget_minutes is not None:
        lines.append(f"- Soft working-time budget: about {budget_minutes} minute(s).")
    if token_budget is not None:
        lines.append(f"- Soft token budget: about {token_budget} output/input reasoning tokens total.")
    if tool_call_budget is not None:
        lines.append(f"- Soft tool-call budget: about {tool_call_budget} tool calls.")
    lines.append(f"- Shadow fix mode: {shadow_fix_mode}.")
    if shadow_fix_budget_minutes is not None:
        lines.append(f"- Shadow fix budget: about {shadow_fix_budget_minutes} minute(s).")
    lines.extend(
        [
            "",
            "Treat these as operating budgets. The CLI enforces only the hard process timeout; "
            "token and tool-call budgets are evaluator instructions because OpenCode does not "
            "expose native token/tool-call limit flags for `opencode run`.",
        ]
    )
    return "\n".join(lines) + "\n"


def copy_repo_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__"),
    )


def apply_patch(repo: Path, patch: str) -> str:
    if not patch.strip():
        return "No patch content was available for this run.\n"
    completed = subprocess.run(
        ["git", "apply", "--whitespace=nowarn"],
        cwd=repo,
        input=patch,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout
    if completed.stderr:
        output += ("\n" if output else "") + completed.stderr
    if completed.returncode == 0:
        return "Patch applied cleanly.\n" + output
    return f"Patch apply failed with exit code {completed.returncode}.\n{output}"


def run_repro_command(repo: Path, *, timeout: int = 60) -> str:
    try:
        completed = subprocess.run(
            TEST_COMMAND,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = completed.stdout
        if completed.stderr:
            output += ("\n" if output else "") + completed.stderr
        return f"$ {' '.join(TEST_COMMAND)}\nexit_code={completed.returncode}\n{output}"
    except subprocess.TimeoutExpired as exc:
        output = ""
        if exc.stdout:
            output += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", "replace")
        if exc.stderr:
            output += ("\n" if output else "")
            output += exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", "replace")
        return f"$ {' '.join(TEST_COMMAND)}\nexit_code=124\n{output}\nCommand timed out after {timeout} seconds."


def working_board_template(row: sqlite3.Row) -> str:
    return dedent(
        f"""
        # Evaluator Working Board

        Challenge: `{row['scenario']}`
        Run ID: `{row['run_id']}`
        Model under test: `{row['model']}`

        ## Reproduction

        - Public/hidden reproduction command:
        - Observed model_repo result:

        ## Contract Hypothesis

        - Missed or satisfied contract:
        - Why this is the right interpretation:

        ## Shadow Fix Lab

        - Attempted in `workbench/shadow_repo`: yes/no
        - What changed, if attempted:
        - Test result, if attempted:

        ## Verdict Notes

        - Final verdict:
        - Patch quality rationale:
        - Debug discipline rationale:
        """
    ).lstrip()


def prepare_workbench(row: sqlite3.Row, review_dir: Path) -> None:
    workbench = review_dir / "workbench"
    if workbench.exists():
        shutil.rmtree(workbench)
    workbench.mkdir(parents=True)

    seed_repo = workbench / "seed_visible_repo"
    model_repo = workbench / "model_repo"
    shadow_repo = workbench / "shadow_repo"
    hidden_dir = workbench / "hidden_acceptance"

    write_scenario(str(row["scenario"]), seed_repo, clean=True)
    copy_repo_tree(seed_repo, model_repo)
    copy_repo_tree(seed_repo, shadow_repo)

    patch = read_text(row["patch_path"], str(row["patch"] or ""))
    write_text(workbench / "model_patch.diff", patch)
    write_text(workbench / "model_patch_apply.txt", apply_patch(model_repo, patch))

    model_summary = ""
    try:
        model_summary = str(row["model_summary"] or "")
    except (KeyError, IndexError):
        pass
    if model_summary.strip():
        write_text(workbench / "model_summary.txt", model_summary + "\n")

    hidden_dir.mkdir(parents=True, exist_ok=True)
    hidden_text = get_scenario(str(row["scenario"])).hidden_test
    write_text(hidden_dir / "test_hidden_acceptance.py", hidden_text)
    write_hidden_test(str(row["scenario"]), model_repo)
    write_hidden_test(str(row["scenario"]), shadow_repo)

    write_text(workbench / "model_repo_test.txt", run_repro_command(model_repo))
    write_text(
        workbench / "README.md",
        dedent(
            f"""
            # Evaluator Agent Workbench

            This directory lets the evaluator act like a coding agent while keeping
            the model-under-test artifact auditable.

            - `seed_visible_repo/`: original visible challenge repo before the model patch.
            - `model_repo/`: original repo plus the model patch plus hidden acceptance tests.
            - `shadow_repo/`: scratch repo plus hidden acceptance tests. The evaluator may edit this
              directory to test a better fix.
            - `hidden_acceptance/test_hidden_acceptance.py`: hidden test source.
            - `model_patch.diff`: exact patch captured from the model-under-test run.
            - `model_summary.txt`: the model's own explanation of what it changed and why (if produced).
            - `model_repo_test.txt`: harness reproduction of public+hidden tests in `model_repo`.

            Test command:

            ```bash
            {' '.join(TEST_COMMAND)}
            ```
            """
        ).strip()
        + "\n",
    )


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

    model_summary_val = ""
    try:
        model_summary_val = str(row["model_summary"] or "")
    except (KeyError, IndexError):
        pass

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

        ## Model's Own Explanation

        {model_summary_val or '(no summary produced)'}

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
        workbench_path = "./workbench"
        budget_path = "./BUDGET.md"
        working_board_path = "./WORKING_BOARD.md"
        json_path = "./evaluation.json"
        markdown_path = "./evaluation.md"
    else:
        resolved = review_dir.resolve()
        packet_path = str(resolved / "EVALUATION_PACKET.md")
        workbench_path = str(resolved / "workbench")
        budget_path = str(resolved / "BUDGET.md")
        working_board_path = str(resolved / "WORKING_BOARD.md")
        json_path = str(resolved / "evaluation.json")
        markdown_path = str(resolved / "evaluation.md")
    return dedent(
        f"""
        You are the evaluator agent for a coding-agent benchmark.

        Non-negotiable constraints:
        - Do not fix the model-under-test artifact.
        - You may edit only `{workbench_path}/shadow_repo` if a scratch shadow fix helps you test your judgment.
        - Read `{budget_path}` before deciding how deep to go.
        - Read `{packet_path}` and files under `{workbench_path}`.
        - Write only `{working_board_path}`, `{json_path}`, `{markdown_path}`, and files under `{workbench_path}/shadow_repo`.
        - Do not search parent directories.
        - Do not use or write any other `runs/...` path.
        - Do not edit EVALUATION_PACKET.md.
        - Do not edit `{workbench_path}/model_repo`; use it only for inspection and test reproduction.
        - Use the workbench before judging: inspect the model patch, run or read the reproduced tests, and optionally test a better fix in `shadow_repo`.
        - Use only evidence present in `{packet_path}` for final JSON evidence quotes.
        - Every evidence.quote must be an exact contiguous substring copied from `{packet_path}`.
        - Keep evidence.quote short: prefer one exact line or one exact bullet.
        - For patch evidence, quote one exact added/removed/context line, not a reconstructed diff hunk.
        - If the model under test passed public tests but failed hidden tests, the verdict must be public_green_hidden_red.
        - If public tests failed, the verdict must be public_red.
        - Do not invent missing tests, hidden intent, source files, or facts.

        Your job is to analyze the run in EVALUATION_PACKET.md and the evaluator workbench.
        First update `{working_board_path}` with your working notes:

        - reproduction result from `workbench/model_repo`
        - contract hypothesis
        - whether you attempted a shadow fix in `workbench/shadow_repo`
        - verdict rationale

        Then write two final files. `evaluation.md` can be natural and practical.
        `evaluation.json` should follow the schema so the harness can summarize the run,
        but your working board is the primary agent trace.

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


def validate_and_normalize_review(
    review: dict[str, object],
    packet: str,
    row: sqlite3.Row,
) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    try:
        parsed = EvaluationReview.model_validate(review)
    except ValidationError as exc:
        return review, [f"pydantic schema error: {error['loc']}: {error['msg']}" for error in exc.errors()]

    normalized: dict[str, object] = parsed.model_dump(mode="json")

    public_pass = int(row["public_pass"])
    hidden_pass = int(row["hidden_pass"])
    verdict = normalized.get("verdict")
    if public_pass and not hidden_pass and verdict != "public_green_hidden_red":
        errors.append("public green + hidden red rows must use verdict public_green_hidden_red")
    if not public_pass and verdict != "public_red":
        errors.append("public red rows must use verdict public_red")
    if public_pass and hidden_pass and verdict not in {"pass", "blocked"}:
        errors.append("public+hidden pass rows should use verdict pass unless evaluator blocked")

    evidence = normalized.get("evidence")
    if not isinstance(evidence, list):
        evidence = []
    hidden_cited = False
    patch_or_contract_cited = False
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        quote = item.get("quote")
        if source == "hidden_test_output":
            hidden_cited = True
        if source in {"patch", "challenge_contract"}:
            patch_or_contract_cited = True
        if isinstance(quote, str) and quote not in packet and source != "evaluator_validation":
            errors.append(f"evidence[{index}].quote is not an exact packet substring")
    if public_pass and not hidden_pass:
        if len(evidence) < 2:
            errors.append("hidden failures require at least two evidence objects")
        if not hidden_cited:
            errors.append("hidden failures require hidden_test_output evidence")
        if not patch_or_contract_cited:
            errors.append("hidden failures require patch or challenge_contract evidence")
    return normalized, errors


def validate_review(review: dict[str, object], packet: str, row: sqlite3.Row) -> list[str]:
    _normalized, errors = validate_and_normalize_review(review, packet, row)
    return errors


def validate_working_board(review_dir: Path) -> list[str]:
    path = review_dir / "WORKING_BOARD.md"
    if not path.exists():
        return ["WORKING_BOARD.md was not created"]
    text = path.read_text(encoding="utf-8", errors="replace")
    required_section_patterns = [
        ("reproduction", r"^##\s+.*reproduction"),
        ("contract hypothesis", r"^##\s+.*(contract|hypothesis)"),
        ("shadow fix lab", r"^##\s+.*shadow"),
        ("verdict notes", r"^##\s+.*(verdict|rationale)"),
    ]
    errors = []
    for label, pattern in required_section_patterns:
        if not re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            errors.append(f"WORKING_BOARD.md missing {label} section")
    return errors


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
    stream: bool,
) -> tuple[int, str, str]:
    command = build_opencode_evaluator_command(
        review_dir=review_dir,
        model=model,
        agent=agent,
        opencode_bin=opencode_bin,
        auto_approve=auto_approve,
    )
    if stream:
        return run_opencode_evaluator_streaming(command, timeout=timeout)
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


def run_opencode_evaluator_streaming(command: list[str], *, timeout: int) -> tuple[int, str, str]:
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    while True:
        if time.monotonic() - started > timeout:
            process.kill()
            selector.close()
            tail_stdout, tail_stderr = process.communicate()
            if tail_stdout:
                print(tail_stdout, end="", flush=True)
                stdout_chunks.append(tail_stdout)
            if tail_stderr:
                print(tail_stderr, end="", file=sys.stderr, flush=True)
                stderr_chunks.append(tail_stderr)
            stderr = "".join(stderr_chunks) + f"\nEvaluator timed out after {timeout} seconds."
            return 124, "".join(stdout_chunks), stderr
        for key, _event in selector.select(timeout=0.2):
            line = key.fileobj.readline()
            if not line:
                selector.unregister(key.fileobj)
                continue
            if key.data == "stdout":
                print(line, end="", flush=True)
                stdout_chunks.append(line)
            else:
                print(line, end="", file=sys.stderr, flush=True)
                stderr_chunks.append(line)
        if process.poll() is not None:
            selector.close()
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                print(remaining_stdout, end="", flush=True)
                stdout_chunks.append(remaining_stdout)
            if remaining_stderr:
                print(remaining_stderr, end="", file=sys.stderr, flush=True)
                stderr_chunks.append(remaining_stderr)
            return process.returncode, "".join(stdout_chunks), "".join(stderr_chunks)


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
    stream: bool,
    loose: bool,
    budget_minutes: int | None,
    token_budget: int | None,
    tool_call_budget: int | None,
    shadow_fix_mode: str,
    shadow_fix_budget_minutes: int | None,
) -> ReviewResult:
    start = time.monotonic()
    review_dir = out_dir / str(row["run_id"])
    review_dir.mkdir(parents=True, exist_ok=True)
    ensure_review_workspace(review_dir)
    packet = make_packet(row)
    write_text(review_dir / "EVALUATION_PACKET.md", packet)
    prepare_workbench(row, review_dir)
    write_text(review_dir / "WORKING_BOARD.md", working_board_template(row))
    write_text(
        review_dir / "BUDGET.md",
        build_budget_note(
            timeout=timeout,
            budget_minutes=budget_minutes,
            token_budget=token_budget,
            tool_call_budget=tool_call_budget,
            shadow_fix_mode=shadow_fix_mode,
            shadow_fix_budget_minutes=shadow_fix_budget_minutes,
            loose=loose,
        ),
    )
    write_text(review_dir / "prompt.txt", evaluator_prompt(review_dir) + "\n")

    agent_exit_code: int | None = None
    stderr = ""
    if model:
        for filename in [
            "evaluation.json",
            "evaluation.md",
            "evaluation.agent.json",
            "validation_errors.json",
            "evaluator_stdout.jsonl",
            "evaluator_stderr.txt",
        ]:
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
            stream=stream,
        )
        write_text(review_dir / "evaluator_stdout.jsonl", stdout)
        write_text(review_dir / "evaluator_stderr.txt", stderr)

    agent_review_path = review_dir / "evaluation.json"
    if model and agent_review_path.exists():
        finalize_agent_review(review_dir, row, packet, loose=loose)
    elif model:
        errors = agent_missing_errors(agent_exit_code=agent_exit_code, stderr=stderr)
        write_text(review_dir / "validation_errors.json", json.dumps(errors, indent=2) + "\n")
        review = deterministic_review(row) if loose else validation_error_review(row, errors)
        if loose:
            review["review_limits"] = (
                "Loose evaluator mode used deterministic summary because the evaluator "
                "did not create schema JSON; inspect WORKING_BOARD.md and evaluator_stdout.jsonl."
            )
        write_text(review_dir / "evaluation.json", json.dumps(review, indent=2, sort_keys=True) + "\n")
        if loose and (review_dir / "evaluation.md").exists():
            pass
        else:
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


def finalize_agent_review(review_dir: Path, row: sqlite3.Row, packet: str, *, loose: bool) -> None:
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
            agent_review, errors = validate_and_normalize_review(agent_review, packet, row)
            errors.extend(validate_working_board(review_dir))

    write_text(review_dir / "evaluation.agent.json", raw_review)
    if errors:
        write_text(review_dir / "validation_errors.json", json.dumps(errors, indent=2) + "\n")
        review = deterministic_review(row) if loose else validation_error_review(row, errors)
        if loose:
            review["review_limits"] = (
                "Loose evaluator mode kept the agent's raw evaluation.agent.json, "
                "WORKING_BOARD.md, and evaluator stream, but used deterministic summary "
                f"because schema validation found: {'; '.join(errors[:4])}"
            )
        write_text(review_dir / "evaluation.json", json.dumps(review, indent=2, sort_keys=True) + "\n")
        if not loose or not (review_dir / "evaluation.md").exists():
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


def extract_packet_field(packet_text: str, label: str, fallback: str = "") -> str:
    match = re.search(rf"-\s*{re.escape(label)}:\s*`([^`]+)`", packet_text)
    return match.group(1) if match else fallback


def infer_evaluator_model(review_root: Path) -> str:
    name = review_root.name
    if "deepseek-v4-pro" in name:
        return "deepseek/deepseek-v4-pro"
    return name


def existing_path(path: Path) -> str:
    return str(path) if path.exists() else ""


def evaluator_review_row(review_dir: Path, *, evaluator_model: str) -> dict[str, object] | None:
    review = load_review(review_dir)
    if not review:
        return None
    try:
        parsed = EvaluationReview.model_validate(review)
    except ValidationError as exc:
        joined = "; ".join(f"{error['loc']}: {error['msg']}" for error in exc.errors())
        raise ValueError(f"{review_dir / 'evaluation.json'} failed evaluator schema validation: {joined}") from exc
    normalized = parsed.model_dump(mode="json")
    packet_path = review_dir / "EVALUATION_PACKET.md"
    packet_text = packet_path.read_text(encoding="utf-8", errors="replace") if packet_path.exists() else ""
    target_run_id = extract_packet_field(packet_text, "Run ID", review_dir.name)
    scenario = extract_scenario_from_packet(packet_text, review_dir.name)
    target_model = extract_packet_field(packet_text, "Model under test", "")
    return {
        "target_run_id": target_run_id,
        "target_model": target_model,
        "scenario": scenario,
        "evaluator_model": evaluator_model,
        "review_dir": str(review_dir),
        "schema_version": normalized["schema_version"],
        "validation_status": normalized["validation_status"],
        "verdict": normalized["verdict"],
        "root_cause_category": normalized["root_cause_category"],
        "root_cause": normalized["root_cause"],
        "missed_contract": normalized["missed_contract"],
        "patch_quality": normalized["patch_quality"],
        "debug_discipline": normalized["debug_discipline"],
        "severity": normalized["severity"],
        "confidence": normalized["confidence"],
        "evidence_json": json.dumps(normalized["evidence"], sort_keys=True),
        "recommendation": normalized["recommendation"],
        "review_limits": normalized["review_limits"],
        "evaluation_json_path": existing_path(review_dir / "evaluation.json"),
        "evaluation_agent_json_path": existing_path(review_dir / "evaluation.agent.json"),
        "evaluation_md_path": existing_path(review_dir / "evaluation.md"),
        "working_board_path": existing_path(review_dir / "WORKING_BOARD.md"),
        "evaluator_stdout_path": existing_path(review_dir / "evaluator_stdout.jsonl"),
        "evaluator_stderr_path": existing_path(review_dir / "evaluator_stderr.txt"),
        "packet_path": existing_path(packet_path),
        "created_at": utc_now(),
    }


def ingest_review_dir(db_path: Path, review_dir: Path, *, evaluator_model: str) -> bool:
    row = evaluator_review_row(review_dir, evaluator_model=evaluator_model)
    if row is None:
        return False
    upsert_evaluator_review(db_path, row)
    return True


def ingest_reviews(db_path: Path, reviews_root: Path, *, evaluator_model: str | None = None) -> int:
    model = evaluator_model or infer_evaluator_model(reviews_root)
    count = 0
    for review_dir in sorted(path for path in reviews_root.iterdir() if path.is_dir()):
        if ingest_review_dir(db_path, review_dir, evaluator_model=model):
            count += 1
    return count


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
    rows = load_rows(
        Path(args.db),
        hidden_only=args.hidden_only,
        pack=args.pack,
        target_model=args.target_model,
        public_green_only=args.public_green_only,
    )
    if not rows:
        print("No rows matched.")
        return
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
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
            stream=args.stream,
            loose=args.loose,
            budget_minutes=args.budget_minutes,
            token_budget=args.token_budget,
            tool_call_budget=args.tool_call_budget,
            shadow_fix_mode=args.shadow_fix_mode,
            shadow_fix_budget_minutes=args.shadow_fix_budget_minutes,
        )
        results.append(result)
        print(f"  wrote {result.review_dir}")
        if args.write_db:
            evaluator_model = args.model or "deterministic"
            if ingest_review_dir(Path(args.db), result.review_dir, evaluator_model=evaluator_model):
                print(f"  indexed review in {Path(args.db)}")
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
    run.add_argument("--target-model", help="Only evaluate rows produced by this model under test.")
    run.add_argument("--hidden-only", action="store_true", help="Only evaluate hidden-test failures.")
    run.add_argument(
        "--public-green-only",
        action="store_true",
        help="Only evaluate runs where public tests passed. Useful for expensive public-green/hidden-red review.",
    )
    run.add_argument("--model", default="opencode-go/glm-5.2", help="OpenCode model for evaluator-agent review. Defaults to opencode-go/glm-5.2 (SOTA).")
    run.add_argument("--agent", help="Optional OpenCode agent name for evaluator-agent review.")
    run.add_argument("--opencode-bin", default="opencode")
    run.add_argument("--timeout", type=int, default=900)
    run.add_argument("--max-rows", type=int, help="Evaluate at most this many matching rows.")
    run.add_argument("--stream", action="store_true", help="Print evaluator-agent stdout/stderr as it runs.")
    run.add_argument("--loose", action="store_true", help="Keep flexible evaluator outputs and fallback summaries instead of hard-blocking on schema issues.")
    run.add_argument("--budget-minutes", type=int, help="Soft evaluator working-time budget written to BUDGET.md.")
    run.add_argument("--token-budget", type=int, help="Soft evaluator token budget written to BUDGET.md.")
    run.add_argument("--tool-call-budget", type=int, help="Soft evaluator tool-call budget written to BUDGET.md.")
    run.add_argument(
        "--shadow-fix-mode",
        choices=["off", "optional", "required"],
        default="optional",
        help="How much the evaluator should use shadow_repo when forming judgment.",
    )
    run.add_argument(
        "--shadow-fix-budget-minutes",
        type=int,
        help="Soft time budget for any shadow fix attempt.",
    )
    run.add_argument("--auto-approve", action="store_true")
    run.add_argument("--report", help="Write a Markdown summary report after reviews.")
    run.add_argument("--write-db", action="store_true", help="Index validated evaluator review artifacts in the SQLite database.")

    report = subparsers.add_parser("report", help="Build summary report from existing evaluator review directory.")
    report.add_argument("--reviews", required=True)
    report.add_argument("--out", required=True)

    ingest = subparsers.add_parser("ingest", help="Index existing evaluator review artifacts in SQLite.")
    ingest.add_argument("--db", default=str(DEFAULT_DB))
    ingest.add_argument("--reviews", required=True)
    ingest.add_argument("--evaluator-model", help="Evaluator model label. Defaults to a best-effort value from the review root name.")

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
    if args.command == "ingest":
        count = ingest_reviews(Path(args.db), Path(args.reviews), evaluator_model=args.evaluator_model)
        print(f"Indexed {count} evaluator review(s) in {Path(args.db).resolve()}")
        return 0
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
