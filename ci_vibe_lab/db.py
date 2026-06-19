from __future__ import annotations

import sqlite3
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


SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_scenario ON runs(scenario);
CREATE INDEX IF NOT EXISTS idx_runs_pack ON runs(challenge_pack);
CREATE INDEX IF NOT EXISTS idx_runs_category ON runs(category);
CREATE INDEX IF NOT EXISTS idx_runs_model ON runs(model);
"""


def migrate(connection: sqlite3.Connection) -> None:
    existing = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(runs)").fetchall()
    }
    for column, definition in EXTRA_COLUMNS.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE runs ADD COLUMN {column} {definition}")
    connection.commit()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    migrate(connection)
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
