from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from textwrap import shorten


DEFAULT_DB = Path("data/results.sqlite")


def load_rows(db_path: Path) -> list[sqlite3.Row]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        return list(connection.execute("SELECT * FROM runs ORDER BY id"))
    finally:
        connection.close()


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Markdown reports from CI Vibe Lab result DBs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    hidden = subparsers.add_parser("hidden-failures", help="Generate a hidden-test failure report.")
    hidden.add_argument("--db", default=str(DEFAULT_DB), help="SQLite result database.")
    hidden.add_argument("--out", required=True, help="Markdown output path.")

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
    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
