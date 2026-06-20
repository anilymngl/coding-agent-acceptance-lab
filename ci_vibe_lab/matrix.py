from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from ci_vibe_lab.db import connect
from ci_vibe_lab.scenarios import PROMPT_MODES, pack_ids, scenario_ids


DEFAULT_MATRIX_OUTPUT_ROOT = Path("data/matrix")
DEFAULT_MATRIX_RUNS_ROOT = Path("runs/matrix")
DEFAULT_EVALUATOR_MODEL = "opencode-go/glm-5.2"
SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
PROVIDER_ERROR_MARKERS = (
    "providermodelnotfounderror",
    "model not found",
    "does not support tools",
    "apierror",
    "api error",
    "authentication",
    "authorization",
    "unauthorized",
    "forbidden",
    "invalid api key",
    "connection refused",
    "econnrefused",
    "failed to connect",
    "no such provider",
    "provider",
)

Outcome = Literal[
    "hidden_pass",
    "false_green",
    "public_red",
    "agent_timeout",
    "no_output_timeout",
    "provider_or_config_error",
    "runner_error",
    "missing",
]

EvidenceStatus = Literal["complete", "partial", "runtime_stalled", "missing", "mixed", "legacy"]


def _validate_slug(value: str, field_name: str) -> str:
    if not SLUG_PATTERN.match(value):
        raise ValueError(
            f"{field_name} must be filesystem-safe: letters, numbers, '.', '_' and '-' only"
        )
    return value


class DefaultsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str = "build"
    auto_approve: bool = False
    timeout: int = 900
    first_output_timeout: float | None = None
    delay_seconds: float = 0.0
    runs: int = 1
    prompt_modes: list[str] = Field(default_factory=lambda: ["sparse"])
    packs: list[str] = Field(default_factory=list)
    warmup: bool = True
    warmup_timeout: int = 600
    warmup_keep_alive: str = "30m"

    @field_validator("timeout", "runs", "warmup_timeout")
    @classmethod
    def positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @field_validator("first_output_timeout", "delay_seconds")
    @classmethod
    def non_negative_float(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("must be non-negative")
        return value

    @field_validator("prompt_modes")
    @classmethod
    def valid_prompt_modes(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("prompt_modes must not be empty")
        invalid = sorted(set(values) - set(PROMPT_MODES))
        if invalid:
            raise ValueError(f"unknown prompt mode(s): {', '.join(invalid)}")
        return values

    @field_validator("packs")
    @classmethod
    def valid_default_packs(cls, values: list[str]) -> list[str]:
        invalid = sorted(set(values) - set(pack_ids()))
        if invalid:
            raise ValueError(f"unknown pack(s): {', '.join(invalid)}")
        return values


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alias: str
    id: str
    runtime: str = ""
    enabled: bool = True
    agent: str | None = None
    timeout: int | None = None
    first_output_timeout: float | None = None
    delay_seconds: float | None = None
    auto_approve: bool | None = None
    warmup: bool | None = None
    warmup_timeout: int | None = None
    warmup_keep_alive: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    notes: str = ""

    @field_validator("alias")
    @classmethod
    def valid_alias(cls, value: str) -> str:
        return _validate_slug(value, "model alias")

    @field_validator("timeout", "warmup_timeout")
    @classmethod
    def valid_timeout(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("must be positive")
        return value

    @field_validator("first_output_timeout", "delay_seconds")
    @classmethod
    def valid_float(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("must be non-negative")
        return value


class PackConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runs: int | None = None
    prompt_modes: list[str] | None = None
    challenge: str = "all"

    @field_validator("runs")
    @classmethod
    def valid_runs(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("runs must be positive")
        return value

    @field_validator("prompt_modes")
    @classmethod
    def valid_prompt_modes(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return values
        if not values:
            raise ValueError("prompt_modes must not be empty")
        invalid = sorted(set(values) - set(PROMPT_MODES))
        if invalid:
            raise ValueError(f"unknown prompt mode(s): {', '.join(invalid)}")
        return values


class MatrixConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matrix_id: str
    description: str = ""
    output_root: Path | None = None
    runs_root: Path | None = None
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    models: list[ModelConfig]
    packs: list[str] | dict[str, PackConfig] | None = None

    @field_validator("matrix_id")
    @classmethod
    def valid_matrix_id(cls, value: str) -> str:
        return _validate_slug(value, "matrix_id")

    @field_validator("output_root", "runs_root", mode="before")
    @classmethod
    def empty_path_to_none(cls, value: object) -> object:
        return None if value == "" else value

    @model_validator(mode="after")
    def validate_config(self) -> "MatrixConfig":
        aliases = [model.alias for model in self.models]
        duplicates = sorted(alias for alias in set(aliases) if aliases.count(alias) > 1)
        if duplicates:
            raise ValueError(f"duplicate model alias(es): {', '.join(duplicates)}")
        if not [model for model in self.models if model.enabled]:
            raise ValueError("at least one enabled model is required")
        pack_names = self.pack_names()
        if not pack_names:
            raise ValueError("at least one pack is required")
        invalid = sorted(set(pack_names) - set(pack_ids()))
        if invalid:
            raise ValueError(f"unknown pack(s): {', '.join(invalid)}")
        return self

    def output_root_path(self) -> Path:
        return self.output_root or DEFAULT_MATRIX_OUTPUT_ROOT / self.matrix_id

    def runs_root_path(self) -> Path:
        return self.runs_root or DEFAULT_MATRIX_RUNS_ROOT / self.matrix_id

    def pack_names(self) -> list[str]:
        if isinstance(self.packs, dict):
            return list(self.packs.keys())
        if isinstance(self.packs, list):
            return self.packs
        return self.defaults.packs

    def pack_config(self, pack: str) -> PackConfig:
        if isinstance(self.packs, dict):
            return self.packs.get(pack, PackConfig())
        return PackConfig()


@dataclass(frozen=True)
class MatrixCell:
    matrix_id: str
    model_alias: str
    model_id: str
    pack: str
    prompt_mode: str
    challenge: str
    runs: int
    agent: str
    auto_approve: bool
    timeout: int
    first_output_timeout: float | None
    delay_seconds: float
    db_path: Path
    runs_dir: Path
    experiment_id: str
    environment: dict[str, str]
    warmup: bool
    warmup_timeout: int
    warmup_keep_alive: str
    notes: str = ""


@dataclass(frozen=True)
class CellStatus:
    cell: MatrixCell
    db_exists: bool
    expected_attempts: int
    rows: int
    valid_completed: int
    runtime_failures: int
    missing_coverage: int
    evidence_status: EvidenceStatus
    latest_started_at: str
    latest_ended_at: str
    outcome_counts: Counter[str]


def load_config(path: Path) -> MatrixConfig:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Matrix config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    try:
        return MatrixConfig.model_validate(data)
    except ValidationError as exc:
        raise SystemExit(str(exc)) from exc
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def expand_cells(config: MatrixConfig) -> list[MatrixCell]:
    cells: list[MatrixCell] = []
    db_paths: set[Path] = set()
    for model in config.models:
        if not model.enabled:
            continue
        for pack in config.pack_names():
            pack_config = config.pack_config(pack)
            prompt_modes = pack_config.prompt_modes or config.defaults.prompt_modes
            runs = pack_config.runs or config.defaults.runs
            challenge = pack_config.challenge
            _validate_pack_challenge(pack, challenge)
            for prompt_mode in prompt_modes:
                db_path = config.output_root_path() / model.alias / f"{pack}-{prompt_mode}.sqlite"
                runs_dir = config.runs_root_path() / model.alias / pack / prompt_mode
                if db_path in db_paths:
                    raise SystemExit(f"Two matrix cells derive the same DB path: {db_path}")
                db_paths.add(db_path)
                cells.append(
                    MatrixCell(
                        matrix_id=config.matrix_id,
                        model_alias=model.alias,
                        model_id=model.id,
                        pack=pack,
                        prompt_mode=prompt_mode,
                        challenge=challenge,
                        runs=runs,
                        agent=model.agent or config.defaults.agent,
                        auto_approve=(
                            model.auto_approve
                            if model.auto_approve is not None
                            else config.defaults.auto_approve
                        ),
                        timeout=model.timeout or config.defaults.timeout,
                        first_output_timeout=(
                            model.first_output_timeout
                            if model.first_output_timeout is not None
                            else config.defaults.first_output_timeout
                        ),
                        delay_seconds=(
                            model.delay_seconds
                            if model.delay_seconds is not None
                            else config.defaults.delay_seconds
                        ),
                        db_path=db_path,
                        runs_dir=runs_dir,
                        experiment_id=f"{config.matrix_id}-{model.alias}-{pack}-{prompt_mode}",
                        environment=dict(model.environment),
                        warmup=(
                            model.warmup
                            if model.warmup is not None
                            else config.defaults.warmup
                        ),
                        warmup_timeout=(
                            model.warmup_timeout
                            if model.warmup_timeout is not None
                            else config.defaults.warmup_timeout
                        ),
                        warmup_keep_alive=model.warmup_keep_alive or config.defaults.warmup_keep_alive,
                        notes=model.notes,
                    )
                )
    return cells


def _validate_pack_challenge(pack: str, challenge: str) -> None:
    if pack not in pack_ids():
        raise SystemExit(f"Unknown pack {pack!r}. Valid packs: {', '.join(pack_ids())}")
    if challenge == "all":
        return
    if challenge not in scenario_ids(pack):
        raise SystemExit(f"Challenge {challenge!r} is not in pack {pack!r}.")


def filter_cells(
    cells: list[MatrixCell],
    *,
    only_model: str | None = None,
    only_pack: str | None = None,
    only_prompt_mode: str | None = None,
    max_cells: int | None = None,
) -> list[MatrixCell]:
    selected = cells
    if only_model:
        selected = [cell for cell in selected if cell.model_alias == only_model]
    if only_pack:
        selected = [cell for cell in selected if cell.pack == only_pack]
    if only_prompt_mode:
        selected = [cell for cell in selected if cell.prompt_mode == only_prompt_mode]
    if max_cells is not None:
        if max_cells < 0:
            raise SystemExit("--max-cells must be non-negative")
        selected = selected[:max_cells]
    return selected


def cell_command(
    cell: MatrixCell,
    *,
    resume: bool = False,
    skip_timeouts: bool = False,
) -> list[str]:
    command = [
        "uv",
        "run",
        "ci-vibe-run",
        "run",
        "--challenge",
        cell.challenge,
        "--pack",
        cell.pack,
        "--model",
        cell.model_id,
        "--agent",
        cell.agent,
        "--db",
        str(cell.db_path),
        "--runs-dir",
        str(cell.runs_dir),
        "--timeout",
        str(cell.timeout),
        "--runs",
        str(cell.runs),
        "--delay-seconds",
        str(cell.delay_seconds),
        "--prompt-mode",
        cell.prompt_mode,
        "--experiment-id",
        cell.experiment_id,
    ]
    if cell.first_output_timeout is not None:
        command.extend(["--first-output-timeout", str(cell.first_output_timeout)])
    if cell.auto_approve:
        command.append("--auto-approve")
    if resume:
        command.append("--resume")
    if skip_timeouts:
        command.append("--skip-timeouts")
    return command


def db_paths_for_cells(cells: Iterable[MatrixCell]) -> list[Path]:
    return [cell.db_path for cell in cells]


def ollama_model_name(model_id: str) -> str | None:
    if not model_id.startswith("ollama/"):
        return None
    name = model_id.split("/", 1)[1].strip()
    return name or None


def should_warmup_cell(cell: MatrixCell) -> bool:
    return cell.warmup and ollama_model_name(cell.model_id) is not None


def warmup_ollama_model(
    model_name: str,
    *,
    timeout: int,
    keep_alive: str,
    base_url: str = "http://localhost:11434",
) -> float:
    """Load an Ollama model before the timed OpenCode attempt starts."""
    payload = json.dumps(
        {
            "model": model_name,
            "prompt": "Reply READY only.",
            "stream": False,
            "keep_alive": keep_alive,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama warmup failed for {model_name}: {exc}") from exc
    return time.monotonic() - started


def expected_attempts_for_cell(cell: MatrixCell) -> int:
    scenario_count = len(scenario_ids(cell.pack)) if cell.challenge == "all" else 1
    return scenario_count * cell.runs


def _row_get(row: sqlite3.Row | dict[str, object], key: str, default: object = "") -> object:
    try:
        if isinstance(row, sqlite3.Row):
            return row[key]
        return row.get(key, default)
    except (KeyError, IndexError):
        return default


def _as_int(value: object, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def classify_row(row: sqlite3.Row | dict[str, object] | None) -> Outcome:
    if row is None:
        return "missing"
    exit_code = _row_get(row, "opencode_exit_code", None)
    stdout = str(_row_get(row, "opencode_stdout", "") or "")
    stderr = str(_row_get(row, "opencode_stderr", "") or "")
    patch = str(_row_get(row, "patch", "") or "")
    public_pass = _as_int(_row_get(row, "public_pass", 0))
    hidden_pass = _as_int(_row_get(row, "hidden_pass", 0))
    combined_output = f"{stdout}\n{stderr}".lower()

    if exit_code == 0 or str(exit_code) == "0":
        if not stdout and not patch:
            return "runner_error"
        if public_pass and hidden_pass:
            return "hidden_pass"
        if public_pass and not hidden_pass:
            return "false_green"
        return "public_red"

    if exit_code == 124 or str(exit_code) == "124":
        if not stdout.strip() and "produced no stdout/stderr" in stderr.lower():
            return "no_output_timeout"
        if stdout.strip():
            return "agent_timeout"

    if any(marker in combined_output for marker in PROVIDER_ERROR_MARKERS):
        return "provider_or_config_error"
    return "runner_error"


def is_completed_outcome(outcome: Outcome) -> bool:
    return outcome in {"hidden_pass", "false_green", "public_red"}


def is_runtime_failure_outcome(outcome: Outcome) -> bool:
    return outcome in {
        "agent_timeout",
        "no_output_timeout",
        "provider_or_config_error",
        "runner_error",
    }


def load_cell_rows(cell: MatrixCell) -> list[dict[str, object]]:
    if not cell.db_path.exists():
        return []
    with connect(cell.db_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM runs
            WHERE model = ?
              AND challenge_pack = ?
              AND prompt_mode = ?
              AND experiment_id = ?
            ORDER BY id
            """,
            (cell.model_id, cell.pack, cell.prompt_mode, cell.experiment_id),
        ).fetchall()
    return [dict(row) for row in rows]


def summarize_cell_status(cell: MatrixCell) -> CellStatus:
    rows = load_cell_rows(cell)
    outcomes = Counter(classify_row(row) for row in rows)
    expected = expected_attempts_for_cell(cell)
    valid_completed = sum(count for outcome, count in outcomes.items() if is_completed_outcome(outcome))  # type: ignore[arg-type]
    runtime_failures = sum(count for outcome, count in outcomes.items() if is_runtime_failure_outcome(outcome))  # type: ignore[arg-type]
    missing = max(0, expected - len(rows))
    latest_started_at = str(rows[-1].get("started_at", "")) if rows else ""
    latest_ended_at = str(rows[-1].get("ended_at", "")) if rows else ""
    if not cell.db_path.exists() and not rows:
        evidence_status: EvidenceStatus = "missing"
    elif len(rows) == 0:
        evidence_status = "missing"
    elif valid_completed >= expected and runtime_failures == 0 and missing == 0:
        evidence_status = "complete"
    elif runtime_failures and not valid_completed:
        evidence_status = "runtime_stalled"
    elif runtime_failures and (valid_completed or missing):
        evidence_status = "mixed"
    else:
        evidence_status = "partial"
    return CellStatus(
        cell=cell,
        db_exists=cell.db_path.exists(),
        expected_attempts=expected,
        rows=len(rows),
        valid_completed=valid_completed,
        runtime_failures=runtime_failures,
        missing_coverage=missing,
        evidence_status=evidence_status,
        latest_started_at=latest_started_at,
        latest_ended_at=latest_ended_at,
        outcome_counts=outcomes,
    )


def print_validation(config: MatrixConfig, cells: list[MatrixCell]) -> None:
    print(f"Valid matrix: {config.matrix_id}")
    if config.description:
        print(f"Description: {config.description}")
    print(f"Models: {len([model for model in config.models if model.enabled])}")
    print(f"Packs: {', '.join(config.pack_names())}")
    print(f"Cells: {len(cells)}")
    print(f"Output root: {config.output_root_path()}")
    print(f"Runs root: {config.runs_root_path()}")


def print_plan(cells: list[MatrixCell], *, resume: bool, skip_timeouts: bool) -> None:
    print(f"Cell count: {len(cells)}")
    total_attempts = sum(expected_attempts_for_cell(cell) for cell in cells)
    print(f"Estimated maximum attempts: {total_attempts}")
    for index, cell in enumerate(cells, start=1):
        command = cell_command(cell, resume=resume, skip_timeouts=skip_timeouts)
        print("")
        print(f"[{index}] {cell.model_alias} / {cell.pack} / {cell.prompt_mode}")
        print(f"  db: {cell.db_path}")
        print(f"  runs: {cell.runs_dir}")
        print(f"  experiment: {cell.experiment_id}")
        print(f"  expected attempts: {expected_attempts_for_cell(cell)}")
        if should_warmup_cell(cell):
            print(
                f"  warmup: ollama model {ollama_model_name(cell.model_id)} "
                f"(timeout {cell.warmup_timeout}s, keep_alive {cell.warmup_keep_alive})"
            )
        print(f"  command: {shlex.join(command)}")


def print_status(cells: list[MatrixCell]) -> None:
    print("| Model | Pack | Lane | Expected | Rows | Completed | Runtime Failures | Missing | Status | Latest Ended |")
    print("|---|---|---|---:|---:|---:|---:|---:|---|---|")
    for status in [summarize_cell_status(cell) for cell in cells]:
        cell = status.cell
        print(
            f"| `{cell.model_alias}` | `{cell.pack}` | `{cell.prompt_mode}` | "
            f"{status.expected_attempts} | {status.rows} | {status.valid_completed} | "
            f"{status.runtime_failures} | {status.missing_coverage} | "
            f"`{status.evidence_status}` | {status.latest_ended_at} |"
        )


def run_cells(
    cells: list[MatrixCell],
    *,
    resume: bool,
    skip_timeouts: bool,
    dry_run: bool,
    stop_on_failure: bool,
) -> int:
    if dry_run:
        print_plan(cells, resume=resume, skip_timeouts=skip_timeouts)
        return 0
    exit_code = 0
    for index, cell in enumerate(cells, start=1):
        command = cell_command(cell, resume=resume, skip_timeouts=skip_timeouts)
        cell.runs_dir.mkdir(parents=True, exist_ok=True)
        cell.db_path.parent.mkdir(parents=True, exist_ok=True)
        log_path = cell.runs_dir / "matrix-run.log"
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {shlex.join(command)}\n")
        print(f"[{index}/{len(cells)}] Running {cell.model_alias} / {cell.pack} / {cell.prompt_mode}")
        print(shlex.join(command), flush=True)
        env = None
        if cell.environment:
            env = {**os.environ, **cell.environment}
        if should_warmup_cell(cell):
            model_name = ollama_model_name(cell.model_id)
            assert model_name is not None
            print(f"Prewarming Ollama model {model_name} before timed OpenCode attempt...", flush=True)
            try:
                warmup_seconds = warmup_ollama_model(
                    model_name,
                    timeout=cell.warmup_timeout,
                    keep_alive=cell.warmup_keep_alive,
                )
            except RuntimeError as exc:
                with log_path.open("a", encoding="utf-8") as log:
                    log.write(f"warmup_error={exc}\n")
                print(str(exc), flush=True)
                if stop_on_failure:
                    return 1
                exit_code = 1
                continue
            with log_path.open("a", encoding="utf-8") as log:
                log.write(
                    f"warmup_model={model_name} warmup_seconds={warmup_seconds:.2f} "
                    f"keep_alive={cell.warmup_keep_alive}\n"
                )
            print(f"Warmup complete in {warmup_seconds:.1f}s; starting ci-vibe-run.", flush=True)
        completed = subprocess.run(command, check=False, env=env)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"exit_code={completed.returncode}\n")
        if completed.returncode != 0:
            exit_code = completed.returncode
            print(f"Cell failed with exit code {completed.returncode}: {cell.model_alias}/{cell.pack}/{cell.prompt_mode}")
            if stop_on_failure:
                return exit_code
    return exit_code


@dataclass(frozen=True)
class EvaluateOptions:
    evaluator_model: str
    agent: str | None = None
    opencode_bin: str = "opencode"
    timeout: int = 900
    auto_approve: bool = True
    stream: bool = False
    loose: bool = True
    budget_minutes: int | None = None
    token_budget: int | None = None
    tool_call_budget: int | None = None
    shadow_fix_mode: str = "optional"
    shadow_fix_budget_minutes: int | None = None
    max_rows: int | None = None


def cell_evaluate_command(cell: MatrixCell, out_dir: Path, options: EvaluateOptions) -> list[str]:
    command = [
        "uv",
        "run",
        "ci-vibe-evaluate",
        "run",
        "--db",
        str(cell.db_path),
        "--out",
        str(out_dir),
        "--target-model",
        cell.model_id,
        "--model",
        options.evaluator_model,
        "--timeout",
        str(options.timeout),
        "--hidden-only",
        "--public-green-only",
        "--write-db",
        "--shadow-fix-mode",
        options.shadow_fix_mode,
    ]
    if options.agent:
        command.extend(["--agent", options.agent])
    if options.auto_approve:
        command.append("--auto-approve")
    if options.stream:
        command.append("--stream")
    if options.loose:
        command.append("--loose")
    if options.budget_minutes is not None:
        command.extend(["--budget-minutes", str(options.budget_minutes)])
    if options.token_budget is not None:
        command.extend(["--token-budget", str(options.token_budget)])
    if options.tool_call_budget is not None:
        command.extend(["--tool-call-budget", str(options.tool_call_budget)])
    if options.shadow_fix_budget_minutes is not None:
        command.extend(["--shadow-fix-budget-minutes", str(options.shadow_fix_budget_minutes)])
    if options.max_rows is not None:
        command.extend(["--max-rows", str(options.max_rows)])
    return command


def cell_false_green_count(cell: MatrixCell) -> int:
    rows = load_cell_rows(cell)
    return sum(1 for row in rows if classify_row(row) == "false_green")


def print_evaluate_plan(cells: list[MatrixCell], options: EvaluateOptions) -> None:
    print(f"Evaluator model: {options.evaluator_model}")
    print(f"Cells to evaluate: {len(cells)}")
    total_false_greens = sum(cell_false_green_count(cell) for cell in cells)
    print(f"Total false-green rows to review: {total_false_greens}")
    for index, cell in enumerate(cells, start=1):
        out_dir = cell.runs_dir / "evaluator"
        command = cell_evaluate_command(cell, out_dir, options)
        count = cell_false_green_count(cell)
        print("")
        print(f"[{index}] {cell.model_alias} / {cell.pack} / {cell.prompt_mode}")
        print(f"  db: {cell.db_path}")
        print(f"  out: {out_dir}")
        print(f"  false-greens: {count}")
        print(f"  command: {shlex.join(command)}")


def evaluate_cells(
    cells: list[MatrixCell],
    options: EvaluateOptions,
    *,
    dry_run: bool,
    stop_on_failure: bool,
) -> int:
    if dry_run:
        print_evaluate_plan(cells, options)
        return 0
    exit_code = 0
    for index, cell in enumerate(cells, start=1):
        out_dir = cell.runs_dir / "evaluator"
        command = cell_evaluate_command(cell, out_dir, options)
        out_dir.mkdir(parents=True, exist_ok=True)
        cell.db_path.parent.mkdir(parents=True, exist_ok=True)
        log_path = cell.runs_dir / "matrix-evaluate.log"
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {shlex.join(command)}\n")
        count = cell_false_green_count(cell)
        print(
            f"[{index}/{len(cells)}] Evaluating {cell.model_alias} / {cell.pack} / {cell.prompt_mode} "
            f"({count} false-green rows)"
        )
        print(shlex.join(command), flush=True)
        if count == 0:
            print("  no false-green rows to review; skipping.", flush=True)
            with log_path.open("a", encoding="utf-8") as log:
                log.write("skipped=no_false_greens\n")
            continue
        completed = subprocess.run(command, check=False)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"exit_code={completed.returncode}\n")
        if completed.returncode != 0:
            exit_code = completed.returncode
            print(
                f"Cell evaluation failed with exit code {completed.returncode}: "
                f"{cell.model_alias}/{cell.pack}/{cell.prompt_mode}"
            )
            if stop_on_failure:
                return exit_code
    return exit_code


def common_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--only-model", help="Run or show only one model alias.")
    parser.add_argument("--only-pack", choices=pack_ids(), help="Run or show only one pack.")
    parser.add_argument("--only-prompt-mode", choices=PROMPT_MODES, help="Run or show only one prompt mode.")
    parser.add_argument("--max-cells", type=int, help="Limit the number of selected cells.")


def selected_cells_from_args(args: argparse.Namespace) -> tuple[MatrixConfig, list[MatrixCell]]:
    config = load_config(Path(args.config))
    cells = expand_cells(config)
    return config, filter_cells(
        cells,
        only_model=getattr(args, "only_model", None),
        only_pack=getattr(args, "only_pack", None),
        only_prompt_mode=getattr(args, "only_prompt_mode", None),
        max_cells=getattr(args, "max_cells", None),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan and run CI Vibe Lab model comparison matrices.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a JSON matrix config.")
    validate.add_argument("config")

    plan = subparsers.add_parser("plan", help="Print deterministic matrix cells and ci-vibe-run commands.")
    plan.add_argument("config")
    plan.add_argument("--resume", action="store_true", help="Show commands with --resume.")
    plan.add_argument("--skip-timeouts", action="store_true", help="Show commands with --skip-timeouts.")
    common_filter_args(plan)

    dbs = subparsers.add_parser("dbs", help="Print comma-separated DB paths for dashboard loading.")
    dbs.add_argument("config")
    common_filter_args(dbs)

    status = subparsers.add_parser("status", help="Summarize evidence status for matrix cells.")
    status.add_argument("config")
    common_filter_args(status)

    run = subparsers.add_parser("run", help="Execute selected cells by subprocessing ci-vibe-run.")
    run.add_argument("config")
    run.add_argument("--dry-run", action="store_true", help="Print commands without executing model runs.")
    run.add_argument("--resume", action="store_true", help="Pass --resume to ci-vibe-run for each cell.")
    run.add_argument("--skip-timeouts", action="store_true", help="Pass --skip-timeouts to ci-vibe-run for each cell.")
    run.add_argument("--stop-on-failure", action="store_true", help="Stop after the first failing matrix cell.")
    common_filter_args(run)

    evaluate = subparsers.add_parser(
        "evaluate",
        help="Run evaluator-agent reviews over false-green rows in matrix cell DBs.",
    )
    evaluate.add_argument("config")
    evaluate.add_argument(
        "--model",
        default=DEFAULT_EVALUATOR_MODEL,
        help=f"Evaluator OpenCode model. Defaults to {DEFAULT_EVALUATOR_MODEL} (SOTA).",
    )
    evaluate.add_argument("--agent", help="Optional OpenCode agent name for the evaluator.")
    evaluate.add_argument("--timeout", type=int, default=900, help="Hard process timeout per evaluator cell.")
    evaluate.add_argument("--max-rows", type=int, help="Evaluate at most this many false-green rows per cell.")
    evaluate.add_argument("--dry-run", action="store_true", help="Print evaluator commands without executing.")
    evaluate.add_argument("--stop-on-failure", action="store_true", help="Stop after the first failing evaluator cell.")
    evaluate.add_argument("--stream", action="store_true", help="Stream evaluator stdout/stderr.")
    evaluate.add_argument("--no-loose", action="store_true", help="Disable loose evaluator fallback (hard-block on schema errors).")
    evaluate.add_argument("--no-auto-approve", action="store_true", help="Do not pass --dangerously-skip-permissions.")
    evaluate.add_argument("--budget-minutes", type=int, help="Soft evaluator working-time budget.")
    evaluate.add_argument("--token-budget", type=int, help="Soft evaluator token budget.")
    evaluate.add_argument("--tool-call-budget", type=int, help="Soft evaluator tool-call budget.")
    evaluate.add_argument(
        "--shadow-fix-mode",
        choices=["off", "optional", "required"],
        default="optional",
        help="How much the evaluator should use shadow_repo.",
    )
    evaluate.add_argument("--shadow-fix-budget-minutes", type=int, help="Soft time budget for shadow fix attempts.")
    common_filter_args(evaluate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        config = load_config(Path(args.config))
        cells = expand_cells(config)
        print_validation(config, cells)
        return 0
    if args.command == "plan":
        _config, cells = selected_cells_from_args(args)
        print_plan(cells, resume=args.resume, skip_timeouts=args.skip_timeouts)
        return 0
    if args.command == "dbs":
        _config, cells = selected_cells_from_args(args)
        print(",".join(str(path) for path in db_paths_for_cells(cells)))
        return 0
    if args.command == "status":
        _config, cells = selected_cells_from_args(args)
        print_status(cells)
        return 0
    if args.command == "run":
        _config, cells = selected_cells_from_args(args)
        return run_cells(
            cells,
            resume=args.resume,
            skip_timeouts=args.skip_timeouts,
            dry_run=args.dry_run,
            stop_on_failure=args.stop_on_failure,
        )
    if args.command == "evaluate":
        _config, cells = selected_cells_from_args(args)
        options = EvaluateOptions(
            evaluator_model=args.model,
            agent=args.agent,
            timeout=args.timeout,
            auto_approve=not args.no_auto_approve,
            stream=args.stream,
            loose=not args.no_loose,
            budget_minutes=args.budget_minutes,
            token_budget=args.token_budget,
            tool_call_budget=args.tool_call_budget,
            shadow_fix_mode=args.shadow_fix_mode,
            shadow_fix_budget_minutes=args.shadow_fix_budget_minutes,
            max_rows=args.max_rows,
        )
        return evaluate_cells(cells, options, dry_run=args.dry_run, stop_on_failure=args.stop_on_failure)
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
