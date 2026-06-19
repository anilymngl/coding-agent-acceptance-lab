from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from ci_vibe_lab.analysis import (
    compute_trust_metrics,
    compute_value_metrics,
    effective_review_minutes,
    percent,
    select_best_patches,
)
from ci_vibe_lab.db import connect, load_evaluator_reviews, load_scenario_audits, update_review


DEFAULT_DB = os.environ.get("CI_VIBE_DB", "data/results.sqlite")


def apply_base_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --vibe-bg: #f6f4ef;
            --vibe-panel: #ffffff;
            --vibe-ink: #202124;
            --vibe-muted: #6b6760;
            --vibe-line: #e3ded5;
            --vibe-good: #207a4c;
            --vibe-warn: #a15c12;
            --vibe-bad: #a83a3a;
        }
        .stApp {
            background: var(--vibe-bg);
            color: var(--vibe-ink);
        }
        .vibe-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 10px 0 4px 0;
        }
        .vibe-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid var(--vibe-line);
            background: var(--vibe-panel);
            border-radius: 8px;
            padding: 5px 9px;
            font-size: 0.82rem;
            line-height: 1.2;
        }
        .vibe-chip.good { color: var(--vibe-good); border-color: #b7dbc9; background: #eef8f2; }
        .vibe-chip.warn { color: var(--vibe-warn); border-color: #ead2aa; background: #fbf5e8; }
        .vibe-chip.bad { color: var(--vibe-bad); border-color: #e3b8b8; background: #faeeee; }
        .vibe-chip .label {
            color: var(--vibe-muted);
            text-transform: uppercase;
            font-size: 0.64rem;
            letter-spacing: 0.05em;
        }
        .vibe-chip .value { font-weight: 650; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_db_paths(value: str) -> list[Path]:
    return [Path(item.strip()) for item in value.split(",") if item.strip()]


def load_runs(db_paths: list[Path]) -> pd.DataFrame:
    frames = []
    for db_path in db_paths:
        if not db_path.exists():
            continue
        with connect(db_path) as connection:
            frame = pd.read_sql_query("SELECT * FROM runs ORDER BY started_at DESC", connection)
        frame["source_db"] = str(db_path)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values("started_at", ascending=False)


def load_audits(db_paths: list[Path]) -> pd.DataFrame:
    frames = []
    for db_path in db_paths:
        if not db_path.exists():
            continue
        rows = [dict(row) | {"source_db": str(db_path)} for row in load_scenario_audits(db_path)]
        if rows:
            frames.append(pd.DataFrame(rows))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["scenario"], keep="last")


def load_reviews(db_paths: list[Path]) -> pd.DataFrame:
    frames = []
    for db_path in db_paths:
        if not db_path.exists():
            continue
        rows = [dict(row) | {"source_db": str(db_path)} for row in load_evaluator_reviews(db_path)]
        if rows:
            frames.append(pd.DataFrame(rows))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def parse_json_list(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def read_artifact(path: object, fallback: str) -> str:
    if path is None or pd.isna(path) or not str(path):
        return fallback
    artifact_path = Path(str(path))
    if not artifact_path.exists():
        return fallback
    return artifact_path.read_text(encoding="utf-8")


def bool_label(value: object) -> str:
    return "pass" if int(value) else "fail"


def pass_status(public_pass: object, hidden_pass: object) -> str:
    if int(public_pass) and int(hidden_pass):
        return "pass"
    if int(public_pass) and not int(hidden_pass):
        return "hidden fail"
    return "fail"


def run_label(run_id: str, started_at: object) -> str:
    text = str(started_at or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        label = parsed.strftime("%b %d, %H:%M:%S")
    except ValueError:
        label = text[:19] or run_id[:12]
    return f"{label} - {run_id[:12]}"


def chip(label: str, value: object, tone: str = "") -> str:
    tone_class = f" {tone}" if tone else ""
    safe_label = str(label).replace("<", "&lt;").replace(">", "&gt;")
    safe_value = str(value).replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<span class="vibe-chip{tone_class}">'
        f'<span class="label">{safe_label}</span>'
        f'<span class="value">{safe_value}</span>'
        "</span>"
    )


def render_chip_strip(items: list[tuple[str, object, str]]) -> None:
    html = '<div class="vibe-strip">' + "".join(chip(label, value, tone) for label, value, tone in items) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def latest_by_model_and_scenario(rows: pd.DataFrame, model: str) -> pd.DataFrame:
    model_rows = rows[rows["model"] == model].copy()
    if model_rows.empty:
        return model_rows
    model_rows = model_rows.sort_values("started_at", ascending=False)
    return model_rows.drop_duplicates(subset=["scenario"], keep="first")


def latest_per_model_scenario_frame(rows: pd.DataFrame) -> pd.DataFrame:
    return rows.sort_values("started_at", ascending=False).drop_duplicates(subset=["model", "scenario"], keep="first")


def audit_weight_map(audits: pd.DataFrame) -> dict[str, int]:
    if audits.empty:
        return {}
    weights = {}
    for _, row in audits.iterrows():
        try:
            weights[str(row["scenario"])] = int(row["impact_weight"])
        except (KeyError, TypeError, ValueError):
            weights[str(row.get("scenario", ""))] = 3
    return weights


def model_comparison(rows: pd.DataFrame, model_a: str, model_b: str) -> pd.DataFrame:
    latest_a = latest_by_model_and_scenario(rows, model_a)
    latest_b = latest_by_model_and_scenario(rows, model_b)
    if latest_a.empty or latest_b.empty:
        return pd.DataFrame()
    cols = ["scenario", "scenario_title", "category", "hidden_pass", "public_pass", "duration_seconds", "run_id"]
    merged = latest_a[cols].merge(
        latest_b[cols],
        on=["scenario", "scenario_title", "category"],
        suffixes=("_a", "_b"),
    )
    merged["outcome_a"] = merged.apply(lambda row: pass_status(row["public_pass_a"], row["hidden_pass_a"]), axis=1)
    merged["outcome_b"] = merged.apply(lambda row: pass_status(row["public_pass_b"], row["hidden_pass_b"]), axis=1)
    merged["delta"] = merged["hidden_pass_b"].astype(int) - merged["hidden_pass_a"].astype(int)
    return merged.sort_values(["delta", "scenario"], ascending=[False, True])


def focus_rows(rows: pd.DataFrame) -> pd.DataFrame:
    items = []
    public_fail = rows[rows["public_pass"].astype(int) == 0]
    hidden_fail = rows[(rows["public_pass"].astype(int) == 1) & (rows["hidden_pass"].astype(int) == 0)]
    unreviewed_pass = rows[(rows["hidden_pass"].astype(int) == 1) & rows["patch_quality"].isna()]

    items.append(
        {
            "priority": "P0",
            "focus": "CI still red",
            "count": len(public_fail),
            "why": "The agent did not get the visible test suite green.",
        }
    )
    items.append(
        {
            "priority": "P1",
            "focus": "Hidden acceptance failed",
            "count": len(hidden_fail),
            "why": "The patch looked green publicly but missed the real behavioral contract.",
        }
    )
    items.append(
        {
            "priority": "P2",
            "focus": "Needs human review",
            "count": len(unreviewed_pass),
            "why": "The run passed hidden checks, but patch quality and debug discipline are not scored yet.",
        }
    )
    return pd.DataFrame(items)


def outcome_matrix(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame()
    matrix = rows.copy()
    matrix["outcome"] = matrix.apply(lambda row: pass_status(row["public_pass"], row["hidden_pass"]), axis=1)
    return pd.crosstab(matrix["category"], matrix["outcome"]).reset_index()


def build_run_table(rows: pd.DataFrame) -> pd.DataFrame:
    table_columns = [
        "started_at",
        "run_id",
        "scenario",
        "category",
        "difficulty",
        "model",
        "source_db",
        "opencode_exit_code",
        "baseline_pass",
        "public_pass",
        "hidden_pass",
        "duration_seconds",
        "patch_files_touched",
        "patch_changed_lines",
        "estimated_review_minutes",
        "manual_review_minutes",
        "review_decision",
        "patch_quality",
        "debug_discipline",
    ]
    run_table = rows[table_columns].copy()
    for column in ["baseline_pass", "public_pass", "hidden_pass"]:
        run_table[column] = run_table[column].map(bool_label)
    return run_table


def build_report_markdown(rows: pd.DataFrame, audits: pd.DataFrame | None = None) -> str:
    total = len(rows)
    weights = audit_weight_map(audits) if audits is not None else None
    metrics = compute_trust_metrics(rows.to_dict("records"), audit_weights=weights)
    lines = [
        "# CI Vibe Lab Report",
        "",
        f"- Runs: {total}",
        f"- Models: {rows['model'].nunique() if total else 0}",
        f"- Challenges: {rows['scenario'].nunique() if total else 0}",
        f"- Public pass rate: {percent(metrics.public_pass_rate)}",
        f"- Hidden pass rate: {percent(metrics.hidden_pass_rate)}",
        f"- Trust gap: {percent(metrics.trust_gap)}",
        f"- False-green rate: {percent(metrics.false_green_rate)}",
        "",
        "## What To Focus On",
        "",
    ]
    for row in focus_rows(rows).to_dict("records"):
        lines.append(f"- {row['priority']} {row['focus']}: {row['count']} - {row['why']}")
    lines.extend(["", "## Challenge Outcomes", ""])
    summary = (
        rows.groupby(["scenario", "scenario_title", "category"], as_index=False)
        .agg(runs=("run_id", "count"), public_pass_rate=("public_pass", "mean"), hidden_pass_rate=("hidden_pass", "mean"))
        .sort_values("scenario")
    )
    for row in summary.to_dict("records"):
        lines.append(
            f"- {row['scenario']}: public {row['public_pass_rate'] * 100:.0f}%, "
            f"hidden {row['hidden_pass_rate'] * 100:.0f}% ({row['runs']} runs)"
        )
    return "\n".join(lines) + "\n"


def build_run_markdown(run: pd.Series) -> str:
    expected = "\n".join(f"- {item}" for item in parse_json_list(run["expected_behavior"])) or "- n/a"
    success = "\n".join(f"- {item}" for item in parse_json_list(run["success_signals"])) or "- n/a"
    failure = "\n".join(f"- {item}" for item in parse_json_list(run["failure_modes"])) or "- n/a"
    return "\n".join(
        [
            f"# Run {run['run_id']}",
            "",
            f"- Challenge: {run['scenario_title']} (`{run['scenario']}`)",
            f"- Model: `{run['model']}`",
            f"- Outcome: {pass_status(run['public_pass'], run['hidden_pass'])}",
            f"- Public pass: {bool_label(run['public_pass'])}",
            f"- Hidden pass: {bool_label(run['hidden_pass'])}",
            f"- Duration: {float(run['duration_seconds']):.1f}s",
            f"- Workdir: `{run['workdir']}`",
            "",
            "## Expected Behavior",
            expected,
            "",
            "## Success Signals",
            success,
            "",
            "## Failure Modes",
            failure,
            "",
            "## Notes",
            str(run["notes"] or ""),
            "",
            "## Patch",
            "```diff",
            read_artifact(run["patch_path"], run["patch"] or ""),
            "```",
            "",
        ]
    )


def render_report(rows: pd.DataFrame, audits: pd.DataFrame, reviews: pd.DataFrame, *, show_weighted: bool) -> None:
    total_runs = len(rows)
    weights = audit_weight_map(audits) if show_weighted else None
    metrics = compute_trust_metrics(rows.to_dict("records"), audit_weights=weights)
    avg_duration = rows["duration_seconds"].mean()
    reviewed = rows["patch_quality"].notna().sum()
    hidden_rate = metrics.hidden_pass_rate * 100
    hidden_tone = "good" if hidden_rate >= 80 else "warn" if hidden_rate >= 50 else "bad"
    gap_tone = "bad" if metrics.trust_gap >= 0.25 else "warn" if metrics.trust_gap >= 0.1 else "good"

    cols = st.columns(6)
    cols[0].metric("Runs", total_runs)
    cols[1].metric("Public Pass Rate", percent(metrics.public_pass_rate))
    cols[2].metric("Hidden Pass Rate", percent(metrics.hidden_pass_rate))
    cols[3].metric("Trust Gap", percent(metrics.trust_gap))
    cols[4].metric("False Green Rate", percent(metrics.false_green_rate))
    cols[5].metric("Avg Duration", f"{avg_duration:.1f}s")
    render_chip_strip(
        [
            ("reviewed", f"{reviewed}/{total_runs}", "good" if reviewed == total_runs else "warn"),
            ("models", rows["model"].nunique(), ""),
            ("challenges", rows["scenario"].nunique(), ""),
            (
                "hidden signal",
                "strong" if metrics.hidden_pass_rate >= metrics.public_pass_rate else "catching gaps",
                hidden_tone,
            ),
            ("trust gap", percent(metrics.trust_gap), gap_tone),
        ]
    )
    if show_weighted and metrics.severity_weighted_failure_rate is not None:
        render_chip_strip(
            [("severity weighted hidden failure", percent(metrics.severity_weighted_failure_rate), "bad")]
        )

    product_rows = rows[rows["challenge_pack"] == "product_workflows"]
    if not product_rows.empty:
        product_metrics = compute_trust_metrics(product_rows.to_dict("records"), audit_weights=weights)
        st.subheader("Product Workflow Stress Read")
        render_chip_strip(
            [
                ("product runs", product_metrics.total, ""),
                ("product public", f"{product_metrics.public_pass}/{product_metrics.total}", ""),
                ("product hidden", f"{product_metrics.hidden_pass}/{product_metrics.total}", ""),
                ("product false green", f"{product_metrics.public_green_hidden_red}/{product_metrics.public_pass}", "bad"),
            ]
        )

    st.subheader("What To Focus On")
    focus = focus_rows(rows)
    st.dataframe(focus, use_container_width=True, hide_index=True)

    st.subheader("Result Matrix")
    matrix = outcome_matrix(rows)
    if matrix.empty:
        st.info("No matrix data available.")
    else:
        st.dataframe(matrix, use_container_width=True, hide_index=True)

    by_category = (
        rows.groupby("category", as_index=False)
        .agg(
            runs=("run_id", "count"),
            public_pass_rate=("public_pass", "mean"),
            hidden_pass_rate=("hidden_pass", "mean"),
        )
        .sort_values("category")
    )
    by_category["public_pass_rate"] *= 100
    by_category["hidden_pass_rate"] *= 100
    by_category["trust_gap"] = by_category["public_pass_rate"] - by_category["hidden_pass_rate"]

    st.subheader("Category Readout")
    st.dataframe(by_category, use_container_width=True, hide_index=True)
    st.bar_chart(by_category.set_index("category")[["public_pass_rate", "hidden_pass_rate"]])

    by_scenario = (
        rows.groupby("scenario", as_index=False)
        .agg(
            title=("scenario_title", "first"),
            category=("category", "first"),
            difficulty=("difficulty", "first"),
            runs=("run_id", "count"),
            public_pass_rate=("public_pass", "mean"),
            hidden_pass_rate=("hidden_pass", "mean"),
        )
        .sort_values("scenario")
    )
    by_scenario["public_pass_rate"] *= 100
    by_scenario["hidden_pass_rate"] *= 100
    by_scenario["trust_gap"] = by_scenario["public_pass_rate"] - by_scenario["hidden_pass_rate"]

    st.subheader("Challenge Summary")
    st.dataframe(by_scenario, use_container_width=True, hide_index=True)

    if not reviews.empty:
        st.subheader("Evaluator Review Summary")
        review_counts = reviews.groupby(["verdict", "root_cause_category"], as_index=False).agg(reviews=("id", "count"))
        st.dataframe(review_counts, use_container_width=True, hide_index=True)
    render_value_section(rows)


def render_value_section(rows: pd.DataFrame) -> None:
    value_rows = rows[rows["challenge_pack"] == "maintenance_value"].copy()
    if value_rows.empty:
        return

    records = value_rows.to_dict("records")
    value_metrics = compute_value_metrics(records)
    st.subheader("Maintenance Value Mode")
    cols = st.columns(4)
    cols[0].metric("Accepted / Review Hour", f"{value_metrics.accepted_patches_per_review_hour:.2f}")
    cols[1].metric(
        "Best-of-3 Success",
        f"{value_metrics.best_of_three_successes}/{value_metrics.best_of_three_scenarios}",
    )
    cols[2].metric("Median Review Minutes", f"{value_metrics.median_review_minutes:.1f}")
    cols[3].metric("Median Changed Lines", f"{value_metrics.median_changed_lines:.0f}")

    selected = select_best_patches(records)
    selected_rows = []
    for row in selected:
        selected_rows.append(
            {
                "scenario": row.get("scenario", ""),
                "run_id": row.get("run_id", ""),
                "model": row.get("model", ""),
                "review_minutes": effective_review_minutes(row),
                "files_touched": row.get("patch_files_touched", 0),
                "changed_lines": row.get("patch_changed_lines", 0),
                "started_at": row.get("started_at", ""),
            }
        )
    if selected_rows:
        st.caption("Selected survivor per model+scenario: hidden-passing attempt with the smallest patch.")
        st.dataframe(pd.DataFrame(selected_rows), use_container_width=True, hide_index=True)

    scenario_rows = []
    for scenario, group in value_rows.groupby("scenario"):
        group_records = group.to_dict("records")
        scenario_rows.append(
            {
                "scenario": scenario,
                "attempts": len(group),
                "public_passes": int(group["public_pass"].sum()),
                "hidden_passes": int(group["hidden_pass"].sum()),
                "best_of_3": "pass" if select_best_patches(group_records) else "fail",
            }
        )
    st.dataframe(pd.DataFrame(scenario_rows).sort_values("scenario"), use_container_width=True, hide_index=True)


def render_runs(rows: pd.DataFrame) -> None:
    run_table = build_run_table(rows)
    st.subheader("Runs")
    st.dataframe(
        run_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "duration_seconds": st.column_config.ProgressColumn(
                "duration_seconds",
                min_value=0.0,
                max_value=max(float(run_table["duration_seconds"].max()), 1.0),
                format="%.1fs",
            ),
        },
    )

    failure_inbox = rows[(rows["public_pass"].astype(int) == 0) | (rows["hidden_pass"].astype(int) == 0)].copy()
    st.subheader("Failure Inbox")
    if failure_inbox.empty:
        st.success("No failing runs in the current filter.")
    else:
        failure_inbox["status"] = failure_inbox.apply(
            lambda row: pass_status(row["public_pass"], row["hidden_pass"]),
            axis=1,
        )
        st.dataframe(
            failure_inbox[
                [
                    "status",
                    "scenario",
                    "category",
                    "model",
                    "started_at",
                    "run_id",
                    "workdir",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    model_values = sorted(rows["model"].dropna().unique())
    if len(model_values) >= 2:
        st.subheader("Model Compare")
        compare_cols = st.columns(2)
        model_a = compare_cols[0].selectbox("Model A", model_values, index=0)
        model_b = compare_cols[1].selectbox("Model B", model_values, index=1)
        comparison = model_comparison(rows, model_a, model_b)
        if comparison.empty:
            st.info("No overlapping latest challenge runs for the selected models.")
        else:
            gains = int((comparison["delta"] > 0).sum())
            losses = int((comparison["delta"] < 0).sum())
            ties = int((comparison["delta"] == 0).sum())
            render_chip_strip(
                [
                    ("B gains", gains, "good" if gains else ""),
                    ("B losses", losses, "bad" if losses else ""),
                    ("ties", ties, ""),
                ]
            )
            st.dataframe(
                comparison[
                    [
                        "scenario",
                        "category",
                        "outcome_a",
                        "outcome_b",
                        "duration_seconds_a",
                        "duration_seconds_b",
                        "run_id_a",
                        "run_id_b",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )


def render_challenge_card(run: pd.Series) -> None:
    st.subheader("Challenge Card")
    st.markdown(f"**{run['scenario_title']}**")
    st.write(run["vibe"] or run["scenario"])
    card_cols = st.columns(4)
    card_cols[0].write(f"Pack: `{run['challenge_pack']}`")
    card_cols[1].write(f"Category: `{run['category']}`")
    card_cols[2].write(f"Difficulty: `{run['difficulty']}`")
    card_cols[3].write("Tags: " + ", ".join(f"`{tag}`" for tag in parse_json_list(run["tags"])))

    info_cols = st.columns(3)
    with info_cols[0]:
        st.markdown("**Expected Behavior**")
        for item in parse_json_list(run["expected_behavior"]):
            st.write(f"- {item}")
    with info_cols[1]:
        st.markdown("**Success Signals**")
        for item in parse_json_list(run["success_signals"]):
            st.write(f"- {item}")
    with info_cols[2]:
        st.markdown("**Failure Modes**")
        for item in parse_json_list(run["failure_modes"]):
            st.write(f"- {item}")

    with st.expander("Trap", expanded=False):
        st.write(run["trap"] or "No trap documented.")


def render_inspector(rows: pd.DataFrame, default_db_path: Path) -> None:
    options = rows["run_id"].tolist()
    labels = {
        row["run_id"]: f"{run_label(row['run_id'], row['started_at'])} - {row['scenario']} - {row['model']}"
        for _, row in rows.iterrows()
    }
    selected_run_id = st.selectbox("Inspect run", options, format_func=lambda rid: labels.get(rid, rid))
    run = rows[rows["run_id"] == selected_run_id].iloc[0]

    render_challenge_card(run)

    st.subheader("Run Detail")
    detail_cols = st.columns(4)
    detail_cols[0].write(f"Outcome: `{pass_status(run['public_pass'], run['hidden_pass'])}`")
    detail_cols[1].write(f"Model: `{run['model']}`")
    detail_cols[2].write(f"Workdir: `{run['workdir']}`")
    detail_cols[3].write(f"Artifacts: `{run['artifact_dir']}`")

    st.markdown("**Human Review Rubric:** " + ", ".join(f"`{item}`" for item in parse_json_list(run["rubric"])))
    review_cols = st.columns([1, 1, 3])
    patch_quality = review_cols[0].number_input(
        "Patch quality",
        min_value=1,
        max_value=5,
        value=int(run["patch_quality"]) if pd.notna(run["patch_quality"]) else 3,
    )
    debug_discipline = review_cols[1].number_input(
        "Debug discipline",
        min_value=1,
        max_value=5,
        value=int(run["debug_discipline"]) if pd.notna(run["debug_discipline"]) else 3,
    )
    notes = review_cols[2].text_area("Notes", value=run["notes"] or "", height=96)
    value_cols = st.columns([1, 1, 2])
    current_decision = str(run.get("review_decision") or "")
    decision_options = ["", "accept", "edit", "reject"]
    review_decision = value_cols[0].selectbox(
        "Review decision",
        decision_options,
        index=decision_options.index(current_decision) if current_decision in decision_options else 0,
    )
    current_manual = float(run["manual_review_minutes"]) if "manual_review_minutes" in run and pd.notna(run["manual_review_minutes"]) else 0.0
    manual_review_minutes = value_cols[1].number_input(
        "Manual review minutes",
        min_value=0.0,
        value=current_manual,
        step=0.5,
        help="Use 0 to fall back to the deterministic estimate.",
    )
    value_cols[2].write(
        f"Estimated review: `{float(run.get('estimated_review_minutes') or 0):.1f} min`; "
        f"patch: `{int(run.get('patch_files_touched') or 0)}` files, `{int(run.get('patch_changed_lines') or 0)}` changed lines."
    )
    if st.button("Save review"):
        review_db_path = Path(str(run.get("source_db") or default_db_path))
        update_review(
            review_db_path,
            selected_run_id,
            patch_quality=patch_quality,
            debug_discipline=debug_discipline,
            notes=notes,
            manual_review_minutes=manual_review_minutes if manual_review_minutes > 0 else None,
            review_decision=review_decision,
        )
        st.success("Saved review.")

    st.download_button(
        "Download run report (Markdown)",
        data=build_run_markdown(run),
        file_name=f"{selected_run_id}_report.md",
        mime="text/markdown",
    )

    prompt_tab, tests_tab, trace_tab, patch_tab = st.tabs(["Prompt", "Tests", "OpenCode Trace", "Patch"])
    with prompt_tab:
        st.code(read_artifact(run["prompt_path"], run["prompt"]), language="text")
        try:
            command = json.loads(run["opencode_command"])
        except json.JSONDecodeError:
            command = run["opencode_command"]
        st.caption("OpenCode command")
        st.code(command if isinstance(command, str) else " ".join(command), language="bash")
    with tests_tab:
        output_cols = st.columns(3)
        with output_cols[0]:
            st.caption("Baseline")
            st.code(read_artifact(run["baseline_output_path"], run["baseline_output"]), language="text")
        with output_cols[1]:
            st.caption("Public")
            st.code(read_artifact(run["public_output_path"], run["public_output"]), language="text")
        with output_cols[2]:
            st.caption("Hidden")
            st.code(read_artifact(run["hidden_output_path"], run["hidden_output"]), language="text")
    with trace_tab:
        st.caption("stdout / JSON events")
        st.code(read_artifact(run["opencode_stdout_path"], run["opencode_stdout"]), language="json")
        st.caption("stderr")
        st.code(read_artifact(run["opencode_stderr_path"], run["opencode_stderr"]), language="text")
    with patch_tab:
        st.code(read_artifact(run["patch_path"], run["patch"] or "<empty patch>"), language="diff")


def render_evidence(rows: pd.DataFrame, audits: pd.DataFrame, reviews: pd.DataFrame) -> None:
    st.subheader("Evaluator Reviews")
    if reviews.empty:
        st.info("No evaluator reviews indexed yet. Run `ci-vibe-evaluate ingest` or evaluator batches with `--write-db`.")
    else:
        relevant_models = set(rows["model"].dropna().astype(str))
        relevant_runs = set(rows["run_id"].dropna().astype(str))
        view = reviews[
            reviews["target_model"].astype(str).isin(relevant_models) | reviews["target_run_id"].astype(str).isin(relevant_runs)
        ].copy()
        if view.empty:
            st.info("No evaluator reviews match the current run filters.")
        else:
            st.dataframe(
                view[
                    [
                        "scenario",
                        "target_model",
                        "verdict",
                        "root_cause_category",
                        "severity",
                        "confidence",
                        "patch_quality",
                        "review_dir",
                        "evaluation_json_path",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    st.subheader("Benchmark Quality Audit")
    if audits.empty:
        st.warning("No scenario audit rows found.")
    else:
        scenarios = set(rows["scenario"].dropna().astype(str))
        audit_view = audits[audits["scenario"].astype(str).isin(scenarios)].copy()
        st.dataframe(
            audit_view[
                [
                    "scenario",
                    "audit_status",
                    "risk_area",
                    "impact_weight",
                    "inferability_score",
                    "hidden_legitimacy_score",
                    "implementation_flexibility_score",
                    "audit_notes",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_exports(rows: pd.DataFrame, audits: pd.DataFrame) -> None:
    st.subheader("Exports")
    st.write("Export the filtered result set for deeper review or sharing with another local agent.")
    run_csv = build_run_table(rows).to_csv(index=False)
    raw_csv = rows.to_csv(index=False)
    report_md = build_report_markdown(rows, audits)
    cols = st.columns(3)
    cols[0].download_button("Download run table (CSV)", data=run_csv, file_name="ci_vibe_runs.csv", mime="text/csv")
    cols[1].download_button("Download raw rows (CSV)", data=raw_csv, file_name="ci_vibe_raw_rows.csv", mime="text/csv")
    cols[2].download_button("Download report (Markdown)", data=report_md, file_name="ci_vibe_report.md", mime="text/markdown")


def main() -> None:
    st.set_page_config(page_title="CI Vibe Lab", layout="wide")
    apply_base_styles()
    st.title("CI Vibe Lab")
    st.caption("Local coding-agent challenge runs, patches, traces, and human review in one place.")

    db_input = st.sidebar.text_input("SQLite database(s)", value=str(DEFAULT_DB))
    db_paths = parse_db_paths(db_input)
    runs = load_runs(db_paths)
    audits = load_audits(db_paths)
    reviews = load_reviews(db_paths)

    if runs.empty:
        st.info("No runs found.")
        st.code(
            "uv run python -m ci_vibe_lab.runner run --scenario all "
            "--model provider/model --agent build --auto-approve",
            language="bash",
        )
        return

    pack_options = ["all", *sorted(runs["challenge_pack"].dropna().unique())]
    category_options = ["all", *sorted(runs["category"].dropna().unique())]
    difficulty_options = ["all", *sorted(runs["difficulty"].dropna().unique())]
    scenario_options = ["all", *sorted(runs["scenario"].dropna().unique())]
    model_options = ["all", *sorted(runs["model"].dropna().unique())]
    selected_pack = st.sidebar.selectbox("Challenge pack", pack_options)
    selected_category = st.sidebar.selectbox("Category", category_options)
    selected_difficulty = st.sidebar.selectbox("Difficulty", difficulty_options)
    selected_scenario = st.sidebar.selectbox("Scenario", scenario_options)
    selected_model = st.sidebar.selectbox("Model", model_options)
    latest_only = st.sidebar.checkbox("Latest per model+scenario", value=False)
    accepted_only = st.sidebar.checkbox("Audited accepted scenarios only", value=False)
    public_green_hidden_red_only = st.sidebar.checkbox("Public-green / hidden-red only", value=False)
    show_weighted = st.sidebar.checkbox("Show severity-weighted metric", value=True)

    filtered = runs.copy()
    if selected_pack != "all":
        filtered = filtered[filtered["challenge_pack"] == selected_pack]
    if selected_category != "all":
        filtered = filtered[filtered["category"] == selected_category]
    if selected_difficulty != "all":
        filtered = filtered[filtered["difficulty"] == selected_difficulty]
    if selected_scenario != "all":
        filtered = filtered[filtered["scenario"] == selected_scenario]
    if selected_model != "all":
        filtered = filtered[filtered["model"] == selected_model]
    if accepted_only and not audits.empty:
        accepted_scenarios = set(audits[audits["audit_status"] == "accepted"]["scenario"].astype(str))
        filtered = filtered[filtered["scenario"].astype(str).isin(accepted_scenarios)]
    if public_green_hidden_red_only:
        filtered = filtered[(filtered["public_pass"].astype(int) == 1) & (filtered["hidden_pass"].astype(int) == 0)]
    if latest_only:
        filtered = latest_per_model_scenario_frame(filtered)

    if filtered.empty:
        st.warning("No runs match the selected filters.")
        return

    latest = filtered["started_at"].max()
    hidden_rate = filtered["hidden_pass"].mean() * 100
    tone = "good" if hidden_rate >= 80 else "warn" if hidden_rate >= 50 else "bad"
    render_chip_strip(
        [
            ("dbs", len(db_paths), ""),
            ("db", db_paths[0].name if len(db_paths) == 1 else "multi", ""),
            ("pack", selected_pack, ""),
            ("model", selected_model, ""),
            ("latest", str(latest)[:19], ""),
            ("hidden pass", f"{hidden_rate:.0f}%", tone),
        ]
    )

    report_tab, runs_tab, inspector_tab, evidence_tab, exports_tab = st.tabs(["Report", "Runs", "Inspector", "Evidence", "Exports"])
    with report_tab:
        render_report(filtered, audits, reviews, show_weighted=show_weighted)
    with runs_tab:
        render_runs(filtered)
    with inspector_tab:
        render_inspector(filtered, db_paths[0])
    with evidence_tab:
        render_evidence(filtered, audits, reviews)
    with exports_tab:
        render_exports(filtered, audits)


if __name__ == "__main__":
    main()
