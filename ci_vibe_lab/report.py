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
    compute_trust_metrics,
    compute_value_metrics,
    effective_review_minutes,
    percent,
    select_best_patches,
)
from ci_vibe_lab.db import connect, load_evaluator_reviews, load_scenario_audits


DEFAULT_DB = Path("data/results.sqlite")


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
        if str(audits.get(str(row.get("scenario", "")), {}).get("audit_status", "accepted")) == "accepted"
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
        f"| Accepted patches / review hour | {format_number(value_metrics.accepted_patches_per_review_hour)} |",
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
            "Use this report as an operating-mode readout, not a leaderboard. A strong result means",
            "the model is useful for cheap bounded attempts protected by deterministic acceptance gates.",
            "A weak result means even green-zone maintenance work needs either better prompts, better",
            "acceptance tests, or escalation to a stronger model.",
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
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
