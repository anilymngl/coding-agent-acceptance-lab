from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ci_vibe_lab.db import insert_run
from ci_vibe_lab.runner import run_command
from ci_vibe_lab.scenarios import TEST_COMMAND, scenario_ids, write_hidden_test, write_scenario


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


if __name__ == "__main__":
    unittest.main()

