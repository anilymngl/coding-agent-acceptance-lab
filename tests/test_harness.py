from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ci_vibe_lab.db import connect, insert_run
from ci_vibe_lab.evaluator import (
    build_opencode_evaluator_command,
    extract_scenario_from_packet,
    validate_review,
)
from ci_vibe_lab.runner import run_command
from ci_vibe_lab.scenarios import TEST_COMMAND, challenge_manifest, scenario_ids, write_hidden_test, write_scenario


class ScenarioTests(unittest.TestCase):
    def test_all_scenarios_start_red(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for scenario_id in scenario_ids():
                workdir = root / scenario_id
                write_scenario(scenario_id, workdir)
                result = run_command(TEST_COMMAND, workdir, timeout=30)
                self.assertNotEqual(result.returncode, 0, scenario_id)
                self.assertIn("FAILED", result.output)

    def test_hidden_test_can_be_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workdir = Path(temp_dir) / "scenario"
            write_scenario("dependency_api_change", workdir)
            hidden_path = write_hidden_test("dependency_api_change", workdir)
            self.assertTrue(hidden_path.exists())
            self.assertIn("HiddenBillingAcceptanceTests", hidden_path.read_text(encoding="utf-8"))

    def test_all_hidden_tests_are_valid_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for scenario_id in scenario_ids():
                workdir = root / scenario_id
                write_scenario(scenario_id, workdir)
                hidden_path = write_hidden_test(scenario_id, workdir)
                compile(hidden_path.read_text(encoding="utf-8"), str(hidden_path), "exec")

    def test_challenge_pack_has_at_least_ten_curated_cases(self) -> None:
        manifest = challenge_manifest()
        self.assertGreaterEqual(len(manifest), 10)
        for challenge in manifest:
            self.assertTrue(challenge["vibe"], challenge["id"])
            self.assertTrue(challenge["trap"], challenge["id"])
            self.assertGreaterEqual(len(challenge["expected_behavior"]), 3, challenge["id"])
            self.assertGreaterEqual(len(challenge["success_signals"]), 3, challenge["id"])
            self.assertGreaterEqual(len(challenge["failure_modes"]), 3, challenge["id"])


class DatabaseTests(unittest.TestCase):
    def test_insert_run_creates_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "results.sqlite"
            insert_run(
                db_path,
                {
                    "run_id": "run-1",
                    "scenario": "dependency_api_change",
                    "scenario_title": "Dependency API Change",
                    "model": "test/model",
                    "agent": "build",
                    "started_at": "2026-01-01T00:00:00+00:00",
                    "ended_at": "2026-01-01T00:00:01+00:00",
                    "duration_seconds": 1.0,
                    "workdir": "/tmp/work",
                    "prompt": "fix it",
                    "opencode_command": "[]",
                    "opencode_exit_code": 0,
                    "baseline_pass": 0,
                    "public_pass": 1,
                    "hidden_pass": 1,
                    "baseline_output": "fail",
                    "opencode_stdout": "{}",
                    "opencode_stderr": "",
                    "public_output": "pass",
                    "hidden_output": "pass",
                    "patch": "diff --git",
                },
            )
            with sqlite3.connect(db_path) as connection:
                count = connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            self.assertEqual(count, 1)

    def test_legacy_database_is_migrated_before_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "legacy.sqlite"
            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    """
                    CREATE TABLE runs (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      run_id TEXT NOT NULL UNIQUE,
                      scenario TEXT NOT NULL,
                      scenario_title TEXT NOT NULL,
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
                      patch_quality INTEGER,
                      debug_discipline INTEGER,
                      notes TEXT DEFAULT ''
                    )
                    """
                )
                connection.commit()

            with connect(db_path) as connection:
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(runs)").fetchall()
                }

            self.assertIn("challenge_pack", columns)
            self.assertIn("artifact_dir", columns)


class EvaluatorTests(unittest.TestCase):
    def test_evaluator_command_uses_current_review_dir(self) -> None:
        review_dir = Path("/tmp/ci-vibe-review")
        command = build_opencode_evaluator_command(
            review_dir=review_dir,
            model="deepseek/deepseek-v4-pro",
            agent=None,
            opencode_bin="opencode",
            auto_approve=True,
        )
        self.assertEqual(
            command[:7],
            ["opencode", "run", "--dir", str(review_dir.resolve()), "--format", "json", "--model"],
        )
        self.assertIn("deepseek/deepseek-v4-pro", command)
        self.assertIn("--dangerously-skip-permissions", command)

    def test_summary_extracts_indented_challenge_line(self) -> None:
        packet = "        - Challenge: `csv_header_contract` - CSV Header Contract\n"
        self.assertEqual(extract_scenario_from_packet(packet, "fallback"), "csv_header_contract")

    def test_validator_requires_exact_packet_quotes(self) -> None:
        packet = "Patch says: return EXPORT_COLUMNS\nHidden says: FAIL: test_empty_export"
        row = {
            "public_pass": 1,
            "hidden_pass": 0,
        }
        review = {
            "schema_version": "ci-vibe-evaluator/v1",
            "review_source": "evaluator_agent",
            "validation_status": "valid",
            "verdict": "public_green_hidden_red",
            "root_cause_category": "missed_hidden_contract",
            "root_cause": "The patch missed an export contract.",
            "missed_contract": "The empty export path still needs a header.",
            "patch_quality": 3,
            "debug_discipline": 3,
            "severity": "medium",
            "confidence": 0.9,
            "evidence": [
                {
                    "source": "hidden_test_output",
                    "quote": "FAIL: test_empty_export",
                    "interpretation": "Hidden acceptance failed.",
                },
                {
                    "source": "patch",
                    "quote": "return EXPORT_COLUMNS",
                    "interpretation": "The patch touched the visible column order only.",
                },
            ],
            "recommendation": "Handle empty exports and extra fields.",
            "review_limits": "Only packet evidence was used.",
        }
        self.assertEqual(validate_review(review, packet, row), [])

        bad_review = dict(review)
        bad_review["evidence"] = [
            {
                "source": "patch",
                "quote": "invented quote",
                "interpretation": "This quote is not in the packet.",
            }
        ]
        errors = validate_review(bad_review, packet, row)
        self.assertTrue(any("exact packet substring" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
