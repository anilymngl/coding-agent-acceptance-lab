#!/usr/bin/env python3
"""Verify the public release data against publication metrics."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = REPO_ROOT / "data" / "releases" / "v1"


class MetricParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current: str | None = None
        self.metrics: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if "data-metric" in attrs_dict:
            self.current = attrs_dict["data-metric"]
            self.metrics[self.current] = ""

    def handle_data(self, data: str) -> None:
        if self.current:
            self.metrics[self.current] += data.strip()

    def handle_endtag(self, tag: str) -> None:
        self.current = None


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def con(db_name: str) -> sqlite3.Connection:
    path = RELEASE_DIR / db_name
    if not path.exists():
        fail(f"missing {path}")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def scalar(conn: sqlite3.Connection, sql: str, args: tuple[object, ...] = ()) -> int:
    value = conn.execute(sql, args).fetchone()[0]
    return int(value or 0)


def check_eq(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def pct(num: int, den: int) -> float:
    return round(num / den * 100, 1)


def verify_sqlite_integrity() -> None:
    for db_name in ["study-a.sqlite", "study-b.sqlite", "evaluator-reviews.sqlite", "supporting-gemma.sqlite"]:
        conn = con(db_name)
        try:
            result = conn.execute("pragma integrity_check").fetchone()[0]
            check_eq(f"{db_name} integrity_check", result, "ok")
        finally:
            conn.close()


def sqlite_rows(db_name: str, table: str) -> tuple[list[str], list[list[str]]]:
    conn = con(db_name)
    try:
        cursor = conn.execute(f"select * from {table} order by 1")
        columns = [d[0] for d in cursor.description]
        rows = [[str(row[col]) if row[col] is not None else "" for col in columns] for row in cursor.fetchall()]
        return columns, rows
    finally:
        conn.close()


def csv_rows(relpath: str) -> tuple[list[str], list[list[str]]]:
    path = RELEASE_DIR / relpath
    if not path.exists():
        fail(f"missing CSV {relpath}")
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows:
        fail(f"empty CSV {relpath}")
    return rows[0], rows[1:]


def verify_csv_parity() -> None:
    checks = [
        ("study-b.sqlite", "attempts", "exports/study-b-attempts.csv"),
        ("study-b.sqlite", "cells", "exports/study-b-cells.csv"),
        ("study-b.sqlite", "exclusions", "exports/study-b-exclusions.csv"),
        ("study-b.sqlite", "scenarios", "exports/scenarios.csv"),
        ("study-a.sqlite", "attempts", "exports/study-a-attempts.csv"),
        ("study-a.sqlite", "cells", "exports/study-a-cells.csv"),
        ("evaluator-reviews.sqlite", "evaluator_reviews", "exports/evaluator-reviews.csv"),
        ("supporting-gemma.sqlite", "attempts", "exports/supporting-gemma.csv"),
    ]
    for db_name, table, csv_path in checks:
        db_cols, db_rows = sqlite_rows(db_name, table)
        file_cols, file_rows = csv_rows(csv_path)
        check_eq(f"{csv_path} columns", file_cols, db_cols)
        check_eq(f"{csv_path} rows", file_rows, db_rows)


def release_cell_map() -> dict[tuple[str, str, str, str], dict[str, int | str]]:
    conn = con("study-b.sqlite")
    try:
        rows = conn.execute(
            """
            select c.*, min(a.route) as route
            from cells c
            join attempts a using (scenario_id, system_id, prompt_lane)
            group by c.scenario_id, c.system_id, c.prompt_lane
            order by c.scenario_id, c.pack, c.system_id, c.prompt_lane
            """
        ).fetchall()
    finally:
        conn.close()
    result: dict[tuple[str, str, str, str], dict[str, int | str]] = {}
    for row in rows:
        lane = "cv" if row["prompt_lane"] == "contract_visible" else "sparse"
        gw = "or" if row["route"] == "openrouter" else "zen"
        key = (row["scenario_id"], row["pack"], row["system_id"], lane)
        result[key] = {
            "gw": gw,
            "r": int(row["retained_attempts"]),
            "p": int(row["public_passes"]),
            "h": int(row["hidden_passes"]),
            "fg": int(row["false_greens"]),
        }
    return result


def verify_publication_json_parity() -> None:
    cells = json.loads((REPO_ROOT / "publishables" / "data" / "study-b-cells.json").read_text())
    release = release_cell_map()
    pub = {(c["sc"], c["pack"], c["model"], c["lane"]): c for c in cells}
    check_eq("Study B publication cell key set", sorted(pub), sorted(release))
    for key, row in release.items():
        p = pub[key]
        for field in ["gw", "r", "p", "h", "fg"]:
            check_eq(f"Study B publication parity {key} {field}", p[field], row[field])

    expected_a = json.loads((REPO_ROOT / "publishables" / "data" / "study-a-summary.json").read_text())
    conn = con("study-a.sqlite")
    try:
        actual: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
        rows = conn.execute(
            """
            select pack, prompt_lane, system_id,
                   sum(public_pass) as public,
                   sum(hidden_pass) as hidden,
                   sum(false_green) as false_green
            from attempts
            group by pack, prompt_lane, system_id
            """
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        lane = "cv" if row["prompt_lane"] == "contract_visible" else "sparse"
        actual.setdefault(row["pack"], {}).setdefault(lane, {})[row["system_id"]] = {
            "public": int(row["public"]),
            "hidden": int(row["hidden"]),
            "false_green": int(row["false_green"]),
        }
    check_eq("Study A publication parity", actual, expected_a)


def verify_publication_html_parity(expected: dict[str, int]) -> None:
    parser = MetricParser()
    parser.feed((REPO_ROOT / "publishables" / "paper.html").read_text(encoding="utf-8"))
    metric_expectations = {
        "study_b.planned_attempts": str(expected["planned"]),
        "study_b.retained_attempts": str(expected["retained"]),
        "study_b.cell_count": str(expected["cells"]),
        "study_b.false_greens": str(expected["false_greens"]),
    }
    for metric, value in metric_expectations.items():
        check_eq(f"paper metric {metric}", parser.metrics.get(metric), value)
    paper = (REPO_ROOT / "publishables" / "paper.html").read_text(encoding="utf-8")
    for phrase in ["43.3%", "8.9%", "80.0%", "32.3%", "47.7"]:
        if phrase not in paper:
            fail(f"paper.html missing expected metric phrase {phrase}")


def verify_no_local_paths() -> None:
    bad = []
    for path in RELEASE_DIR.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"/" + b"Users/" in data or b"file:" + b"///" in data:
            bad.append(path.relative_to(RELEASE_DIR).as_posix())
    if bad:
        fail("release files contain local paths: " + ", ".join(bad))


def verify_source_manifest_hashes() -> None:
    manifest = json.loads((REPO_ROOT / "publishables" / "data" / "source-manifest.json").read_text())
    release = manifest.get("public_release")
    if not release:
        fail("source-manifest.json missing public_release")
    check_eq("source manifest release id", release.get("release_id"), "coding-agent-acceptance-lab-v1")
    for item in release.get("files", []):
        relpath = item["path"]
        path = REPO_ROOT / relpath
        if not path.exists():
            fail(f"source manifest points to missing release file {relpath}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        check_eq(f"source manifest hash {relpath}", actual, item["sha256"])


def main() -> None:
    conn = con("study-b.sqlite")
    try:
        scenarios = scalar(conn, "select count(distinct scenario_id) from scenarios")
        cells = scalar(conn, "select count(*) from cells")
        planned = scalar(conn, "select sum(planned_attempts) from cells")
        retained = scalar(conn, "select count(*) from attempts")
        public_green = scalar(conn, "select sum(public_pass) from attempts")
        hidden = scalar(conn, "select sum(hidden_pass) from attempts")
        false_greens = scalar(conn, "select sum(false_green) from attempts")
        missing = scalar(conn, "select count(*) from exclusions")
        sparse_fg = scalar(conn, "select sum(false_green) from attempts where prompt_lane='sparse'")
        sparse_public = scalar(conn, "select sum(public_pass) from attempts where prompt_lane='sparse'")
        cv_fg = scalar(conn, "select sum(false_green) from attempts where prompt_lane='contract_visible'")
        cv_public = scalar(conn, "select sum(public_pass) from attempts where prompt_lane='contract_visible'")
        north_product_sparse_fg = scalar(conn, "select sum(false_green) from attempts where system_id='north-mini' and pack='product_workflows' and prompt_lane='sparse'")
        north_product_sparse_public = scalar(conn, "select sum(public_pass) from attempts where system_id='north-mini' and pack='product_workflows' and prompt_lane='sparse'")
        north_product_cv_fg = scalar(conn, "select sum(false_green) from attempts where system_id='north-mini' and pack='product_workflows' and prompt_lane='contract_visible'")
        north_product_cv_public = scalar(conn, "select sum(public_pass) from attempts where system_id='north-mini' and pack='product_workflows' and prompt_lane='contract_visible'")
    finally:
        conn.close()

    expected = {
        "scenarios": 33,
        "cells": 132,
        "planned": 396,
        "retained": 391,
        "public_green": 385,
        "hidden": 284,
        "false_greens": 101,
        "missing": 5,
    }
    check_eq("Study B scenarios", scenarios, expected["scenarios"])
    check_eq("Study B cells", cells, expected["cells"])
    check_eq("Planned attempts", planned, expected["planned"])
    check_eq("Retained attempts", retained, expected["retained"])
    check_eq("Public-green attempts", public_green, expected["public_green"])
    check_eq("Hidden passes", hidden, expected["hidden"])
    check_eq("False-greens", false_greens, expected["false_greens"])
    check_eq("Missing attempts", missing, expected["missing"])
    check_eq("Sparse false-green numerator", sparse_fg, 84)
    check_eq("Sparse false-green denominator", sparse_public, 194)
    check_eq("Contract-visible false-green numerator", cv_fg, 17)
    check_eq("Contract-visible false-green denominator", cv_public, 191)
    check_eq("North Mini product sparse numerator", north_product_sparse_fg, 24)
    check_eq("North Mini product sparse denominator", north_product_sparse_public, 30)
    check_eq("North Mini product contract-visible numerator", north_product_cv_fg, 10)
    check_eq("North Mini product contract-visible denominator", north_product_cv_public, 31)

    verify_sqlite_integrity()
    verify_csv_parity()
    verify_publication_json_parity()
    verify_publication_html_parity(expected)
    verify_no_local_paths()
    verify_source_manifest_hashes()

    improvement = pct(north_product_sparse_fg, north_product_sparse_public) - pct(north_product_cv_fg, north_product_cv_public)
    print(f"Study B scenarios: {scenarios}")
    print(f"Study B cells: {cells}")
    print(f"Planned attempts: {planned}")
    print(f"Retained attempts: {retained}")
    print(f"Public-green attempts: {public_green}")
    print(f"Hidden passes: {hidden}")
    print(f"False-greens: {false_greens}")
    print(f"Missing attempts: {missing}")
    print()
    print("Sparse false-green:")
    print(f"{sparse_fg} / {sparse_public} = {pct(sparse_fg, sparse_public):.1f}%")
    print()
    print("Contract-visible false-green:")
    print(f"{cv_fg} / {cv_public} = {pct(cv_fg, cv_public):.1f}%")
    print()
    print("North Mini product sparse:")
    print(f"{north_product_sparse_fg} / {north_product_sparse_public} = {pct(north_product_sparse_fg, north_product_sparse_public):.1f}%")
    print()
    print("North Mini product contract-visible:")
    print(f"{north_product_cv_fg} / {north_product_cv_public} = {pct(north_product_cv_fg, north_product_cv_public):.1f}%")
    print()
    print("North Mini product improvement:")
    print(f"{improvement:.1f} percentage points")
    print()
    print("SQLite integrity: PASS")
    print("CSV parity: PASS")
    print("Publication JSON parity: PASS")
    print("Publication HTML parity: PASS")


if __name__ == "__main__":
    main()
