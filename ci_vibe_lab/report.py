from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from textwrap import shorten

from ci_vibe_lab.analysis import (
    TrustMetrics,
    accepted_patch,
    compute_false_green_breakdown,
    compute_trust_metrics,
    compute_value_metrics,
    effective_review_minutes,
    is_headline_accepted_audit_status,
    percent,
    select_best_patches,
)
from ci_vibe_lab.db import connect, load_evaluator_reviews, load_scenario_audits


DEFAULT_DB = Path("data/results.sqlite")
NORTH_MINI_MODEL = "opencode/north-mini-code-free"
DEEPSEEK_CONTROL_MODEL = "deepseek/deepseek-v4-pro"
GLM_PARTIAL_MODEL = "opencode-go/glm-5.2"
DEFAULT_ULTIMATE_NORTH_DBS = [
    Path("data/ci-forensics-v2.sqlite"),
    Path("data/product-workflows-v2.sqlite"),
    Path("data/maintenance-value-v2.sqlite"),
    Path("data/results.sqlite"),
]
DEFAULT_ULTIMATE_DEEPSEEK_DBS = [
    Path("data/ci-forensics-deepseek.sqlite"),
    Path("data/control-results.sqlite"),
    Path("data/maintenance-deepseek.sqlite"),
]
DEFAULT_ULTIMATE_PARTIAL_DBS = [Path("data/ci-forensics-glm52.sqlite")]
STRESS_CONTROL_PACKS = {"ci_forensics", "product_workflows", "maintenance_value"}


def load_rows(db_path: Path) -> list[sqlite3.Row]:
    with connect(db_path) as connection:
        return list(connection.execute("SELECT * FROM runs ORDER BY id"))


def row_dict(row: sqlite3.Row, *, source_db: Path) -> dict[str, object]:
    item = dict(row)
    item["source_db"] = str(source_db)
    return item


def load_rows_from_dbs(db_paths: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for db_path in db_paths:
        rows.extend(row_dict(row, source_db=db_path) for row in load_rows(db_path))
    return rows


def load_audits_from_dbs(db_paths: list[Path]) -> dict[str, dict[str, object]]:
    audits: dict[str, dict[str, object]] = {}
    for db_path in db_paths:
        for row in load_scenario_audits(db_path):
            audits[str(row["scenario"])] = dict(row)
    return audits


def load_reviews_from_dbs(db_paths: list[Path]) -> list[dict[str, object]]:
    reviews: list[dict[str, object]] = []
    for db_path in db_paths:
        for row in load_evaluator_reviews(db_path):
            item = dict(row)
            item["source_db"] = str(db_path)
            reviews.append(item)
    return reviews


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


def sha256_file(path_value: object) -> str:
    if not path_value:
        return ""
    path = Path(str(path_value))
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clip(text: str, *, lines: int = 80, chars: int = 6000) -> str:
    selected = "\n".join(text.splitlines()[:lines])
    if len(selected) > chars:
        return selected[:chars].rstrip() + "\n..."
    return selected


def extract_unittest_failures(output: str) -> list[str]:
    markers = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(("FAIL:", "ERROR:")):
            markers.append(stripped)
    return markers


def outcome(row: sqlite3.Row) -> str:
    if int(row["public_pass"]) and int(row["hidden_pass"]):
        return "pass"
    if int(row["public_pass"]) and not int(row["hidden_pass"]):
        return "public green, hidden red"
    if not int(row["public_pass"]):
        return "public red"
    return "unknown"


def make_hidden_failure_report(rows: list[sqlite3.Row]) -> str:
    total = len(rows)
    public_pass = sum(int(row["public_pass"]) for row in rows)
    hidden_pass = sum(int(row["hidden_pass"]) for row in rows)
    hidden_failures = [row for row in rows if int(row["hidden_pass"]) == 0]
    public_green_hidden_red = [
        row for row in rows if int(row["public_pass"]) == 1 and int(row["hidden_pass"]) == 0
    ]

    model_names = sorted({str(row["model"]) for row in rows})
    packs = sorted({str(row["challenge_pack"]) for row in rows})
    lines = [
        "# Hidden Failure Report",
        "",
        "This report is generated from the SQLite run database. It focuses on the",
        "gap between visible CI success and hidden acceptance failure.",
        "",
        "## Run Summary",
        "",
        f"- Rows: {total}",
        f"- Models: {', '.join(model_names) if model_names else 'n/a'}",
        f"- Challenge packs: {', '.join(packs) if packs else 'n/a'}",
        f"- Public tests passed: {public_pass}/{total}",
        f"- Hidden acceptance passed: {hidden_pass}/{total}",
        f"- Public green but hidden red: {len(public_green_hidden_red)}/{total}",
        "",
        "## Failure Inbox",
        "",
    ]

    if not hidden_failures:
        lines.append("No hidden failures found in this result set.")
        return "\n".join(lines) + "\n"

    lines.append("| Challenge | Category | Outcome | Hidden Failure Markers |")
    lines.append("|---|---|---|---|")
    for row in hidden_failures:
        markers = extract_unittest_failures(str(row["hidden_output"]))
        marker_text = "<br>".join(markers) if markers else "hidden suite failed"
        lines.append(
            f"| `{row['scenario']}` | {row['category']} | {outcome(row)} | {marker_text} |"
        )

    lines.append("")
    lines.append("## Failure Details")
    lines.append("")

    for row in hidden_failures:
        expected = json_list(row["expected_behavior"])
        success = json_list(row["success_signals"])
        failure_modes = json_list(row["failure_modes"])
        patch = read_text(row["patch_path"], str(row["patch"] or ""))
        hidden_output = read_text(row["hidden_output_path"], str(row["hidden_output"] or ""))

        lines.extend(
            [
                f"### `{row['scenario']}` - {row['scenario_title']}",
                "",
                f"- Category: `{row['category']}`",
                f"- Difficulty: `{row['difficulty']}`",
                f"- Model: `{row['model']}`",
                f"- Run ID: `{row['run_id']}`",
                f"- Outcome: **{outcome(row)}**",
                f"- Duration: {float(row['duration_seconds']):.1f}s",
                "",
                "**Trap / hidden contract:**",
                "",
                str(row["trap"] or "No trap documented."),
                "",
                "**Expected behavior:**",
                "",
            ]
        )
        lines.extend([f"- {item}" for item in expected] or ["- n/a"])
        lines.extend(["", "**Success signals:**", ""])
        lines.extend([f"- {item}" for item in success] or ["- n/a"])
        lines.extend(["", "**Known failure modes this challenge is meant to catch:**", ""])
        lines.extend([f"- {item}" for item in failure_modes] or ["- n/a"])
        lines.extend(["", "**Patch produced:**", "", "```diff", clip(patch, lines=120), "```", ""])
        lines.extend(
            [
                "**Hidden test output:**",
                "",
                "```text",
                clip(hidden_output, lines=120),
                "```",
                "",
                "**Short read:**",
                "",
                hidden_short_read(row, patch, hidden_output),
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def hidden_short_read(row: sqlite3.Row, patch: str, hidden_output: str) -> str:
    scenario = str(row["scenario"])
    markers = extract_unittest_failures(hidden_output)
    marker_text = "; ".join(markers)
    if scenario == "csv_header_contract":
        return "The patch found the declared column order but did not handle empty exports or extra internal fields."
    if scenario == "decimal_money_rounding":
        return "The patch moved from float to Decimal, but still truncated cents instead of applying the required rounding policy."
    if scenario == "dependency_api_change":
        return "The patch accepted the new success shape but did not propagate the new charge id field."
    if scenario == "env_bool_parser":
        return "The patch handled several false strings but missed blank/whitespace normalization."
    if marker_text:
        return shorten(marker_text, width=240, placeholder="...")
    if patch.strip():
        return "Hidden acceptance failed; inspect the patch and hidden test output above for the missed contract."
    return "No patch was produced, so hidden acceptance remained red."


def filter_model_rows(rows: list[dict[str, object]], model: str) -> list[dict[str, object]]:
    return [row for row in rows if str(row.get("model", "")) == model]


def accepted_rows(rows: list[dict[str, object]], audits: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if is_headline_accepted_audit_status(
            audits.get(str(row.get("scenario", "")), {}).get("audit_status", "accepted")
        )
    ]


def audit_weights(audits: dict[str, dict[str, object]]) -> dict[str, int]:
    weights = {}
    for scenario, audit in audits.items():
        try:
            weights[scenario] = int(audit.get("impact_weight", 3))
        except (TypeError, ValueError):
            weights[scenario] = 3
    return weights


def claim_row(claim: str, evidence: str, source: str, confidence: str, caveat: str) -> str:
    return (
        f"| {claim.replace('|', '/')} | {evidence.replace('|', '/')} | {source.replace('|', '/')} | "
        f"{confidence.replace('|', '/')} | {caveat.replace('|', '/')} |"
    )


def ultimate_claim_row(claim: str, evidence: str, confidence: str, caveat: str) -> str:
    return (
        f"| {claim.replace('|', '/')} | {evidence.replace('|', '/')} | "
        f"{confidence.replace('|', '/')} | {caveat.replace('|', '/')} |"
    )


def format_count_rate(count: int, denominator: int) -> str:
    return f"{count}/{denominator} ({percent(count / denominator) if denominator else '0.0%'})"


def format_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def metrics_table(metrics: TrustMetrics) -> list[str]:
    return [
        "| Metric | Value |",
        "|---|---:|",
        f"| Runs | {metrics.total} |",
        f"| Public pass | {format_count_rate(metrics.public_pass, metrics.total)} |",
        f"| Hidden pass | {format_count_rate(metrics.hidden_pass, metrics.total)} |",
        f"| Trust gap | {percent(metrics.trust_gap)} |",
        f"| Public-green / hidden-red | {metrics.public_green_hidden_red}/{metrics.total} |",
        f"| False-green rate | {format_count_rate(metrics.public_green_hidden_red, metrics.public_pass)} |",
        f"| Public-red rate | {percent(metrics.public_red_rate)} |",
        f"| Severity-weighted hidden-failure rate | {percent(metrics.severity_weighted_failure_rate or 0.0)} |",
    ]


def group_metrics(rows: list[dict[str, object]], group_key: str, weights: dict[str, int]) -> list[dict[str, object]]:
    groups = sorted({str(row.get(group_key, "")) for row in rows})
    output = []
    for group in groups:
        group_rows = [row for row in rows if str(row.get(group_key, "")) == group]
        metrics = compute_trust_metrics(group_rows, audit_weights=weights)
        output.append(
            {
                group_key: group,
                "runs": metrics.total,
                "public": f"{metrics.public_pass}/{metrics.total}",
                "hidden": f"{metrics.hidden_pass}/{metrics.total}",
                "trust_gap": percent(metrics.trust_gap),
                "false_green": format_count_rate(metrics.public_green_hidden_red, metrics.public_pass),
            }
        )
    return output


def evaluator_taxonomy(reviews: list[dict[str, object]]) -> list[tuple[str, int]]:
    counts = Counter(str(review.get("root_cause_category", "") or "unknown") for review in reviews)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def latest_reviews_by_target_run(reviews: list[dict[str, object]]) -> list[dict[str, object]]:
    latest: dict[str, dict[str, object]] = {}
    for review in sorted(
        reviews,
        key=lambda item: (
            str(item.get("created_at", "")),
            str(item.get("review_dir", "")),
        ),
    ):
        target_run_id = str(review.get("target_run_id", ""))
        if target_run_id:
            latest[target_run_id] = review
    return list(latest.values())


def artifact_line(row: dict[str, object], review_by_run: dict[str, dict[str, object]]) -> str:
    run_id = str(row.get("run_id", ""))
    review = review_by_run.get(run_id, {})
    prompt_path = str(row.get("prompt_path", ""))
    patch_path = str(row.get("patch_path", ""))
    public_path = str(row.get("public_output_path", ""))
    hidden_path = str(row.get("hidden_output_path", ""))
    review_path = str(review.get("evaluation_json_path", ""))
    digest = sha256_file(patch_path)[:12] if patch_path else ""
    return (
        f"| `{run_id}` | `{row.get('scenario', '')}` | `{prompt_path}` | `{patch_path}` | "
        f"`{public_path}` | `{hidden_path}` | `{review_path}` | `{digest}` |"
    )


def value_artifact_line(row: dict[str, object]) -> str:
    patch_path = str(row.get("patch_path", ""))
    digest = sha256_file(patch_path)[:12] if patch_path else ""
    return (
        f"| `{row.get('run_id', '')}` | `{row.get('scenario', '')}` | `{row.get('prompt_path', '')}` | "
        f"`{patch_path}` | `{row.get('public_output_path', '')}` | `{row.get('hidden_output_path', '')}` | `{digest}` |"
    )


def make_value_report(
    *,
    db_paths: list[Path],
    model: str,
    pack: str,
    include_artifact_index: bool,
) -> str:
    all_rows = load_rows_from_dbs(db_paths)
    rows = [
        row
        for row in all_rows
        if str(row.get("model", "")) == model and str(row.get("challenge_pack", "")) == pack
    ]
    metrics = compute_trust_metrics(rows)
    value_metrics = compute_value_metrics(rows)
    selected = {str(row.get("scenario", "")): row for row in select_best_patches(rows)}
    scenarios = sorted({str(row.get("scenario", "")) for row in rows})

    lines = [
        "# Maintenance Value Report",
        "",
        "## Executive Claim",
        "",
        "This report measures whether the model can create useful, reviewable maintenance patches",
        "when the task has an explicit contract, local blast radius, and deterministic acceptance tests.",
        "",
        "The headline value metric is accepted maintenance patches per engineer-review hour.",
        "",
        "## Methodology",
        "",
        f"- Model: `{model}`",
        f"- Pack: `{pack}`",
        "- Intended run design: three attempts per scenario, then select the smallest hidden-passing patch.",
        "- Public tests are visible to the coding agent; hidden acceptance is injected only after the agent exits.",
        "- Review minutes use manual override when present; otherwise they use the deterministic patch-size heuristic.",
        "",
        "## Scorecard",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Attempts | {len(rows)} |",
        f"| Public pass | {format_count_rate(metrics.public_pass, metrics.total)} |",
        f"| Hidden pass | {format_count_rate(metrics.hidden_pass, metrics.total)} |",
        f"| False-green rate | {format_count_rate(metrics.public_green_hidden_red, metrics.public_pass)} |",
        f"| Best-of-3 scenario success | {format_count_rate(value_metrics.best_of_three_successes, value_metrics.best_of_three_scenarios)} |",
        f"| Accepted patches / selected-review hour | {format_number(value_metrics.accepted_patches_per_review_hour)} |",
        f"| Accepted patches / all-attempt review hour | {format_number(value_metrics.accepted_patches_per_attempt_review_hour)} |",
        f"| Selected accepted review minutes | {format_number(value_metrics.total_review_minutes)} |",
        f"| All-attempt review minutes | {format_number(value_metrics.all_attempt_review_minutes)} |",
        f"| Median review minutes | {format_number(value_metrics.median_review_minutes)} |",
        f"| Median changed lines | {format_number(value_metrics.median_changed_lines)} |",
        "",
        "## Scenario Breakdown",
        "",
        "| Scenario | Attempts | Hidden Passes | Best-of-3 | Selected Run | Review Minutes | Changed Lines |",
        "|---|---:|---:|---|---|---:|---:|",
    ]
    for scenario in scenarios:
        scenario_rows = [row for row in rows if str(row.get("scenario", "")) == scenario]
        hidden_passes = sum(int(row.get("hidden_pass", 0)) for row in scenario_rows)
        selected_row = selected.get(scenario)
        lines.append(
            f"| `{scenario}` | {len(scenario_rows)} | {hidden_passes} | "
            f"{'pass' if selected_row else 'fail'} | "
            f"`{selected_row.get('run_id', '') if selected_row else ''}` | "
            f"{format_number(effective_review_minutes(selected_row)) if selected_row else '0'} | "
            f"{selected_row.get('patch_changed_lines', 0) if selected_row else 0} |"
        )

    lines.extend(
        [
            "",
            "## Reviewability Table",
            "",
            "| Run ID | Scenario | Public | Hidden | Accepted | Files | Changed Lines | Review Minutes | Decision |",
            "|---|---|---:|---:|---|---:|---:|---:|---|",
        ]
    )
    for row in sorted(rows, key=lambda item: (str(item.get("scenario", "")), str(item.get("started_at", "")))):
        lines.append(
            f"| `{row.get('run_id', '')}` | `{row.get('scenario', '')}` | {row.get('public_pass', 0)} | "
            f"{row.get('hidden_pass', 0)} | {'yes' if accepted_patch(row) else 'no'} | "
            f"{row.get('patch_files_touched', 0)} | {row.get('patch_changed_lines', 0)} | "
            f"{format_number(effective_review_minutes(row))} | {row.get('review_decision', '') or ''} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Use this report as an operating-mode readout, not a leaderboard. The selected-review",
            "throughput says how cheap the accepted patches are to inspect after best-of-3 selection.",
            "The all-attempt review throughput is the more conservative workflow metric because it",
            "charges review effort for every attempted patch. A weak result means even green-zone",
            "maintenance work needs either better prompts, better acceptance tests, or escalation to",
            "a stronger model.",
            "",
        ]
    )

    if include_artifact_index:
        lines.extend(
            [
                "## Artifact Index",
                "",
                "| Run ID | Scenario | Prompt | Patch | Public Output | Hidden Output | Patch SHA256 Prefix |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for row in rows:
            lines.append(value_artifact_line(row))
        lines.append("")

    return "\n".join(lines) + "\n"


def existing_paths(db_paths: list[Path]) -> list[Path]:
    return [path for path in db_paths if path.exists()]


def model_rows(db_paths: list[Path], model: str) -> list[dict[str, object]]:
    return filter_model_rows(load_rows_from_dbs(existing_paths(db_paths)), model)


def canonical_north_rows(db_paths: list[Path], model: str = NORTH_MINI_MODEL) -> list[dict[str, object]]:
    rows = model_rows(db_paths, model)
    filtered: list[dict[str, object]] = []
    for row in rows:
        pack = str(row.get("challenge_pack", ""))
        if not pack:
            continue
        source_name = Path(str(row.get("source_db", ""))).name
        if source_name == "results.sqlite" and pack != "data_semantics":
            continue
        filtered.append(row)
    return filtered


def pack_rows(rows: list[dict[str, object]], pack: str) -> list[dict[str, object]]:
    return [row for row in rows if str(row.get("challenge_pack", "")) == pack]


def sorted_packs(rows: list[dict[str, object]]) -> list[str]:
    preferred = ["ci_forensics", "data_semantics", "product_workflows", "maintenance_value"]
    present = {str(row.get("challenge_pack", "")) for row in rows if str(row.get("challenge_pack", ""))}
    ordered = [pack for pack in preferred if pack in present]
    ordered.extend(sorted(present - set(ordered)))
    return ordered


def pack_table_lines(rows: list[dict[str, object]], *, value_details: bool = False) -> list[str]:
    lines = [
        "| Pack | Runs | Public Pass | Hidden Pass | Trust Gap | False-Green Rate | Extra Readout |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for pack in sorted_packs(rows):
        current = pack_rows(rows, pack)
        metrics = compute_trust_metrics(current)
        extra = ""
        if value_details and pack == "maintenance_value":
            value_metrics = compute_value_metrics(current)
            extra = (
                f"best-of-3 {value_metrics.best_of_three_successes}/"
                f"{value_metrics.best_of_three_scenarios}; "
                f"{format_number(value_metrics.accepted_patches_per_review_hour)} selected-review accepted/hr; "
                f"{format_number(value_metrics.accepted_patches_per_attempt_review_hour)} all-attempt accepted/hr"
            )
        lines.append(
            f"| `{pack}` | {metrics.total} | {format_count_rate(metrics.public_pass, metrics.total)} | "
            f"{format_count_rate(metrics.hidden_pass, metrics.total)} | {percent(metrics.trust_gap)} | "
            f"{format_count_rate(metrics.public_green_hidden_red, metrics.public_pass)} | {extra} |"
        )
    return lines


def scenario_level_units(
    rows: list[dict[str, object]],
    *,
    packs: set[str] | None = None,
) -> list[dict[str, object]]:
    selected_packs = packs or {str(row.get("challenge_pack", "")) for row in rows}
    units: list[dict[str, object]] = []
    for pack in sorted_packs(rows):
        if pack not in selected_packs:
            continue
        current = pack_rows(rows, pack)
        for scenario in sorted({str(row.get("scenario", "")) for row in current}):
            scenario_rows = [row for row in current if str(row.get("scenario", "")) == scenario]
            if not scenario_rows:
                continue
            units.append(
                {
                    "scenario": scenario,
                    "challenge_pack": pack,
                    "model": scenario_rows[0].get("model", ""),
                    "public_pass": 1 if any(int(row.get("public_pass", 0)) for row in scenario_rows) else 0,
                    "hidden_pass": 1 if any(int(row.get("hidden_pass", 0)) for row in scenario_rows) else 0,
                    "attempts": len(scenario_rows),
                }
            )
    return units


def scenario_level_pack_table(units: list[dict[str, object]]) -> list[str]:
    lines = [
        "| Pack | Scenario Units | Hidden Pass | False-Green | Note |",
        "|---|---:|---:|---:|---|",
    ]
    for pack in sorted_packs(units):
        current = pack_rows(units, pack)
        metrics = compute_trust_metrics(current)
        note = "single run per scenario"
        if pack == "maintenance_value":
            note = "best hidden-passing result across three attempts"
        lines.append(
            f"| `{pack}` | {metrics.total} | {format_count_rate(metrics.hidden_pass, metrics.total)} | "
            f"{format_count_rate(metrics.public_green_hidden_red, metrics.public_pass)} | {note} |"
        )
    return lines


def false_green_scenarios(rows: list[dict[str, object]]) -> list[str]:
    return sorted(
        {
            str(row.get("scenario", ""))
            for row in rows
            if int(row.get("public_pass", 0)) == 1 and int(row.get("hidden_pass", 0)) == 0
        }
    )


def false_green_unit_scenarios(units: list[dict[str, object]], pack: str) -> list[str]:
    return sorted(
        str(unit.get("scenario", ""))
        for unit in units
        if str(unit.get("challenge_pack", "")) == pack
        and int(unit.get("public_pass", 0)) == 1
        and int(unit.get("hidden_pass", 0)) == 0
    )


def markdown_list(items: list[str], *, empty: str = "none") -> list[str]:
    if not items:
        return [f"- {empty}"]
    return [f"- `{item}`" for item in items]


def db_source_lines(db_paths: list[Path]) -> list[str]:
    lines = ["| Source DB | Exists | Runs |", "|---|---:|---:|"]
    for path in db_paths:
        count = len(load_rows(path)) if path.exists() else 0
        lines.append(f"| `{path}` | {'yes' if path.exists() else 'no'} | {count} |")
    return lines


def comparison_delta(north_metrics: TrustMetrics, deepseek_metrics: TrustMetrics) -> str:
    hidden_delta = deepseek_metrics.hidden_pass - north_metrics.hidden_pass
    hidden_rate_delta = deepseek_metrics.hidden_pass_rate - north_metrics.hidden_pass_rate
    false_green_delta = deepseek_metrics.public_green_hidden_red - north_metrics.public_green_hidden_red
    return (
        f"DeepSeek solved {hidden_delta:+d} more scenario units "
        f"({percent(hidden_rate_delta)} hidden-pass-rate delta) and produced "
        f"{false_green_delta:+d} false-green scenario units versus North Mini."
    )


def make_ultimate_report(
    *,
    north_db_paths: list[Path],
    deepseek_db_paths: list[Path],
    partial_db_paths: list[Path],
    out_path: Path | None = None,
) -> str:
    north_rows = canonical_north_rows(north_db_paths)
    deepseek_rows = model_rows(deepseek_db_paths, DEEPSEEK_CONTROL_MODEL)
    glm_rows = model_rows(partial_db_paths, GLM_PARTIAL_MODEL)

    north_metrics = compute_trust_metrics(north_rows)
    deepseek_metrics = compute_trust_metrics(deepseek_rows)
    glm_metrics = compute_trust_metrics(glm_rows)

    north_units = scenario_level_units(north_rows, packs=STRESS_CONTROL_PACKS)
    deepseek_units = scenario_level_units(deepseek_rows, packs=STRESS_CONTROL_PACKS)
    north_unit_metrics = compute_trust_metrics(north_units)
    deepseek_unit_metrics = compute_trust_metrics(deepseek_units)

    north_value = compute_value_metrics(pack_rows(north_rows, "maintenance_value"))
    deepseek_value = compute_value_metrics(pack_rows(deepseek_rows, "maintenance_value"))
    north_product = compute_trust_metrics(pack_rows(north_rows, "product_workflows"))
    deepseek_product = compute_trust_metrics(pack_rows(deepseek_rows, "product_workflows"))
    north_ci = compute_trust_metrics(pack_rows(north_rows, "ci_forensics"))
    deepseek_ci = compute_trust_metrics(pack_rows(deepseek_rows, "ci_forensics"))

    generated_path = f"`{out_path}`" if out_path else "this report"
    lines = [
        "# North Mini Code Ultimate Eval Report",
        "",
        "## Technical Summary",
        "",
        "**Main result:** North Mini Code behaves like a credible small-active coding agent, not like a",
        "semantic acceptance oracle. In this harness it is extremely good at reaching visible public",
        "green states, but hidden acceptance exposes a large trust gap on product and business contracts.",
        "",
        f"- North Mini canonical evidence: {north_metrics.total} attempts across "
        f"{len(sorted_packs(north_rows))} packs; public pass "
        f"{format_count_rate(north_metrics.public_pass, north_metrics.total)}; hidden pass "
        f"{format_count_rate(north_metrics.hidden_pass, north_metrics.total)}; false-green "
        f"{format_count_rate(north_metrics.public_green_hidden_red, north_metrics.public_pass)}.",
        f"- Like-for-like stress control set: North Mini hidden pass "
        f"{format_count_rate(north_unit_metrics.hidden_pass, north_unit_metrics.total)} versus "
        f"DeepSeek hidden pass {format_count_rate(deepseek_unit_metrics.hidden_pass, deepseek_unit_metrics.total)}.",
        f"- Product workflows are the failure microscope: North Mini hidden pass "
        f"{format_count_rate(north_product.hidden_pass, north_product.total)} and false-green "
        f"{format_count_rate(north_product.public_green_hidden_red, north_product.public_pass)}; "
        f"DeepSeek control is only {format_count_rate(deepseek_product.hidden_pass, deepseek_product.total)} hidden-pass.",
        f"- Maintenance work is the positive-value counterexample: North Mini reaches "
        f"{format_count_rate(north_value.best_of_three_successes, north_value.best_of_three_scenarios)} "
        "best-of-3 scenario success. Its accepted patches are slightly cheaper after selection, "
        f"but DeepSeek has stronger whole-workflow maintenance value when every attempted patch is charged "
        f"({format_number(deepseek_value.accepted_patches_per_attempt_review_hour)} versus "
        f"{format_number(north_value.accepted_patches_per_attempt_review_hour)} accepted patches per all-attempt review hour).",
        "",
        "**Defensible interpretation:** the model is useful when a workflow supplies narrow tasks, fast",
        "public feedback, deterministic hidden gates, and human review. It is risky when public green is",
        "treated as acceptance for policy-heavy product logic, money math, authorization, audit, or data",
        "semantic boundaries.",
        "",
        "## What Was Measured",
        "",
        "The harness measures the gap between visible CI repair and hidden contract repair.",
        "",
        "- Public tests are visible to the OpenCode agent during the run.",
        "- Hidden tests are injected after the agent exits.",
        "- A false-green is `public_pass=1` and `hidden_pass=0`.",
        "- Trust gap is public pass rate minus hidden pass rate.",
        "- The maintenance pack reports both attempt-level pass rate and scenario-level best-of-3 success.",
        "- Maintenance value reports selected-review throughput and all-attempt review throughput separately.",
        "- The like-for-like control set uses 33 scenario units: 12 `ci_forensics`, 11 `product_workflows`, and 10 `maintenance_value` units.",
        "- `data_semantics` is included for North Mini's own capability readout, but excluded from the DeepSeek comparison because no matching control run is present.",
        "",
        "This report is generated from local SQLite run databases and should be read as a behavior",
        "microscope, not a public leaderboard benchmark.",
        "",
        "## Official Model-Card Connection",
        "",
        "Cohere's public North Mini Code page, checked on 2026-06-20, identifies `north-mini-code-1-0`",
        "as a 30B total / 3B active Mixture-of-Experts model with a 256K token context window and",
        "64K max output tokens. It describes the model as trained for agentic coding, repo-level",
        "software engineering in harnesses like SWE-Agent and OpenCode, terminal-based agents, local",
        "coding, and code generation.",
        "",
        "That official framing is consistent with what this harness sees: the model can drive the",
        "coding-agent loop. The missing piece is acceptance reliability under sparse semantic contracts.",
        "The Cohere page says it is competitive on software-engineering and terminal-agent benchmarks,",
        "but it does not publish a numeric benchmark table on that page, so this report does not claim",
        "an official Cohere accuracy number.",
        "",
        "Reference links:",
        "",
        "- Cohere North Mini Code docs: https://docs.cohere.com/docs/north-mini-code-1.0",
        "- OpenCode docs: https://opencode.ai/docs/",
        "- SWE-bench leaderboard methodology context: https://www.swebench.com/",
        "- Terminal-Bench methodology context: https://www.tbench.ai/",
        "",
        "## North Mini Scorecard",
        "",
    ]
    lines.extend(pack_table_lines(north_rows, value_details=True))
    lines.extend(
        [
            "",
            "**Readout:** public success is not the problem. North Mini made all 57 canonical public",
            "attempts green. The problem is acceptance reliability after public green: 26 of those 57",
            "public-green attempts were hidden-red.",
            "",
            "## Strong-Model Control Scorecard",
            "",
        ]
    )
    lines.extend(pack_table_lines(deepseek_rows, value_details=True))
    lines.extend(
        [
            "",
            "**Readout:** DeepSeek is better on the like-for-like stress set, but not by enough to",
            "invalidate the harness. It reduces false-greens, but the semantic trap remains visible.",
            "",
            "## Like-For-Like Control Comparison",
            "",
            "This comparison uses scenario units so the maintenance pack's three attempts do not dominate",
            "the denominator. For `maintenance_value`, a scenario is counted as hidden-pass if any of the",
            "three attempts produced an accepted hidden-passing patch.",
            "",
            "| Model | Scenario Units | Public Pass | Hidden Pass | False-Green | Trust Gap |",
            "|---|---:|---:|---:|---:|---:|",
            f"| North Mini Code | {north_unit_metrics.total} | "
            f"{format_count_rate(north_unit_metrics.public_pass, north_unit_metrics.total)} | "
            f"{format_count_rate(north_unit_metrics.hidden_pass, north_unit_metrics.total)} | "
            f"{format_count_rate(north_unit_metrics.public_green_hidden_red, north_unit_metrics.public_pass)} | "
            f"{percent(north_unit_metrics.trust_gap)} |",
            f"| DeepSeek V4 Pro | {deepseek_unit_metrics.total} | "
            f"{format_count_rate(deepseek_unit_metrics.public_pass, deepseek_unit_metrics.total)} | "
            f"{format_count_rate(deepseek_unit_metrics.hidden_pass, deepseek_unit_metrics.total)} | "
            f"{format_count_rate(deepseek_unit_metrics.public_green_hidden_red, deepseek_unit_metrics.public_pass)} | "
            f"{percent(deepseek_unit_metrics.trust_gap)} |",
            "",
            comparison_delta(north_unit_metrics, deepseek_unit_metrics),
            "",
            "### North Mini Scenario-Level Pack Breakdown",
            "",
        ]
    )
    lines.extend(scenario_level_pack_table(north_units))
    lines.extend(["", "### DeepSeek Scenario-Level Pack Breakdown", ""])
    lines.extend(scenario_level_pack_table(deepseek_units))

    lines.extend(
        [
            "",
            "## Why DeepSeek Was Not Dramatically Better",
            "",
            "**The control result is the most important sanity check in the whole report.** If a much larger",
            "control model had crushed these tasks, the report would mostly be about North Mini's model",
            "limit. Instead, DeepSeek improves the result but still fails many public-green cases.",
            "",
            "Facts:",
            "",
            f"- `ci_forensics`: North Mini {format_count_rate(north_ci.hidden_pass, north_ci.total)} hidden-pass; "
            f"DeepSeek {format_count_rate(deepseek_ci.hidden_pass, deepseek_ci.total)}.",
            f"- `product_workflows`: North Mini {format_count_rate(north_product.hidden_pass, north_product.total)} hidden-pass; "
            f"DeepSeek {format_count_rate(deepseek_product.hidden_pass, deepseek_product.total)}.",
            f"- `maintenance_value`: North Mini {format_count_rate(north_value.best_of_three_successes, north_value.best_of_three_scenarios)} "
            f"best-of-3; DeepSeek {format_count_rate(deepseek_value.best_of_three_successes, deepseek_value.best_of_three_scenarios)}.",
            f"- Attempt-level maintenance hidden pass is identical: North Mini "
            f"{format_count_rate(compute_trust_metrics(pack_rows(north_rows, 'maintenance_value')).hidden_pass, len(pack_rows(north_rows, 'maintenance_value')))}; "
            f"DeepSeek {format_count_rate(compute_trust_metrics(pack_rows(deepseek_rows, 'maintenance_value')).hidden_pass, len(pack_rows(deepseek_rows, 'maintenance_value')))}.",
            f"- Selected-review throughput favors North Mini slightly: "
            f"{format_number(north_value.accepted_patches_per_review_hour)} versus "
            f"{format_number(deepseek_value.accepted_patches_per_review_hour)} accepted patches per selected-review hour.",
            f"- All-attempt review throughput favors DeepSeek: "
            f"{format_number(deepseek_value.accepted_patches_per_attempt_review_hour)} versus "
            f"{format_number(north_value.accepted_patches_per_attempt_review_hour)} accepted patches per all-attempt review hour.",
            "",
            "Interpretation:",
            "",
            "- The tasks compress frontier-model advantages. Repos are small, context is short, and the main question is not search depth; it is whether the agent infers the unstated contract behind weak visible tests.",
            "- Visible public tests create an optimization attractor. Both models often stop when public CI is green, even when a stronger semantic reading would imply additional changes.",
            "- Product workflows are policy-dense. They encode business rules like proration, audit redaction, idempotency, raw-body signatures, SLA calendars, and inventory conservation. These are small-code tasks but high-contract tasks.",
            "- Maintenance tasks are explicit and local. That is why North Mini gets close to DeepSeek there: the job is bounded, the contract is clear, and the verifier is deterministic.",
            "- The original selected-review metric was too easy to misread. It measured how cheap accepted patches were to inspect after best-of-3 selection, not total workflow ROI.",
            "",
            "The conclusion is not that DeepSeek is weak. The conclusion is that this harness is probing a",
            "different axis than many leaderboard-style coding evals: not raw repo repair, but whether public",
            "green can be trusted as acceptance when the visible tests under-specify the product contract.",
            "",
            "## Failure X-Ray",
            "",
            "### North Mini False-Green Scenarios By Pack",
            "",
            "**Product workflows are the sharpest warning sign.** Hidden failures there are not syntax",
            "or import problems; they are missed domain rules.",
            "",
            "`ci_forensics`:",
            "",
        ]
    )
    lines.extend(markdown_list(false_green_scenarios(pack_rows(north_rows, "ci_forensics"))))
    lines.extend(["", "`data_semantics`:", ""])
    lines.extend(markdown_list(false_green_scenarios(pack_rows(north_rows, "data_semantics"))))
    lines.extend(["", "`product_workflows`:", ""])
    lines.extend(markdown_list(false_green_scenarios(pack_rows(north_rows, "product_workflows"))))
    lines.extend(["", "`maintenance_value` scenario-level false-greens:", ""])
    lines.extend(markdown_list(false_green_unit_scenarios(north_units, "maintenance_value")))

    lines.extend(
        [
            "",
            "### Failure Categories",
            "",
            "| Category | What It Means | Evidence Pattern |",
            "|---|---|---|",
            "| Assertion completion | The agent fixes the visible assertion and stops. | High public pass with hidden failures after injection. |",
            "| Policy boundary miss | The patch handles the shown case but misses edge policy. | Product workflow false-greens in billing, SLA, discounts, inventory, audit, and webhook cases. |",
            "| Semantic ownership error | The model changes the wrong layer of the system. | Data semantics tasks where raw APIs and user-facing aggregators need different treatment. |",
            "| Local maintenance success | The agent performs bounded, explicit, low-blast-radius work well. | Maintenance best-of-3 success and accepted patches per review hour. |",
            "",
            "## What North Mini Is Capable Of",
            "",
            "**Operational loop competence is high.** It can read a small repository, identify failing tests,",
            "edit code, run the loop, and return a patch. On the canonical North Mini evidence set, every",
            "public test suite passed after the agent run.",
            "",
            "**It is valuable for bounded maintenance.** The maintenance pack is deliberately not a trap",
            "benchmark. It asks for useful chores: generated artifacts, deprecated API migrations, fixture",
            "updates, doc/CLI sync, import hygiene, validation matrices, and pure helper implementation.",
            f"North Mini accepted {north_value.best_of_three_successes} of {north_value.best_of_three_scenarios} "
            "maintenance scenarios after three attempts each. DeepSeek accepted 7 of 10 and should be read",
            "as stronger on whole-workflow maintenance value, despite lower selected-review throughput.",
            "",
            "**It is not safe as an autonomous product-logic merger.** Product workflows are the opposite",
            "shape: sparse visible tests, business policy under-specification, and acceptance conditions that",
            "matter to users. North Mini passed all visible product tests but only 2 of 11 hidden acceptance",
            "suites.",
            "",
            "## What This Eval Does Differently",
            "",
            "Most coding benchmarks ask whether the final submitted patch resolves a task. This harness asks",
            "a narrower operational question: when the model makes CI green, how often is that green state",
            "actually trustworthy?",
            "",
            "| Standard Benchmark Lens | This Harness Lens | Why It Matters |",
            "|---|---|---|",
            "| Pass/fail resolution | Public-green versus hidden-red split | Separates visible repair from acceptance repair. |",
            "| Broad task corpus | Curated semantic stress packs | Makes specific failure modes inspectable. |",
            "| Single score | Trust gap plus false-green rate | Exposes confidently wrong patches. |",
            "| Leaderboard comparison | Behavior microscope with controls | Supports deployment policy, not model marketing. |",
            "| Hidden tests as final grade | Hidden tests as trust audit | Measures whether public CI can be trusted. |",
            "",
            "## Deployment Policy",
            "",
            "| Zone | Recommended Use | Required Gate | Rationale |",
            "|---|---|---|---|",
            "| Green | Mechanical maintenance, generated artifacts, fixture/doc sync, small pure utilities | Public tests, hidden acceptance, patch review | Evidence shows useful positive-value behavior. |",
            "| Amber | Adapter changes, finite validation logic, low-blast-radius product helpers | Hidden tests plus reviewer who understands the contract | The model often gets close, but boundary cases matter. |",
            "| Red | Money movement, auth, audit logging, tenant isolation, inventory, SLA, raw security signatures | Stronger model/control run plus domain review | Product-workflow false-greens are too frequent. |",
            "",
            "## Harness Quality Check",
            "",
            "The current evidence does not support dismissing the harness as simply unfair. Three checks point",
            "the other way:",
            "",
            "1. The maintenance pack is passable and useful, so hidden tests are not universally impossible.",
            "2. The `ci_forensics` pack lands in the middle, so the harness is not only testing product policy.",
            "3. The DeepSeek control improves results but still struggles on product workflows, so the product pack is broadly hard under this setup.",
            "",
            "Still, the harness is not a public benchmark yet. It needs more seeds, more control models,",
            "scenario audits by someone other than the author, and evaluator agreement checks before it can",
            "support broad model-ranking claims.",
            "",
            "## Partial GLM-5.2 Snapshot",
            "",
        ]
    )
    if glm_rows:
        lines.extend(
            [
                f"The GLM-5.2 run is partial: {glm_metrics.total} `ci_forensics` rows only. It is useful as",
                "a smoke signal, not as a comparison baseline.",
                "",
                "| Model | Pack | Runs | Public Pass | Hidden Pass | False-Green |",
                "|---|---|---:|---:|---:|---:|",
                f"| GLM-5.2 | `ci_forensics` | {glm_metrics.total} | "
                f"{format_count_rate(glm_metrics.public_pass, glm_metrics.total)} | "
                f"{format_count_rate(glm_metrics.hidden_pass, glm_metrics.total)} | "
                f"{format_count_rate(glm_metrics.public_green_hidden_red, glm_metrics.public_pass)} |",
                "",
            ]
        )
    else:
        lines.extend(["No GLM-5.2 rows were found in the configured partial-control databases.", ""])

    lines.extend(
        [
            "## Claim Ledger",
            "",
            "| Claim | Evidence | Confidence | Caveat |",
            "|---|---|---|---|",
            ultimate_claim_row(
                "North Mini can execute the OpenCode repair loop",
                f"Public pass {format_count_rate(north_metrics.public_pass, north_metrics.total)}",
                "high",
                "Small curated repos; not a full production workload sample.",
            ),
            ultimate_claim_row(
                "North Mini has a large trust gap after public green",
                f"False-green {format_count_rate(north_metrics.public_green_hidden_red, north_metrics.public_pass)}",
                "high",
                "Hidden tests encode authored contracts; external audit would strengthen legitimacy.",
            ),
            ultimate_claim_row(
                "Product workflows are the main red zone",
                f"North Mini product hidden pass {format_count_rate(north_product.hidden_pass, north_product.total)}",
                "high",
                "The pack is intentionally policy-dense and not a random sample of backend work.",
            ),
            ultimate_claim_row(
                "DeepSeek improves but does not collapse the trust gap",
                f"Like-for-like hidden pass {format_count_rate(deepseek_unit_metrics.hidden_pass, deepseek_unit_metrics.total)} vs North {format_count_rate(north_unit_metrics.hidden_pass, north_unit_metrics.total)}",
                "medium-high",
                "Single control model and mostly single-seed outside maintenance.",
            ),
            ultimate_claim_row(
                "North Mini has positive maintenance value",
                f"Maintenance best-of-3 {format_count_rate(north_value.best_of_three_successes, north_value.best_of_three_scenarios)}, selected-review {format_number(north_value.accepted_patches_per_review_hour)} accepted/hr, all-attempt {format_number(north_value.accepted_patches_per_attempt_review_hour)} accepted/hr",
                "medium-high",
                "Review-hour estimate is heuristic; selected-review throughput is not whole-workflow ROI.",
            ),
            "",
            "## What Can And Cannot Be Defended",
            "",
            "**Can defend from this evidence:**",
            "",
            "- North Mini Code is operationally competent inside the OpenCode loop on these small repos.",
            "- Public pass alone is not a reliable acceptance signal for the semantic/product packs.",
            "- The product-workflow pack reveals a large public-green/hidden-red trust gap.",
            "- Bounded maintenance tasks are a realistic useful operating zone for the model.",
            "- DeepSeek's control run shows these semantic traps are not only a North Mini artifact.",
            "",
            "**Cannot defend yet:**",
            "",
            "- A broad leaderboard ranking of North Mini versus DeepSeek or GLM.",
            "- A statistically stable model accuracy estimate.",
            "- That all product/backend work has this failure rate.",
            "- Official Cohere benchmark accuracy; no numeric official table was present on the checked public page.",
            "",
            "## Reproduce This Report",
            "",
            "Generate the report:",
            "",
            "```bash",
            f"uv run ci-vibe-report ultimate --out {generated_path.strip('`')}",
            "```",
            "",
            "The command uses these default source databases when present.",
            "",
            "### North Mini Sources",
            "",
        ]
    )
    lines.extend(db_source_lines(north_db_paths))
    lines.extend(["", "### DeepSeek Control Sources", ""])
    lines.extend(db_source_lines(deepseek_db_paths))
    lines.extend(["", "### Partial Control Sources", ""])
    lines.extend(db_source_lines(partial_db_paths))
    lines.extend(
        [
            "",
            "## Recommended Next Work",
            "",
            "1. Finish the GLM-5.2 control run or remove it from comparison materials.",
            "2. Run one additional strong model on `product_workflows` to test whether DeepSeek's product failures are model-specific or task-family-specific.",
            "3. Add external scenario audit notes for every hidden test in product workflows and data semantics.",
            "4. Add evaluator-agreement checks: DeepSeek evaluator plus at least one second evaluator model on the false-green set.",
            "5. Only after that, run multi-seed scaling and publish a leaderboard-style summary.",
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def make_xray_report(
    *,
    db_paths: list[Path],
    model: str,
    include_artifact_index: bool,
) -> str:
    all_rows = load_rows_from_dbs(db_paths)
    model_rows = filter_model_rows(all_rows, model)
    audits = load_audits_from_dbs(db_paths)
    weights = audit_weights(audits)
    accepted = accepted_rows(model_rows, audits)
    reviews = [
        review
        for review in load_reviews_from_dbs(db_paths)
        if str(review.get("target_model", "")) == model or not str(review.get("target_model", ""))
    ]
    latest_reviews = latest_reviews_by_target_run(reviews)
    review_by_run = {str(review.get("target_run_id", "")): review for review in latest_reviews}
    metrics = compute_trust_metrics(accepted, audit_weights=weights)
    product_rows = [row for row in accepted if str(row.get("challenge_pack", "")) == "product_workflows"]
    product_metrics = compute_trust_metrics(product_rows, audit_weights=weights)
    control_rows = [
        row
        for row in all_rows
        if str(row.get("model", "")) != model and str(row.get("challenge_pack", "")) == "product_workflows"
    ]
    pghr_rows = [row for row in accepted if int(row.get("public_pass", 0)) == 1 and int(row.get("hidden_pass", 0)) == 0]
    false_green_breakdown = compute_false_green_breakdown(accepted, audits)
    pghr_run_ids = {str(row.get("run_id", "")) for row in pghr_rows}
    diagnostic_reviews = [
        review for review in latest_reviews if str(review.get("target_run_id", "")) in pghr_run_ids
    ]
    audit_status_counts = Counter(str(audits.get(str(row.get("scenario", "")), {}).get("audit_status", "accepted")) for row in model_rows)

    lines = [
        "# North Mini Code Evidence Pack",
        "",
        "## Executive Claim",
        "",
        "North Mini Code is operationally competent but semantically premature: it reliably performs the",
        "OpenCode repository-repair loop, but often stops at public-test success instead of inferring the",
        "full domain or architectural contract.",
        "",
        "This is a behavior microscope, not a public leaderboard benchmark. The defensible claim is about",
        "the trust gap between visible CI success and hidden acceptance on this curated local eval.",
        "",
        "## Model-Card Connection",
        "",
        "Cohere describes North Mini Code as `north-mini-code-1-0`, a 30B total / 3B active MoE model",
        "trained for agentic coding, with a 256K context window and 64K max output tokens. The official",
        "page explicitly names repo-level changes in harnesses like SWE-Agent and OpenCode as intended",
        "uses. The page checked on 2026-06-20 did not provide a numeric benchmark table, so this report",
        "does not claim official accuracy numbers.",
        "",
        "Sources: https://docs.cohere.com/docs/north-mini-code-1.0, https://opencode.ai/docs/,",
        "https://www.swebench.com/, https://www.tbench.ai/",
        "",
        "## Methodology",
        "",
        "- The model saw only visible challenge repos and public tests during the OpenCode call.",
        "- The harness captured prompt, raw OpenCode stream, patch, public output, hidden output, and artifact paths.",
        "- Hidden tests were injected only after the agent exited.",
        "- Evaluator-agent reviews are indexed from validated `evaluation.json` files and preserve raw working boards/streams.",
        "- Headline metrics use only scenarios whose audit status is `accepted`.",
        "",
        "## Scorecard",
        "",
    ]
    lines.extend(metrics_table(metrics))
    lines.extend(
        [
            "",
            "The central diagnostic is the false-green rate: public tests passed but hidden acceptance failed.",
            f"Combined accepted rows: {metrics.public_green_hidden_red}/{metrics.public_pass} public-green runs were hidden-red.",
            f"False-green taxonomy: fair={false_green_breakdown.fair_false_green}, "
            f"weak/spec-exposure={false_green_breakdown.weak_false_green}, "
            f"invalid={false_green_breakdown.invalid_false_green}, "
            f"unclassified={false_green_breakdown.unclassified_false_green}.",
            "",
            "## Product Workflow Stress Read",
            "",
            f"Product workflow false-green rate: {product_metrics.public_green_hidden_red}/{product_metrics.public_pass} "
            f"({percent(product_metrics.false_green_rate)}).",
            "",
            "This pack is the strongest evidence that the weakness is semantic density, not repo scale.",
            "",
        ]
    )
    if control_rows:
        lines.extend(
            [
                "## Strong-Model Control Snapshot",
                "",
                "One product-workflow control run is included as a calibration check, not as a leaderboard result.",
                "It asks whether the pack is broadly hard or uniquely exposing North Mini Code.",
                "",
                "| Control Model | Runs | Public | Hidden | Trust Gap | False Green Rate |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for item in group_metrics(control_rows, "model", weights):
            lines.append(
                f"| `{item['model']}` | {item['runs']} | {item['public']} | {item['hidden']} | "
                f"{item['trust_gap']} | {item['false_green']} |"
            )
        lines.extend(
            [
                "",
                "Interpretation: this control suggests the product-workflow pack is genuinely difficult,",
                "so North Mini's failures should be framed as a trust-gap microscope result first, not as",
                "a complete model-ranking claim.",
                "",
            ]
        )
    lines.extend(
        [
            "## Pack Breakdown",
            "",
            "| Pack | Runs | Public | Hidden | Trust Gap | False Green Rate |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for item in group_metrics(accepted, "challenge_pack", weights):
        lines.append(
            f"| `{item['challenge_pack']}` | {item['runs']} | {item['public']} | {item['hidden']} | "
            f"{item['trust_gap']} | {item['false_green']} |"
        )

    lines.extend(
        [
            "",
            "## Evaluator-Agent Taxonomy",
            "",
            f"Public-green/hidden-red target runs reviewed: {len(diagnostic_reviews)}/{len(pghr_rows)} "
            f"({len(reviews)} review rows indexed).",
            "",
            "| Root Cause Category | Reviews |",
            "|---|---:|",
        ]
    )
    for category, count in evaluator_taxonomy(diagnostic_reviews):
        lines.append(f"| `{category}` | {count} |")
    if not diagnostic_reviews:
        lines.append("| `not_indexed_yet` | 0 |")

    lines.extend(["", "### Evaluator Review Details", ""])
    if diagnostic_reviews:
        lines.extend(
            [
                "| Scenario | Verdict | Severity | Confidence | Patch Quality | Root Cause | Review Artifact |",
                "|---|---|---|---:|---:|---|---|",
            ]
        )
        for review in sorted(diagnostic_reviews, key=lambda item: (str(item.get("scenario", "")), str(item.get("target_run_id", "")))):
            lines.append(
                f"| `{review.get('scenario', '')}` | {review.get('verdict', '')} | {review.get('severity', '')} | "
                f"{review.get('confidence', '')} | {review.get('patch_quality', '')} | "
                f"{str(review.get('root_cause', '')).replace('|', '/')} | `{review.get('evaluation_json_path', '')}` |"
            )
    else:
        lines.append("No evaluator reviews are indexed yet. Run `ci-vibe-evaluate ingest` or evaluator batches with `--write-db`.")

    lines.extend(
        [
            "",
            "## Benchmark Quality Audit",
            "",
            f"Audit status counts: {dict(sorted(audit_status_counts.items()))}",
            "",
            "| Scenario | Status | Risk Area | Impact | Inferability | Hidden Legitimacy | Flexibility | Notes |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for scenario in sorted({str(row.get("scenario", "")) for row in model_rows}):
        audit = audits.get(scenario, {})
        lines.append(
            f"| `{scenario}` | {audit.get('audit_status', 'accepted')} | {audit.get('risk_area', '')} | "
            f"{audit.get('impact_weight', '')} | {audit.get('inferability_score', '')} | "
            f"{audit.get('hidden_legitimacy_score', '')} | {audit.get('implementation_flexibility_score', '')} | "
            f"{str(audit.get('audit_notes', '')).replace('|', '/')} |"
        )

    lines.extend(
        [
            "",
            "## Claim Ledger",
            "",
            "| Claim | Evidence | Source | Confidence | Caveat |",
            "|---|---|---|---|---|",
            claim_row(
                "Operational competence is strong",
                f"Public pass: {format_count_rate(metrics.public_pass, metrics.total)}",
                "SQLite run rows plus public output artifacts",
                "high",
                "Small curated local task set, not a broad benchmark.",
            ),
            claim_row(
                "Semantic trust gap is large",
                f"Trust gap: {percent(metrics.trust_gap)}",
                "Public/hidden pass split after hidden test injection",
                "high",
                "Hidden tests are authored contracts; benchmark audit reduces but does not remove author bias.",
            ),
            claim_row(
                "Product workflows are the sharpest stressor",
                f"Product false-green: {format_count_rate(product_metrics.public_green_hidden_red, product_metrics.public_pass)}",
                "Rows where challenge_pack is product_workflows",
                "high",
                "Add control-model run before claiming difficulty is model-specific.",
            ),
            claim_row(
                "Evaluator-agent diagnostics are accountable",
                f"Public-green/hidden-red target runs reviewed: {len(diagnostic_reviews)}/{len(pghr_rows)}",
                "evaluator_reviews table plus raw review artifacts",
                "medium",
                "Single evaluator model; broader evaluator agreement remains future work.",
            ),
            "",
            "## What Can And Cannot Be Defended",
            "",
            "**Can defend:** North Mini Code is highly effective at visible-feedback CI repair in this harness,",
            "and the public-green/hidden-red split reveals a substantial trust gap on sparse semantic contracts.",
            "",
            "**Cannot yet defend:** broad model leaderboard ranking, statistically stable pass rates, or claims",
            "that these failures generalize to all coding workloads. Multi-seed runs and control models are still required.",
            "",
        ]
    )

    if include_artifact_index:
        lines.extend(
            [
                "## Artifact Index",
                "",
                "| Run ID | Scenario | Prompt | Patch | Public Output | Hidden Output | Evaluator JSON | Patch SHA256 Prefix |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in accepted:
            lines.append(artifact_line(row, review_by_run))
        lines.append("")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Markdown reports from CI Vibe Lab result DBs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    hidden = subparsers.add_parser("hidden-failures", help="Generate a hidden-test failure report.")
    hidden.add_argument("--db", default=str(DEFAULT_DB), help="SQLite result database.")
    hidden.add_argument("--out", required=True, help="Markdown output path.")

    xray = subparsers.add_parser("xray", help="Generate a defensible trust-gap evidence pack report.")
    xray.add_argument("--db", action="append", required=True, help="SQLite result database. Can be provided more than once.")
    xray.add_argument("--model", required=True, help="Model under test to report.")
    xray.add_argument("--out", required=True, help="Markdown output path.")
    xray.add_argument("--include-artifact-index", action="store_true")

    value = subparsers.add_parser("value", help="Generate a positive maintenance-value report.")
    value.add_argument("--db", action="append", required=True, help="SQLite result database. Can be provided more than once.")
    value.add_argument("--model", required=True, help="Model under test to report.")
    value.add_argument("--pack", default="maintenance_value", help="Challenge pack to report.")
    value.add_argument("--out", required=True, help="Markdown output path.")
    value.add_argument("--include-artifact-index", action="store_true")

    ultimate = subparsers.add_parser("ultimate", help="Generate the full-run North Mini evaluation report.")
    ultimate.add_argument("--north-db", action="append", help="North Mini source DB. Defaults to canonical full-run DBs.")
    ultimate.add_argument("--deepseek-db", action="append", help="DeepSeek control DB. Defaults to canonical control DBs.")
    ultimate.add_argument("--partial-db", action="append", help="Partial-control DB, such as GLM smoke runs.")
    ultimate.add_argument("--out", required=True, help="Markdown output path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "hidden-failures":
        db_path = Path(args.db)
        rows = load_rows(db_path)
        report = make_hidden_failure_report(rows)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path.resolve()}")
        return 0
    if args.command == "xray":
        db_paths = [Path(path) for path in args.db]
        report = make_xray_report(
            db_paths=db_paths,
            model=args.model,
            include_artifact_index=args.include_artifact_index,
        )
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path.resolve()}")
        return 0
    if args.command == "value":
        db_paths = [Path(path) for path in args.db]
        report = make_value_report(
            db_paths=db_paths,
            model=args.model,
            pack=args.pack,
            include_artifact_index=args.include_artifact_index,
        )
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path.resolve()}")
        return 0
    if args.command == "ultimate":
        out_path = Path(args.out)
        north_db_paths = [Path(path) for path in args.north_db] if args.north_db else DEFAULT_ULTIMATE_NORTH_DBS
        deepseek_db_paths = (
            [Path(path) for path in args.deepseek_db] if args.deepseek_db else DEFAULT_ULTIMATE_DEEPSEEK_DBS
        )
        partial_db_paths = [Path(path) for path in args.partial_db] if args.partial_db else DEFAULT_ULTIMATE_PARTIAL_DBS
        report = make_ultimate_report(
            north_db_paths=north_db_paths,
            deepseek_db_paths=deepseek_db_paths,
            partial_db_paths=partial_db_paths,
            out_path=out_path,
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote {out_path.resolve()}")
        return 0
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
