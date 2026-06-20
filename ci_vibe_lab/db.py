from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXTRA_COLUMNS = {
    "experiment_id": "TEXT DEFAULT ''",
    "prompt_mode": "TEXT DEFAULT 'sparse'",
    "contract_visibility": "TEXT DEFAULT ''",
    "scenario_audit_status": "TEXT DEFAULT ''",
    "scenario_audit_version": "TEXT DEFAULT ''",
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
    "patch_files_touched": "INTEGER DEFAULT 0",
    "patch_added_lines": "INTEGER DEFAULT 0",
    "patch_deleted_lines": "INTEGER DEFAULT 0",
    "patch_changed_lines": "INTEGER DEFAULT 0",
    "estimated_review_minutes": "REAL DEFAULT 0",
    "manual_review_minutes": "REAL",
    "review_decision": "TEXT DEFAULT ''",
}


TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL UNIQUE,
  experiment_id TEXT DEFAULT '',
  prompt_mode TEXT DEFAULT 'sparse',
  contract_visibility TEXT DEFAULT '',
  scenario_audit_status TEXT DEFAULT '',
  scenario_audit_version TEXT DEFAULT '',
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
  patch_files_touched INTEGER DEFAULT 0,
  patch_added_lines INTEGER DEFAULT 0,
  patch_deleted_lines INTEGER DEFAULT 0,
  patch_changed_lines INTEGER DEFAULT 0,
  estimated_review_minutes REAL DEFAULT 0,
  manual_review_minutes REAL,
  review_decision TEXT DEFAULT '',
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
CREATE INDEX IF NOT EXISTS idx_runs_experiment_id ON runs(experiment_id);
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
    CHECK (audit_status IN (
      'accepted',
      'accepted_sparse',
      'accepted_contract_visible',
      'revise_public_prompt',
      'revise_hidden_test',
      'quarantine'
    )),
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
  contract_visibility TEXT NOT NULL DEFAULT 'repo_inferable'
    CHECK (contract_visibility IN (
      'explicit',
      'repo_inferable',
      'standard_practice',
      'edge_inferable',
      'underexposed',
      'bug_or_invalid'
    )),
  fairness_classification TEXT NOT NULL DEFAULT 'semantic_contract_miss'
    CHECK (fairness_classification IN (
      'search_miss',
      'standard_engineering_miss',
      'semantic_contract_miss',
      'edge_inference_miss',
      'underexposed_contract',
      'harness_or_test_bug'
    )),
  inferability_score INTEGER NOT NULL DEFAULT 4 CHECK (inferability_score BETWEEN 1 AND 5),
  hidden_legitimacy_score INTEGER NOT NULL DEFAULT 4 CHECK (hidden_legitimacy_score BETWEEN 1 AND 5),
  public_prompt_sufficiency_score INTEGER NOT NULL DEFAULT 4 CHECK (public_prompt_sufficiency_score BETWEEN 1 AND 5),
  public_test_sufficiency_score INTEGER NOT NULL DEFAULT 3 CHECK (public_test_sufficiency_score BETWEEN 1 AND 5),
  standard_practice_score INTEGER NOT NULL DEFAULT 4 CHECK (standard_practice_score BETWEEN 1 AND 5),
  implementation_flexibility_score INTEGER NOT NULL DEFAULT 4 CHECK (implementation_flexibility_score BETWEEN 1 AND 5),
  recommended_lane TEXT NOT NULL DEFAULT 'sparse'
    CHECK (recommended_lane IN ('sparse', 'contract_visible', 'audit_visible', 'quarantine')),
  requires_prompt_revision INTEGER NOT NULL DEFAULT 0 CHECK (requires_prompt_revision IN (0, 1)),
  requires_hidden_revision INTEGER NOT NULL DEFAULT 0 CHECK (requires_hidden_revision IN (0, 1)),
  audited_by TEXT DEFAULT 'seed',
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
    "logger_warn_migration": {
        "risk_area": "compatibility",
        "impact_weight": 3,
        "contract_visibility": "standard_practice",
        "fairness_classification": "search_miss",
        "audit_notes": "Mechanical migration should search all runtime logging calls while preserving compatibility shim.",
    },
    "utcnow_timezone_migration": {
        "risk_area": "compatibility",
        "impact_weight": 3,
        "contract_visibility": "standard_practice",
        "fairness_classification": "search_miss",
        "audit_notes": "Mechanical datetime migration should cover all utcnow calls in the target helper file.",
    },
    "batch_splitter_utility": {
        "risk_area": "business_correctness",
        "impact_weight": 2,
        "contract_visibility": "edge_inferable",
        "fairness_classification": "edge_inference_miss",
        "recommended_lane": "contract_visible",
        "requires_prompt_revision": 1,
        "inferability_score": 2,
        "public_prompt_sufficiency_score": 2,
        "audit_notes": "Positive batch size is a reasonable utility edge contract, but sparse prompt does not expose it strongly enough for a headline fair-failure claim.",
    },
    "explicit_validation_matrix": {
        "risk_area": "business_correctness",
        "impact_weight": 3,
        "contract_visibility": "underexposed",
        "fairness_classification": "underexposed_contract",
        "recommended_lane": "contract_visible",
        "requires_prompt_revision": 1,
        "inferability_score": 2,
        "public_prompt_sufficiency_score": 2,
        "audit_notes": "Prompt references documented finite rules; scenario should include visible contract text before sparse failures are treated as strong model evidence.",
    },
    "adapter_field_rename": {
        "risk_area": "compatibility",
        "impact_weight": 3,
        "contract_visibility": "edge_inferable",
        "fairness_classification": "edge_inference_miss",
        "recommended_lane": "contract_visible",
        "requires_prompt_revision": 1,
        "inferability_score": 3,
        "public_prompt_sufficiency_score": 2,
        "audit_notes": "New-field mapping is visible; backward compatibility and optional-field preservation need stronger visible contract before headline sparse claims.",
    },
}


SCENARIO_AUDIT_EXTRA_COLUMNS = {
    "contract_visibility": "TEXT NOT NULL DEFAULT 'repo_inferable'",
    "fairness_classification": "TEXT NOT NULL DEFAULT 'semantic_contract_miss'",
    "public_prompt_sufficiency_score": "INTEGER NOT NULL DEFAULT 4",
    "public_test_sufficiency_score": "INTEGER NOT NULL DEFAULT 3",
    "standard_practice_score": "INTEGER NOT NULL DEFAULT 4",
    "recommended_lane": "TEXT NOT NULL DEFAULT 'sparse'",
    "requires_prompt_revision": "INTEGER NOT NULL DEFAULT 0",
    "requires_hidden_revision": "INTEGER NOT NULL DEFAULT 0",
    "audited_by": "TEXT DEFAULT 'seed'",
}

UNSET = object()


def migrate(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(runs)").fetchall()
    }
    for column, definition in EXTRA_COLUMNS.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE runs ADD COLUMN {column} {definition}")
    connection.commit()


def migrate_scenario_audits(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(scenario_audits)").fetchall()
    }
    for column, definition in SCENARIO_AUDIT_EXTRA_COLUMNS.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE scenario_audits ADD COLUMN {column} {definition}")
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
              contract_visibility,
              fairness_classification,
              inferability_score,
              hidden_legitimacy_score,
              public_prompt_sufficiency_score,
              public_test_sufficiency_score,
              standard_practice_score,
              implementation_flexibility_score,
              recommended_lane,
              requires_prompt_revision,
              requires_hidden_revision,
              audited_by,
              audit_notes,
              updated_at
            )
            VALUES (?, 'v1', 'accepted', ?, ?, ?, ?, ?, 4, ?, 3, 4, 4, ?, ?, ?, 'seed', ?, ?)
            """,
            [
                scenario,
                defaults.get("risk_area", "business_correctness"),
                defaults.get("impact_weight", 3),
                defaults.get("contract_visibility", "repo_inferable"),
                defaults.get("fairness_classification", "semantic_contract_miss"),
                defaults.get("inferability_score", 4),
                defaults.get("public_prompt_sufficiency_score", 4),
                defaults.get("recommended_lane", "sparse"),
                defaults.get("requires_prompt_revision", 0),
                defaults.get("requires_hidden_revision", 0),
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
    migrate_scenario_audits(connection)
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
    manual_review_minutes: object = UNSET,
    review_decision: object = UNSET,
) -> None:
    assignments = [
        "patch_quality = ?",
        "debug_discipline = ?",
        "notes = ?",
    ]
    params: list[Any] = [patch_quality, debug_discipline, notes]
    if manual_review_minutes is not UNSET:
        assignments.append("manual_review_minutes = ?")
        params.append(manual_review_minutes)
    if review_decision is not UNSET:
        assignments.append("review_decision = ?")
        params.append(review_decision)
    params.append(run_id)
    with connect(db_path) as connection:
        connection.execute(
            f"UPDATE runs SET {', '.join(assignments)} WHERE run_id = ?",
            params,
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
