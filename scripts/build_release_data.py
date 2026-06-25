#!/usr/bin/env python3
"""Build sanitized public research release data.

The release dataset is intentionally narrower than the operational SQLite
databases. It preserves recomputation fields and evidence hashes, while
excluding prompts, stdout/stderr, worktree paths, artifact paths, and provider
payloads.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_DIR = REPO_ROOT / "data" / "releases" / "v1"
EXPORT_DIR_NAME = "exports"
RELEASE_ID = "coding-agent-acceptance-lab-v1"
RELEASE_DATE = "2026-06-25"
SCHEMA_VERSION = "1"
AUDITED_SOURCE_COMMIT = "87319ed04df9c5f2b7658c9643666fcdbd2ad077"

REPRESENTATIVE_SCENARIOS = {
    "stale_generated_schema",
    "dependency_api_change",
    "decimal_money_rounding",
    "generated_openapi_refresh",
    "adapter_field_rename",
    "batch_splitter_utility",
    "audit_log_redaction",
    "inventory_reservation_idempotency",
    "support_sla_business_hours",
}

STUDY_B_SOURCES = [
    ("b_laguna_ci_cv", "laguna-xs2", "ci_forensics", "contract_visible", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-contract_visible.sqlite", "d4ac03c4b2c87a9f5e82245ca751e773c29348929cf31480de75dd81025d4e2e"),
    ("b_laguna_ci_sparse", "laguna-xs2", "ci_forensics", "sparse", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-sparse.sqlite", "417b5ecb67da8d621b6f9fab8b4b65cdf53b42b6480ef4efc902acaad1d3faca"),
    ("b_laguna_maint_cv", "laguna-xs2", "maintenance_value", "contract_visible", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-contract_visible.sqlite", "ccc0544ce7972b1097477fd771de283c53dca07f10021f3027d870df39c4b4b7"),
    ("b_laguna_maint_sparse", "laguna-xs2", "maintenance_value", "sparse", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-sparse.sqlite", "145e7beac32c51c315136bc2fd0a683f9f1328330427642585e7e0bd2a7a4d28"),
    ("b_laguna_product_cv", "laguna-xs2", "product_workflows", "contract_visible", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-contract_visible.sqlite", "c9494017b4088147dccdd7f78fbeb5cd87297ce10ca2170aa4ed127e27021e95"),
    ("b_laguna_product_sparse", "laguna-xs2", "product_workflows", "sparse", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-sparse.sqlite", "234adaa11dde36796abc776c560e244113d9fc3d5a651b490d39a4b68e72eedf"),
    ("b_north_ci_cv", "north-mini", "ci_forensics", "contract_visible", "opencode-zen", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-contract_visible.sqlite", "6ea34e8564a820bb18921f9686270cdd8373f7a8dbe3f9fb2418634b83f91e16"),
    ("b_north_ci_sparse", "north-mini", "ci_forensics", "sparse", "opencode-zen", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-sparse.sqlite", "a5bf61f497d6b4091bf403b27b174e6d21a0be157951cde1c4c676761212e184"),
    ("b_north_maint_cv", "north-mini", "maintenance_value", "contract_visible", "opencode-zen", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-contract_visible.sqlite", "3eb965e1f3e585a2144994946c14346074b1c3f56ba3936b4e7002beb552513b"),
    ("b_north_maint_sparse", "north-mini", "maintenance_value", "sparse", "opencode-zen", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-sparse.sqlite", "1eb1507222865ad565401521176a0368978bfcda3a513915dc69641c59a3a830"),
    ("b_north_product_cv_placeholder", "north-mini", "product_workflows", "contract_visible", "opencode-zen-placeholder", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-contract_visible.sqlite", "ee38ea0d0339ed1778480c74d3042ccbaa1869cbd6731f368d6a74164369d332"),
    ("b_north_product_sparse_placeholder", "north-mini", "product_workflows", "sparse", "opencode-zen-placeholder", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-sparse.sqlite", "9478084c32cf9b2b651095928c4741e4bb5241b36ab963805d232f5ae8a74c53"),
    ("b_north_product_cv", "north-mini", "product_workflows", "contract_visible", "openrouter", "data/matrix/north-mini-openrouter-completion/north-mini/product_workflows-contract_visible.sqlite", "9e99dc8c3783ae36fa922a0120e5b7607b7510cc116b61a7c5284d461eaf6b6f"),
    ("b_north_product_sparse", "north-mini", "product_workflows", "sparse", "openrouter", "data/matrix/north-mini-openrouter-completion/north-mini/product_workflows-sparse.sqlite", "02a68a7920476db9aa201e54115559c785de5416c108ad244eb039c8f6f4ccc1"),
]

STUDY_A_SOURCES = [
    ("a_north_ci_sparse", "north-mini", "ci_forensics", "sparse", "opencode-zen", "data/ci-forensics-v2.sqlite", False),
    ("a_north_ci_cv", "north-mini", "ci_forensics", "contract_visible", "opencode-zen", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/ci_forensics-contract_visible.sqlite", False),
    ("a_gemma_ci_sparse", "gemma4-12b", "ci_forensics", "sparse", "ollama-local", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/ci_forensics-sparse.sqlite", False),
    ("a_gemma_ci_cv", "gemma4-12b", "ci_forensics", "contract_visible", "ollama-local", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/ci_forensics-contract_visible.sqlite", False),
    ("a_deepseek_ci_sparse", "deepseek-v4-pro", "ci_forensics", "sparse", "deepseek-api", "data/ci-forensics-deepseek.sqlite", False),
    ("a_deepseek_ci_cv", "deepseek-v4-pro", "ci_forensics", "contract_visible", "deepseek-api", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/ci_forensics-contract_visible.sqlite", False),
    ("a_laguna_ci_sparse", "laguna-xs2", "ci_forensics", "sparse", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-sparse.sqlite", True),
    ("a_laguna_ci_cv", "laguna-xs2", "ci_forensics", "contract_visible", "openrouter", "data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-contract_visible.sqlite", True),
    ("a_north_maint_sparse", "north-mini", "maintenance_value", "sparse", "opencode-zen", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/maintenance_value-sparse.sqlite", False),
    ("a_north_maint_cv", "north-mini", "maintenance_value", "contract_visible", "opencode-zen", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/maintenance_value-contract_visible.sqlite", False),
    ("a_gemma_maint_sparse", "gemma4-12b", "maintenance_value", "sparse", "ollama-local", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/maintenance_value-sparse.sqlite", False),
    ("a_gemma_maint_cv", "gemma4-12b", "maintenance_value", "contract_visible", "ollama-local", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/maintenance_value-contract_visible.sqlite", False),
    ("a_deepseek_maint_sparse", "deepseek-v4-pro", "maintenance_value", "sparse", "deepseek-api", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/maintenance_value-sparse.sqlite", False),
    ("a_deepseek_maint_cv", "deepseek-v4-pro", "maintenance_value", "contract_visible", "deepseek-api", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/maintenance_value-contract_visible.sqlite", False),
    ("a_north_product_sparse", "north-mini", "product_workflows", "sparse", "opencode-zen", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/product_workflows-sparse.sqlite", False),
    ("a_north_product_cv", "north-mini", "product_workflows", "contract_visible", "opencode-zen", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/north-mini/product_workflows-contract_visible.sqlite", False),
    ("a_gemma_product_sparse", "gemma4-12b", "product_workflows", "sparse", "ollama-local", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/product_workflows-sparse.sqlite", False),
    ("a_gemma_product_cv", "gemma4-12b", "product_workflows", "contract_visible", "ollama-local", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/gemma4-12b/product_workflows-contract_visible.sqlite", False),
    ("a_deepseek_product_sparse", "deepseek-v4-pro", "product_workflows", "sparse", "deepseek-api", "data/control-results.sqlite", False),
    ("a_deepseek_product_cv", "deepseek-v4-pro", "product_workflows", "contract_visible", "deepseek-api", "data/matrix/north-mini-vs-gemma4-12b-2026-06-21/deepseek-v4-pro/product_workflows-contract_visible.sqlite", False),
]

SUPPORTING_GEMMA_SOURCES = [
    ("gemma_two_e4b_sparse", "gemma4-e4b", "maintenance_value", "sparse", "ollama-local", "data/matrix/local-gemma4-two-model-2026-06-20/gemma4-e4b/maintenance_value-sparse.sqlite"),
    ("gemma_two_31b_sparse", "gemma4-31b", "maintenance_value", "sparse", "ollama-local", "data/matrix/local-gemma4-two-model-2026-06-20/gemma4-31b/maintenance_value-sparse.sqlite"),
    ("gemma_smallest_e4b_sparse", "gemma4-e4b", "maintenance_value", "sparse", "ollama-local", "data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value-sparse.sqlite"),
    ("gemma_smallest_e4b_cv", "gemma4-e4b", "maintenance_value", "contract_visible", "ollama-local", "data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-e4b/maintenance_value-contract_visible.sqlite"),
    ("gemma_smallest_12b_sparse", "gemma4-12b", "maintenance_value", "sparse", "ollama-local", "data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value-sparse.sqlite"),
    ("gemma_smallest_12b_cv", "gemma4-12b", "maintenance_value", "contract_visible", "ollama-local", "data/matrix/local-gemma4-smallest-two-2026-06-20/gemma4-12b/maintenance_value-contract_visible.sqlite"),
]


@dataclass(frozen=True)
class Source:
    source_id: str
    system_id: str
    pack: str
    prompt_lane: str
    route: str
    relpath: str
    expected_sha256: str | None = None
    first_attempt_only: bool = False


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_json_hash(value: object) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def provider_for(model: str, route: str) -> str:
    if route == "openrouter" or model.startswith("openrouter/"):
        return "openrouter"
    if route == "opencode-zen" or model.startswith("opencode/"):
        return "opencode"
    if model.startswith("ollama/"):
        return "ollama"
    if model.startswith("deepseek/"):
        return "deepseek"
    return "unknown"


def open_source_db(relpath: str) -> sqlite3.Connection:
    db_path = REPO_ROOT / relpath
    if not db_path.exists():
        raise SystemExit(f"Missing source database: {relpath}")
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def source_info(source: Source) -> dict[str, object]:
    db_path = REPO_ROOT / source.relpath
    actual_sha = sha256_file(db_path)
    if source.expected_sha256 and actual_sha != source.expected_sha256:
        raise SystemExit(f"Source hash mismatch for {source.relpath}: {actual_sha} != {source.expected_sha256}")
    con = open_source_db(source.relpath)
    try:
        schema_version = con.execute("pragma schema_version").fetchone()[0]
        row_count = con.execute("select count(*) from runs").fetchone()[0]
        included = row_count
        if source.first_attempt_only:
            included = len(fetch_runs(source))
        experiment_ids = sorted({r[0] or "" for r in con.execute("select distinct experiment_id from runs").fetchall() if r[0]})
    finally:
        con.close()
    return {
        "source_id": source.source_id,
        "source_label": source.relpath,
        "sha256": actual_sha,
        "schema_version": schema_version,
        "original_row_count": row_count,
        "included_row_count": included,
        "experiment_ids": ",".join(experiment_ids),
        "system_notes": source.system_id,
        "route_notes": source.route,
    }


def study_a_source(row: tuple[str, str, str, str, str, str, bool]) -> Source:
    return Source(row[0], row[1], row[2], row[3], row[4], row[5], None, row[6])


def fetch_runs(source: Source) -> list[sqlite3.Row]:
    con = open_source_db(source.relpath)
    try:
        rows = con.execute(
            """
            select run_id, experiment_id, scenario, challenge_pack, model,
                   prompt_mode, public_pass, hidden_pass, duration_seconds,
                   patch, started_at
            from runs
            where challenge_pack = ?
              and prompt_mode = ?
            order by scenario, started_at, run_id
            """,
            (source.pack, source.prompt_lane),
        ).fetchall()
    finally:
        con.close()
    if source.first_attempt_only:
        first_rows: list[sqlite3.Row] = []
        seen: set[str] = set()
        for row in rows:
            if row["scenario"] in seen:
                continue
            seen.add(row["scenario"])
            first_rows.append(row)
        return first_rows
    return rows


def create_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        create table release_metadata (
          release_id text not null,
          release_date text not null,
          git_commit text not null,
          schema_version text not null,
          study_name text not null,
          description text not null
        );
        create table source_databases (
          source_id text primary key,
          source_label text not null,
          sha256 text not null,
          schema_version integer not null,
          original_row_count integer not null,
          included_row_count integer not null,
          experiment_ids text not null,
          system_notes text not null,
          route_notes text not null
        );
        create table scenarios (
          scenario_id text primary key,
          pack text not null,
          category text not null,
          difficulty text not null,
          description text not null,
          representative integer not null,
          contract_sha256 text not null,
          hidden_test_sha256 text not null
        );
        create table attempts (
          attempt_id text primary key,
          scenario_id text not null,
          pack text not null,
          system_id text not null,
          model text not null,
          provider text not null,
          route text not null,
          prompt_lane text not null,
          attempt_index integer not null,
          experiment_id text not null,
          planned integer not null,
          retained integer not null,
          exclusion_reason text not null,
          public_pass integer not null,
          hidden_pass integer not null,
          false_green integer not null,
          duration_seconds real not null,
          patch_sha256 text not null,
          source_id text not null,
          started_at text not null
        );
        create table exclusions (
          attempt_id text primary key,
          scenario_id text not null,
          system_id text not null,
          prompt_lane text not null,
          attempt_index integer not null,
          reason text not null,
          source_id text not null,
          audit_note text not null
        );
        create table cells (
          scenario_id text not null,
          pack text not null,
          system_id text not null,
          prompt_lane text not null,
          planned_attempts integer not null,
          retained_attempts integer not null,
          public_passes integer not null,
          hidden_passes integer not null,
          false_greens integer not null,
          any_hidden_pass integer not null,
          all_retained_hidden_pass integer not null,
          cell_status text not null,
          primary key (scenario_id, system_id, prompt_lane)
        );
        """
    )


def insert_metadata(con: sqlite3.Connection, study_name: str, description: str) -> None:
    con.execute(
        "insert into release_metadata values (?, ?, ?, ?, ?, ?)",
        (RELEASE_ID, RELEASE_DATE, AUDITED_SOURCE_COMMIT, SCHEMA_VERSION, study_name, description),
    )


def insert_scenarios(con: sqlite3.Connection, pack_filter: set[str] | None = None) -> None:
    from ci_vibe_lab.scenarios import SCENARIOS

    for scenario_id, sc in sorted(SCENARIOS.items()):
        if sc.pack == "data_semantics":
            continue
        if pack_filter and sc.pack not in pack_filter:
            continue
        contract_material = {
            "id": sc.id,
            "title": sc.title,
            "description": sc.description,
            "pack": sc.pack,
            "category": sc.category,
            "difficulty": sc.difficulty,
            "trap": sc.trap,
            "expected_behavior": sc.expected_behavior,
            "success_signals": sc.success_signals,
            "failure_modes": sc.failure_modes,
            "files": sc.files,
        }
        con.execute(
            "insert into scenarios values (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                scenario_id,
                sc.pack,
                sc.category,
                sc.difficulty,
                sc.description,
                1 if scenario_id in REPRESENTATIVE_SCENARIOS else 0,
                stable_json_hash(contract_material),
                sha256_bytes(sc.hidden_test.encode()),
            ),
        )


def insert_sources(con: sqlite3.Connection, sources: Iterable[Source]) -> None:
    for source in sources:
        info = source_info(source)
        con.execute(
            "insert into source_databases values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                info["source_id"],
                info["source_label"],
                info["sha256"],
                info["schema_version"],
                info["original_row_count"],
                info["included_row_count"],
                info["experiment_ids"],
                info["system_notes"],
                info["route_notes"],
            ),
        )


def insert_attempts(con: sqlite3.Connection, study_prefix: str, sources: list[Source], planned_per_cell: int) -> None:
    for source in sources:
        rows = fetch_runs(source)
        by_scenario: dict[str, list[sqlite3.Row]] = {}
        for row in rows:
            by_scenario.setdefault(row["scenario"], []).append(row)
        for scenario_id in sorted(by_scenario):
            scenario_rows = sorted(by_scenario[scenario_id], key=lambda r: (r["started_at"], r["run_id"]))
            for idx, row in enumerate(scenario_rows, start=1):
                patch_hash = sha256_bytes((row["patch"] or "").encode())
                public_pass = int(row["public_pass"])
                hidden_pass = int(row["hidden_pass"])
                model = row["model"] or source.system_id
                con.execute(
                    "insert into attempts values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"{study_prefix}:{source.source_id}:{source.system_id}:{source.prompt_lane}:{scenario_id}:{idx}",
                        scenario_id,
                        source.pack,
                        source.system_id,
                        model,
                        provider_for(model, source.route),
                        source.route,
                        source.prompt_lane,
                        idx,
                        row["experiment_id"] or "",
                        1,
                        1,
                        "",
                        public_pass,
                        hidden_pass,
                        1 if public_pass and not hidden_pass else 0,
                        float(row["duration_seconds"] or 0),
                        patch_hash,
                        source.source_id,
                        row["started_at"] or "",
                    ),
                )
            if planned_per_cell > len(scenario_rows):
                for idx in range(len(scenario_rows) + 1, planned_per_cell + 1):
                    attempt_id = f"{study_prefix}:{source.source_id}:{source.system_id}:{source.prompt_lane}:{scenario_id}:{idx}"
                    con.execute(
                        "insert into exclusions values (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            attempt_id,
                            scenario_id,
                            source.system_id,
                            source.prompt_lane,
                            idx,
                            "missing_attempt",
                            source.source_id,
                            "Operational quota/rate-limit boundary preserved from audited source evidence.",
                        ),
                    )


def derive_cells(con: sqlite3.Connection, planned_per_cell: int) -> None:
    rows = con.execute(
        """
        select scenario_id, pack, system_id, prompt_lane,
               count(*) as retained_attempts,
               sum(public_pass) as public_passes,
               sum(hidden_pass) as hidden_passes,
               sum(false_green) as false_greens
        from attempts
        group by scenario_id, pack, system_id, prompt_lane
        order by scenario_id, system_id, prompt_lane
        """
    ).fetchall()
    for row in rows:
        retained = int(row["retained_attempts"])
        hidden = int(row["hidden_passes"])
        public = int(row["public_passes"])
        false_greens = int(row["false_greens"])
        if retained < planned_per_cell:
            status = "incomplete"
        elif hidden == planned_per_cell:
            status = "all_hidden_pass"
        elif hidden == 0 and public > 0:
            status = "all_hidden_fail"
        else:
            status = "mixed"
        con.execute(
            "insert into cells values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                row["scenario_id"],
                row["pack"],
                row["system_id"],
                row["prompt_lane"],
                planned_per_cell,
                retained,
                public,
                hidden,
                false_greens,
                1 if hidden > 0 else 0,
                1 if retained == planned_per_cell and hidden == planned_per_cell else 0,
                status,
            ),
        )


def write_table_csv(con: sqlite3.Connection, table: str, path: Path) -> None:
    rows = con.execute(f"select * from {table} order by 1").fetchall()
    columns = [d[0] for d in con.execute(f"select * from {table} limit 0").description]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row[col] for col in columns])


def export_csvs(out_dir: Path, db_name: str, mapping: dict[str, str]) -> None:
    con = sqlite3.connect(out_dir / db_name)
    con.row_factory = sqlite3.Row
    try:
        for table, filename in mapping.items():
            write_table_csv(con, table, out_dir / EXPORT_DIR_NAME / filename)
    finally:
        con.close()


def build_study_db(out_dir: Path, db_name: str, study_name: str, description: str, sources: list[Source], planned_per_cell: int) -> None:
    con = sqlite3.connect(out_dir / db_name)
    con.row_factory = sqlite3.Row
    try:
        create_schema(con)
        insert_metadata(con, study_name, description)
        insert_sources(con, sources)
        insert_scenarios(con, {s.pack for s in sources})
        insert_attempts(con, study_name.lower().replace(" ", "-"), sources, planned_per_cell)
        derive_cells(con, planned_per_cell)
        con.commit()
        ok = con.execute("pragma integrity_check").fetchone()[0]
        if ok != "ok":
            raise SystemExit(f"{db_name} integrity_check failed: {ok}")
    finally:
        con.close()


def build_evaluator_reviews(out_dir: Path) -> None:
    sources = [Source(*src[:6], expected_sha256=src[6]) for src in STUDY_B_SOURCES]
    con = sqlite3.connect(out_dir / "evaluator-reviews.sqlite")
    con.execute(
        """
        create table evaluator_reviews (
          review_id text primary key,
          target_run_id text not null,
          scenario_id text not null,
          target_model text not null,
          evaluator_model text not null,
          validation_status text not null,
          verdict text not null,
          root_cause_category text not null,
          patch_quality integer,
          debug_discipline integer,
          severity text not null,
          confidence real,
          source_id text not null,
          created_at text not null
        )
        """
    )
    for source in sources:
        src_con = open_source_db(source.relpath)
        try:
            tables = {r[0] for r in src_con.execute("select name from sqlite_master where type='table'")}
            if "evaluator_reviews" not in tables:
                continue
            rows = src_con.execute(
                """
                select target_run_id, scenario, target_model, evaluator_model,
                       validation_status, verdict, root_cause_category,
                       patch_quality, debug_discipline, severity, confidence, created_at
                from evaluator_reviews
                order by scenario, target_run_id
                """
            ).fetchall()
            for row in rows:
                review_id = sha256_bytes(f"{source.source_id}:{row[0]}:{row[3]}".encode())
                con.execute(
                    "insert into evaluator_reviews values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (review_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], source.source_id, row[11]),
                )
        finally:
            src_con.close()
    con.commit()
    ok = con.execute("pragma integrity_check").fetchone()[0]
    if ok != "ok":
        raise SystemExit(f"evaluator-reviews.sqlite integrity_check failed: {ok}")
    con.close()


def build_supporting_gemma(out_dir: Path) -> None:
    sources = [Source(*src) for src in SUPPORTING_GEMMA_SOURCES]
    build_study_db(out_dir, "supporting-gemma.sqlite", "Supporting Gemma", "Separate local Gemma evidence; not pooled with Study A or Study B.", sources, 1)


def write_schema(out_dir: Path) -> None:
    tmp = sqlite3.connect(":memory:")
    create_schema(tmp)
    rows = tmp.execute("select sql from sqlite_master where type='table' order by name").fetchall()
    (out_dir / "schema.sql").write_text("\n\n".join(r[0] + ";" for r in rows if r[0]) + "\n", encoding="utf-8")
    tmp.close()


def write_readme(out_dir: Path) -> None:
    (out_dir / "README.md").write_text(
        """# Public Research Data Release v1

This directory contains deterministic, sanitized release data for the coding-agent acceptance study.

Operational databases under `data/matrix/` and raw run artifacts under `runs/` remain private mutable execution state. This release directory is the public recomputation layer.

Run:

```bash
uv run python scripts/verify_release_data.py
```

The verifier recomputes the published Study B metrics from `study-b.sqlite`, checks CSV parity, and compares the release data to the publication JSON/HTML.

Licensing: code is MIT; public research data and documentation are CC BY 4.0 unless otherwise stated.
""",
        encoding="utf-8",
    )


def write_provenance(out_dir: Path) -> None:
    sources = [Source(*src[:6], expected_sha256=src[6]) for src in STUDY_B_SOURCES]
    provenance = {
        "release_id": RELEASE_ID,
        "release_date": RELEASE_DATE,
        "schema_version": SCHEMA_VERSION,
        "audited_source_commit": AUDITED_SOURCE_COMMIT,
        "canonical_inputs": {
            "authored_contracts": "ci_vibe_lab/scenarios.py",
            "attempt_evidence": "local SQLite databases under data/matrix/ and selected Study A source DBs",
            "publication_derivations": "publishables/data/*.json",
            "public_release_evidence": "data/releases/v1/*.sqlite and exports/*.csv",
        },
        "study_b_sources": [source_info(s) for s in sources],
        "study_a_sources": [source_info(study_a_source(src)) for src in STUDY_A_SOURCES],
        "supporting_gemma_sources": [source_info(Source(*src)) for src in SUPPORTING_GEMMA_SOURCES],
        "sanitization": [
            "Excluded prompts, stdout/stderr, local worktree paths, artifact paths, provider payloads, and raw credentials.",
            "Preserved model, provider, route, prompt lane, scenario ID, retained/excluded state, pass/fail values, timestamps, duration, and evidence hashes.",
        ],
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(out_dir: Path) -> None:
    lines = []
    for path in sorted(p for p in out_dir.rglob("*") if p.is_file() and p.name != "checksums.sha256"):
        rel = path.relative_to(out_dir).as_posix()
        lines.append(f"{sha256_file(path)}  {rel}")
    (out_dir / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_dirs(expected: Path, actual: Path) -> None:
    expected_files = sorted(p.relative_to(expected) for p in expected.rglob("*") if p.is_file())
    actual_files = sorted(p.relative_to(actual) for p in actual.rglob("*") if p.is_file())
    if expected_files != actual_files:
        raise SystemExit(f"Release file set mismatch:\nexpected={expected_files}\nactual={actual_files}")
    mismatches = []
    for rel in expected_files:
        if (expected / rel).read_bytes() != (actual / rel).read_bytes():
            mismatches.append(rel.as_posix())
    if mismatches:
        raise SystemExit("Release files are stale: " + ", ".join(mismatches))


def build(out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / EXPORT_DIR_NAME).mkdir(parents=True)

    study_b_sources = [Source(*src[:6], expected_sha256=src[6]) for src in STUDY_B_SOURCES if "placeholder" not in src[0]]
    study_b_all_sources = [Source(*src[:6], expected_sha256=src[6]) for src in STUDY_B_SOURCES]
    study_a_sources = [study_a_source(src) for src in STUDY_A_SOURCES]

    build_study_db(out_dir, "study-b.sqlite", "Study B", "Pass@3 Laguna XS.2 vs North Mini depth matrix.", study_b_sources, 3)
    # Add zero-row placeholder sources to Study B provenance table after metrics are built.
    con = sqlite3.connect(out_dir / "study-b.sqlite")
    existing = {r[0] for r in con.execute("select source_id from source_databases")}
    for source in study_b_all_sources:
        if source.source_id not in existing:
            info = source_info(source)
            con.execute("insert into source_databases values (?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(info[k] for k in ["source_id", "source_label", "sha256", "schema_version", "original_row_count", "included_row_count", "experiment_ids", "system_notes", "route_notes"]))
    con.commit()
    con.close()

    build_study_db(out_dir, "study-a.sqlite", "Study A", "Pass@1 breadth evidence matching the publication summary.", study_a_sources, 1)
    build_evaluator_reviews(out_dir)
    build_supporting_gemma(out_dir)

    export_csvs(
        out_dir,
        "study-b.sqlite",
        {"attempts": "study-b-attempts.csv", "cells": "study-b-cells.csv", "exclusions": "study-b-exclusions.csv", "scenarios": "scenarios.csv"},
    )
    export_csvs(out_dir, "study-a.sqlite", {"attempts": "study-a-attempts.csv", "cells": "study-a-cells.csv"})
    export_csvs(out_dir, "evaluator-reviews.sqlite", {"evaluator_reviews": "evaluator-reviews.csv"})
    export_csvs(out_dir, "supporting-gemma.sqlite", {"attempts": "supporting-gemma.csv"})

    write_schema(out_dir)
    write_readme(out_dir)
    write_provenance(out_dir)
    write_checksums(out_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Build in a temp directory and compare with data/releases/v1")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_out = Path(tmp) / "v1"
            build(tmp_out)
            compare_dirs(tmp_out, RELEASE_DIR)
        print("Release data is up to date.")
    else:
        build(RELEASE_DIR)
        print(f"Built release data at {RELEASE_DIR}")


if __name__ == "__main__":
    main()
