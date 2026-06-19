from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXTRA_COLUMNS = {
    "challenge_pack": "TEXT DEFAULT ''",
    "category": "TEXT DEFAULT ''",
    "difficulty": "TEXT DEFAULT ''",
    "vibe": "TEXT DEFAULT ''",
    "tags": "TEXT DEFAULT '[]'",
    "trap": "TEXT DEFAULT ''",
    "expected_behavior": "TEXT DEFAULT '[]'",
    "success_signals": "TEXT DEFAULT '[]'",
    "failure_modes": "TEXT DEFAULT '[]'",
    "rubric": "TEXT DEFAULT '[]'",
    "artifact_dir": "TEXT DEFAULT ''",
    "prompt_path": "TEXT DEFAULT ''",
    "baseline_output_path": "TEXT DEFAULT ''",
    "opencode_stdout_path": "TEXT DEFAULT ''",
    "opencode_stderr_path": "TEXT DEFAULT ''",
    "public_output_path": "TEXT DEFAULT ''",
    "hidden_output_path": "TEXT DEFAULT ''",
    "patch_path": "TEXT DEFAULT ''",
}


TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL UNIQUE,
  scenario TEXT NOT NULL,
  scenario_title TEXT NOT NULL,
  challenge_pack TEXT DEFAULT '',
  category TEXT DEFAULT '',
  difficulty TEXT DEFAULT '',
  vibe TEXT DEFAULT '',
  tags TEXT DEFAULT '[]',
  trap TEXT DEFAULT '',
  expected_behavior TEXT DEFAULT '[]',
  success_signals TEXT DEFAULT '[]',
  failure_modes TEXT DEFAULT '[]',
  rubric TEXT DEFAULT '[]',
  model TEXT,
  agent TEXT,
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  duration_seconds REAL NOT NULL,
  workdir TEXT NOT NULL,
  prompt TEXT NOT NULL,
  opencode_command TEXT NOT NULL,
  opencode_exit_code INTEGER,
  baseline_pass INTEGER NOT NULL,
  public_pass INTEGER NOT NULL,
  hidden_pass INTEGER NOT NULL,
  baseline_output TEXT NOT NULL,
  opencode_stdout TEXT NOT NULL,
  opencode_stderr TEXT NOT NULL,
  public_output TEXT NOT NULL,
  hidden_output TEXT NOT NULL,
  patch TEXT NOT NULL,
  artifact_dir TEXT DEFAULT '',
  prompt_path TEXT DEFAULT '',
  baseline_output_path TEXT DEFAULT '',
  opencode_stdout_path TEXT DEFAULT '',
  opencode_stderr_path TEXT DEFAULT '',
  public_output_path TEXT DEFAULT '',
  hidden_output_path TEXT DEFAULT '',
  patch_path TEXT DEFAULT '',
  patch_quality INTEGER,
  debug_discipline INTEGER,
  notes TEXT DEFAULT ''
);
"""

INDEX_SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_scenario ON runs(scenario);
CREATE INDEX IF NOT EXISTS idx_runs_pack ON runs(challenge_pack);
CREATE INDEX IF NOT EXISTS idx_runs_category ON runs(category);
CREATE INDEX IF NOT EXISTS idx_runs_model ON runs(model);
"""

EVIDENCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluator_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_run_id TEXT NOT NULL,
  target_model TEXT DEFAULT '',
  scenario TEXT NOT NULL,
  evaluator_model TEXT DEFAULT '',
  review_dir TEXT NOT NULL,
  schema_version TEXT DEFAULT '',
  validation_status TEXT DEFAULT '',
  verdict TEXT DEFAULT '',
  root_cause_category TEXT DEFAULT '',
  root_cause TEXT DEFAULT '',
  missed_contract TEXT DEFAULT '',
  patch_quality INTEGER,
  debug_discipline INTEGER,
  severity TEXT DEFAULT '',
  confidence REAL,
  evidence_json TEXT DEFAULT '[]',
  recommendation TEXT DEFAULT '',
  review_limits TEXT DEFAULT '',
  evaluation_json_path TEXT DEFAULT '',
  evaluation_agent_json_path TEXT DEFAULT '',
  evaluation_md_path TEXT DEFAULT '',
  working_board_path TEXT DEFAULT '',
  evaluator_stdout_path TEXT DEFAULT '',
  evaluator_stderr_path TEXT DEFAULT '',
  packet_path TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  UNIQUE(target_run_id, evaluator_model, review_dir)
);

CREATE TABLE IF NOT EXISTS scenario_audits (
  scenario TEXT PRIMARY KEY,
  audit_version TEXT NOT NULL DEFAULT 'v1',
  audit_status TEXT NOT NULL DEFAULT 'accepted'
    CHECK (audit_status IN ('accepted', 'revise_public_prompt', 'revise_hidden_test', 'quarantine')),
  risk_area TEXT NOT NULL DEFAULT 'business_correctness'
    CHECK (risk_area IN (
      'compatibility',
      'business_correctness',
      'financial',
      'state_corruption',
      'authorization_security',
      'data_integrity',
      'semantic_architecture'
    )),
  impact_weight INTEGER NOT NULL DEFAULT 3 CHECK (impact_weight BETWEEN 1 AND 5),
  inferability_score INTEGER NOT NULL DEFAULT 4 CHECK (inferability_score BETWEEN 1 AND 5),
  hidden_legitimacy_score INTEGER NOT NULL DEFAULT 4 CHECK (hidden_legitimacy_score BETWEEN 1 AND 5),
  implementation_flexibility_score INTEGER NOT NULL DEFAULT 4 CHECK (implementation_flexibility_score BETWEEN 1 AND 5),
  audit_notes TEXT DEFAULT '',
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evaluator_reviews_target_run_id ON evaluator_reviews(target_run_id);
CREATE INDEX IF NOT EXISTS idx_evaluator_reviews_scenario ON evaluator_reviews(scenario);
CREATE INDEX IF NOT EXISTS idx_evaluator_reviews_verdict ON evaluator_reviews(verdict);
CREATE INDEX IF NOT EXISTS idx_scenario_audits_status ON scenario_audits(audit_status);
CREATE INDEX IF NOT EXISTS idx_scenario_audits_risk_area ON scenario_audits(risk_area);
"""


SCENARIO_AUDIT_DEFAULTS: dict[str, dict[str, object]] = {
    "dependency_api_change": {
        "risk_area": "compatibility",
        "impact_weight": 4,
        "audit_notes": "Dependency adapter must propagate the new response contract, not only pass the visible ok check.",
    },
    "decimal_money_rounding": {
        "risk_area": "financial",
        "impact_weight": 5,
        "audit_notes": "Financial correctness depends on explicit cent rounding policy.",
    },
    "env_bool_parser": {
        "risk_area": "business_correctness",
        "impact_weight": 3,
        "audit_notes": "Configuration parsing should normalize common string forms, blanks, and whitespace.",
    },
    "csv_header_contract": {
        "risk_area": "data_integrity",
        "impact_weight": 4,
        "audit_notes": "Export schema is a documented data contract across empty and extra-field cases.",
    },
    "metric_semantic_mismatch": {
        "risk_area": "semantic_architecture",
        "impact_weight": 5,
        "audit_notes": "Challenge tests ownership of unit normalization between raw metric API and dashboard layer.",
    },
    "audit_log_redaction": {
        "risk_area": "authorization_security",
        "impact_weight": 5,
        "audit_notes": "Nested secret redaction is security-sensitive and must be recursive.",
    },
    "billing_proration": {
        "risk_area": "financial",
        "impact_weight": 5,
        "audit_notes": "Proration has direct billing impact and must handle rounding, clamps, and downgrades.",
    },
    "cart_discount_stack": {
        "risk_area": "financial",
        "impact_weight": 4,
        "audit_notes": "Discount policy must preserve ordering, zero floors, and input stability.",
    },
    "inventory_reservation_idempotency": {
        "risk_area": "state_corruption",
        "impact_weight": 5,
        "audit_notes": "Failed reservations must not mutate stock; retries must be idempotent.",
    },
    "tenant_cache_leak": {
        "risk_area": "authorization_security",
        "impact_weight": 5,
        "audit_notes": "Tenant isolation failures can expose cross-tenant data.",
    },
    "webhook_signature_raw_body": {
        "risk_area": "authorization_security",
        "impact_weight": 5,
        "audit_notes": "Signature verification must use exact raw bytes.",
    },
    "search_ranking_stability": {
        "risk_area": "business_correctness",
        "impact_weight": 4,
        "audit_notes": "Ranking stability affects user-visible relevance and deterministic tie-breaks.",
    },
    "support_sla_business_hours": {
        "risk_area": "business_correctness",
        "impact_weight": 4,
        "audit_notes": "SLA deadlines must respect business calendars and working-hour carry.",
    },
    "feature_rollout_bucket": {
        "risk_area": "business_correctness",
        "impact_weight": 4,
        "audit_notes": "Rollout buckets must be stable and respect percentage boundaries.",
    },
    "bulk_invite_dedupe": {
        "risk_area": "data_integrity",
        "impact_weight": 4,
        "audit_notes": "Invite dedupe must normalize casing/spacing and reject invalid invite rows.",
    },
    "markdown_slug_collision": {
        "risk_area": "compatibility",
        "impact_weight": 3,
        "audit_notes": "Slug generation must normalize punctuation and repeated collisions deterministically.",
    },
}


def migrate(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(runs)").fetchall()
    }
    for column, definition in EXTRA_COLUMNS.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE runs ADD COLUMN {column} {definition}")
    connection.commit()


def seed_scenario_audits(connection: sqlite3.Connection) -> None:
    from ci_vibe_lab.scenarios import scenario_ids

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for scenario in scenario_ids():
        defaults = SCENARIO_AUDIT_DEFAULTS.get(scenario, {})
        connection.execute(
            """
            INSERT OR IGNORE INTO scenario_audits (
              scenario,
              audit_version,
              audit_status,
              risk_area,
              impact_weight,
              inferability_score,
              hidden_legitimacy_score,
              implementation_flexibility_score,
              audit_notes,
              updated_at
            )
            VALUES (?, 'v1', 'accepted', ?, ?, 4, 4, 4, ?, ?)
            """,
            [
                scenario,
                defaults.get("risk_area", "business_correctness"),
                defaults.get("impact_weight", 3),
                defaults.get("audit_notes", "Default accepted audit seed; review before public benchmark release."),
                now,
            ],
        )
    connection.commit()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(TABLE_SCHEMA)
    migrate(connection)
    connection.executescript(EVIDENCE_SCHEMA)
    seed_scenario_audits(connection)
    connection.executescript(INDEX_SCHEMA)
    connection.commit()
    return connection


def insert_run(db_path: Path, row: dict[str, Any]) -> None:
    columns = list(row)
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO runs ({', '.join(columns)}) VALUES ({placeholders})"
    with connect(db_path) as connection:
        connection.execute(sql, [row[column] for column in columns])
        connection.commit()


def update_review(
    db_path: Path,
    run_id: str,
    *,
    patch_quality: int | None,
    debug_discipline: int | None,
    notes: str,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE runs
            SET patch_quality = ?, debug_discipline = ?, notes = ?
            WHERE run_id = ?
            """,
            [patch_quality, debug_discipline, notes, run_id],
        )
        connection.commit()


def upsert_evaluator_review(db_path: Path, row: dict[str, Any]) -> None:
    columns = [
        "target_run_id",
        "target_model",
        "scenario",
        "evaluator_model",
        "review_dir",
        "schema_version",
        "validation_status",
        "verdict",
        "root_cause_category",
        "root_cause",
        "missed_contract",
        "patch_quality",
        "debug_discipline",
        "severity",
        "confidence",
        "evidence_json",
        "recommendation",
        "review_limits",
        "evaluation_json_path",
        "evaluation_agent_json_path",
        "evaluation_md_path",
        "working_board_path",
        "evaluator_stdout_path",
        "evaluator_stderr_path",
        "packet_path",
        "created_at",
    ]
    placeholders = ", ".join("?" for _ in columns)
    update_columns = [column for column in columns if column not in {"target_run_id", "evaluator_model", "review_dir"}]
    update_sql = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
    sql = f"""
    INSERT INTO evaluator_reviews ({', '.join(columns)})
    VALUES ({placeholders})
    ON CONFLICT(target_run_id, evaluator_model, review_dir)
    DO UPDATE SET {update_sql}
    """
    with connect(db_path) as connection:
        connection.execute(sql, [row.get(column) for column in columns])
        connection.commit()


def load_evaluator_reviews(db_path: Path) -> list[sqlite3.Row]:
    with connect(db_path) as connection:
        return list(connection.execute("SELECT * FROM evaluator_reviews ORDER BY created_at, id"))


def load_scenario_audits(db_path: Path) -> list[sqlite3.Row]:
    with connect(db_path) as connection:
        return list(connection.execute("SELECT * FROM scenario_audits ORDER BY scenario"))
