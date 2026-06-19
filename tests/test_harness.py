from __future__ import annotations

import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ci_vibe_lab.db import connect, insert_run
from ci_vibe_lab.evaluator import (
    build_opencode_evaluator_command,
    extract_scenario_from_packet,
    load_rows as load_evaluator_rows,
    prepare_workbench,
    validate_review,
    validate_working_board,
    working_board_template,
)
from ci_vibe_lab.runner import inspect_run, run_command
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

    def test_inspect_latest_run_prints_artifact_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "results.sqlite"
            artifact_dir = root / "artifacts" / "run-1"
            artifact_dir.mkdir(parents=True)
            prompt_path = artifact_dir / "prompt.txt"
            stdout_path = artifact_dir / "opencode_stdout.jsonl"
            stderr_path = artifact_dir / "opencode_stderr.txt"
            public_path = artifact_dir / "public.txt"
            hidden_path = artifact_dir / "hidden.txt"
            patch_path = artifact_dir / "patch.diff"
            baseline_path = artifact_dir / "baseline.txt"
            for path, content in [
                (prompt_path, "agent prompt"),
                (stdout_path, "{\"type\":\"text\"}\n"),
                (stderr_path, ""),
                (public_path, "public ok"),
                (hidden_path, "hidden ok"),
                (patch_path, "diff --git"),
                (baseline_path, "baseline red"),
            ]:
                path.write_text(content, encoding="utf-8")
            insert_run(
                db_path,
                {
                    "run_id": "run-1",
                    "scenario": "dependency_api_change",
                    "scenario_title": "Dependency API Change",
                    "challenge_pack": "ci_forensics",
                    "model": "test/model",
                    "agent": "build",
                    "started_at": "2026-01-01T00:00:00+00:00",
                    "ended_at": "2026-01-01T00:00:01+00:00",
                    "duration_seconds": 1.0,
                    "workdir": str(root / "work"),
                    "prompt": "agent prompt",
                    "opencode_command": "[\"opencode\"]",
                    "opencode_exit_code": 0,
                    "baseline_pass": 0,
                    "public_pass": 1,
                    "hidden_pass": 1,
                    "baseline_output": "baseline red",
                    "opencode_stdout": "{\"type\":\"text\"}\n",
                    "opencode_stderr": "",
                    "public_output": "public ok",
                    "hidden_output": "hidden ok",
                    "patch": "diff --git",
                    "artifact_dir": str(artifact_dir),
                    "prompt_path": str(prompt_path),
                    "baseline_output_path": str(baseline_path),
                    "opencode_stdout_path": str(stdout_path),
                    "opencode_stderr_path": str(stderr_path),
                    "public_output_path": str(public_path),
                    "hidden_output_path": str(hidden_path),
                    "patch_path": str(patch_path),
                },
            )
            args = type(
                "Args",
                (),
                {
                    "db": str(db_path),
                    "run_id": None,
                    "latest": True,
                    "scenario": "dependency_api_change",
                    "model": None,
                    "full": True,
                },
            )()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                inspect_run(args)
            text = output.getvalue()
            self.assertIn("# Run Inspection: run-1", text)
            self.assertIn("raw OpenCode stdout JSONL", text)
            self.assertIn("Baseline/Public/Hidden pass: 0/1/1", text)
            self.assertIn("## Baseline Test Output", text)
            self.assertIn("baseline red", text)

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
    def test_prepare_workbench_creates_replay_and_shadow_repos(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            review_dir = Path(temp_dir) / "review"
            review_dir.mkdir()
            row = {
                "scenario": "dependency_api_change",
                "run_id": "run-1",
                "model": "model/a",
                "patch_path": "",
                "patch": "",
            }

            prepare_workbench(row, review_dir)  # type: ignore[arg-type]
            (review_dir / "WORKING_BOARD.md").write_text(
                working_board_template(row),  # type: ignore[arg-type]
                encoding="utf-8",
            )

            self.assertTrue((review_dir / "workbench/model_repo/tests/test_hidden_acceptance.py").exists())
            self.assertTrue((review_dir / "workbench/shadow_repo/tests/test_hidden_acceptance.py").exists())
            self.assertIn(
                "No patch content",
                (review_dir / "workbench/model_patch_apply.txt").read_text(encoding="utf-8"),
            )
            self.assertEqual(validate_working_board(review_dir), [])

    def test_load_rows_can_filter_target_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "results.sqlite"
            base = {
                "scenario": "dependency_api_change",
                "scenario_title": "Dependency API Change",
                "challenge_pack": "ci_forensics",
                "agent": "build",
                "started_at": "2026-01-01T00:00:00+00:00",
                "ended_at": "2026-01-01T00:00:01+00:00",
                "duration_seconds": 1.0,
                "workdir": str(Path(temp_dir) / "work"),
                "prompt": "prompt",
                "opencode_command": "[\"opencode\"]",
                "opencode_exit_code": 0,
                "baseline_pass": 0,
                "public_pass": 1,
                "hidden_pass": 0,
                "baseline_output": "baseline",
                "opencode_stdout": "{}",
                "opencode_stderr": "",
                "public_output": "public",
                "hidden_output": "hidden",
                "patch": "diff",
            }
            insert_run(db_path, {**base, "run_id": "run-a", "model": "model/a"})
            insert_run(db_path, {**base, "run_id": "run-b", "model": "model/b"})
            insert_run(
                db_path,
                {
                    **base,
                    "run_id": "run-c",
                    "model": "model/b",
                    "public_pass": 0,
                },
            )

            rows = load_evaluator_rows(
                db_path,
                hidden_only=True,
                pack=None,
                target_model="model/b",
                public_green_only=True,
            )

            self.assertEqual([row["run_id"] for row in rows], ["run-b"])

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

        extra_key_review = dict(review)
        extra_key_review["surprise"] = "not allowed"
        errors = validate_review(extra_key_review, packet, row)
        self.assertTrue(any("pydantic schema error" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
