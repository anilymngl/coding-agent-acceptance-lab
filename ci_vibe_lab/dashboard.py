from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from ci_vibe_lab.db import connect, update_review


DEFAULT_DB = Path(os.environ.get("CI_VIBE_DB", "data/results.sqlite"))


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


def load_runs(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        return pd.DataFrame()
    with connect(db_path) as connection:
        return pd.read_sql_query("SELECT * FROM runs ORDER BY started_at DESC", connection)


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
        "opencode_exit_code",
        "baseline_pass",
        "public_pass",
        "hidden_pass",
        "duration_seconds",
        "patch_quality",
        "debug_discipline",
    ]
    run_table = rows[table_columns].copy()
    for column in ["baseline_pass", "public_pass", "hidden_pass"]:
        run_table[column] = run_table[column].map(bool_label)
    return run_table


def build_report_markdown(rows: pd.DataFrame) -> str:
    total = len(rows)
    public_rate = rows["public_pass"].mean() * 100 if total else 0
    hidden_rate = rows["hidden_pass"].mean() * 100 if total else 0
    lines = [
        "# CI Vibe Lab Report",
        "",
        f"- Runs: {total}",
        f"- Models: {rows['model'].nunique() if total else 0}",
        f"- Challenges: {rows['scenario'].nunique() if total else 0}",
        f"- Public pass rate: {public_rate:.1f}%",
        f"- Hidden pass rate: {hidden_rate:.1f}%",
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


def render_report(rows: pd.DataFrame) -> None:
    total_runs = len(rows)
    public_rate = rows["public_pass"].mean() * 100
    hidden_rate = rows["hidden_pass"].mean() * 100
    avg_duration = rows["duration_seconds"].mean()
    reviewed = rows["patch_quality"].notna().sum()
    hidden_tone = "good" if hidden_rate >= 80 else "warn" if hidden_rate >= 50 else "bad"

    cols = st.columns(4)
    cols[0].metric("Runs", total_runs)
    cols[1].metric("Public Pass Rate", f"{public_rate:.0f}%")
    cols[2].metric("Hidden Pass Rate", f"{hidden_rate:.0f}%")
    cols[3].metric("Avg Duration", f"{avg_duration:.1f}s")
    render_chip_strip(
        [
            ("reviewed", f"{reviewed}/{total_runs}", "good" if reviewed == total_runs else "warn"),
            ("models", rows["model"].nunique(), ""),
            ("challenges", rows["scenario"].nunique(), ""),
            ("hidden signal", "strong" if hidden_rate >= public_rate else "catching gaps", hidden_tone),
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

    st.subheader("Challenge Summary")
    st.dataframe(by_scenario, use_container_width=True, hide_index=True)


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


def render_inspector(rows: pd.DataFrame, db_path: Path) -> None:
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
    if st.button("Save review"):
        update_review(
            db_path,
            selected_run_id,
            patch_quality=patch_quality,
            debug_discipline=debug_discipline,
            notes=notes,
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


def render_exports(rows: pd.DataFrame) -> None:
    st.subheader("Exports")
    st.write("Export the filtered result set for deeper review or sharing with another local agent.")
    run_csv = build_run_table(rows).to_csv(index=False)
    raw_csv = rows.to_csv(index=False)
    report_md = build_report_markdown(rows)
    cols = st.columns(3)
    cols[0].download_button("Download run table (CSV)", data=run_csv, file_name="ci_vibe_runs.csv", mime="text/csv")
    cols[1].download_button("Download raw rows (CSV)", data=raw_csv, file_name="ci_vibe_raw_rows.csv", mime="text/csv")
    cols[2].download_button("Download report (Markdown)", data=report_md, file_name="ci_vibe_report.md", mime="text/markdown")


def main() -> None:
    st.set_page_config(page_title="CI Vibe Lab", layout="wide")
    apply_base_styles()
    st.title("CI Vibe Lab")
    st.caption("Local coding-agent challenge runs, patches, traces, and human review in one place.")

    db_input = st.sidebar.text_input("SQLite database", value=str(DEFAULT_DB))
    db_path = Path(db_input)
    runs = load_runs(db_path)

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

    if filtered.empty:
        st.warning("No runs match the selected filters.")
        return

    latest = filtered["started_at"].max()
    hidden_rate = filtered["hidden_pass"].mean() * 100
    tone = "good" if hidden_rate >= 80 else "warn" if hidden_rate >= 50 else "bad"
    render_chip_strip(
        [
            ("db", db_path.name, ""),
            ("pack", selected_pack, ""),
            ("model", selected_model, ""),
            ("latest", str(latest)[:19], ""),
            ("hidden pass", f"{hidden_rate:.0f}%", tone),
        ]
    )

    report_tab, runs_tab, inspector_tab, exports_tab = st.tabs(["Report", "Runs", "Inspector", "Exports"])
    with report_tab:
        render_report(filtered)
    with runs_tab:
        render_runs(filtered)
    with inspector_tab:
        render_inspector(filtered, db_path)
    with exports_tab:
        render_exports(filtered)


if __name__ == "__main__":
    main()
