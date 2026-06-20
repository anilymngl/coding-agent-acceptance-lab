from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path

from ci_vibe_lab.db import connect, insert_run, upsert_evaluator_review
from ci_vibe_lab.analysis import compute_trust_metrics, compute_value_metrics, effective_review_minutes, select_best_patches
from ci_vibe_lab.dashboard import load_runs as load_dashboard_runs
from ci_vibe_lab.evaluator import (
    build_opencode_evaluator_command,
    extract_scenario_from_packet,
    ingest_reviews,
    load_rows as load_evaluator_rows,
    prepare_workbench,
    validate_review,
    validate_working_board,
    working_board_template,
)
from ci_vibe_lab.report import make_ultimate_report, make_value_report, make_xray_report
from ci_vibe_lab.runner import PatchStats, estimate_review_minutes, git_patch_stats, inspect_run, run_command
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

    def test_maintenance_value_pack_has_ten_positive_value_cases(self) -> None:
        manifest = challenge_manifest(pack="maintenance_value")
        self.assertEqual(len(manifest), 10)
        self.assertEqual(
            {challenge["id"] for challenge in manifest},
            {
                "generated_openapi_refresh",
                "logger_warn_migration",
                "utcnow_timezone_migration",
                "regression_test_gap",
                "adapter_field_rename",
                "fixture_schema_migration",
                "docs_cli_sync",
                "import_hygiene_fix",
                "explicit_validation_matrix",
                "batch_splitter_utility",
            },
        )
        for challenge in manifest:
            self.assertEqual(challenge["pack"], "maintenance_value")
            self.assertTrue(challenge["vibe"], challenge["id"])
            self.assertGreaterEqual(len(challenge["expected_behavior"]), 3, challenge["id"])


class DatabaseTests(unittest.TestCase):
    def run_row(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "run_id": "run-1",
            "scenario": "dependency_api_change",
            "scenario_title": "Dependency API Change",
            "challenge_pack": "ci_forensics",
            "category": "dependency-boundary",
            "difficulty": "medium",
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
            "hidden_pass": 0,
            "baseline_output": "fail",
            "opencode_stdout": "{}",
            "opencode_stderr": "",
            "public_output": "pass",
            "hidden_output": "fail",
            "patch": "diff --git",
        }
        base.update(overrides)
        return base

    def test_insert_run_creates_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "results.sqlite"
            insert_run(db_path, self.run_row(hidden_pass=1, hidden_output="pass"))
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
            self.assertIn("patch_files_touched", columns)
            self.assertIn("patch_changed_lines", columns)
            self.assertIn("estimated_review_minutes", columns)
            self.assertIn("manual_review_minutes", columns)
            self.assertIn("review_decision", columns)

            with connect(db_path) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                audit_count = connection.execute("SELECT COUNT(*) FROM scenario_audits").fetchone()[0]

            self.assertIn("evaluator_reviews", tables)
            self.assertIn("scenario_audits", tables)
            self.assertGreater(audit_count, 0)

    def test_trust_gap_metrics_handle_zero_public_pass(self) -> None:
        metrics = compute_trust_metrics(
            [
                {"public_pass": 0, "hidden_pass": 0, "scenario": "a"},
                {"public_pass": 0, "hidden_pass": 0, "scenario": "b"},
            ]
        )
        self.assertEqual(metrics.public_pass, 0)
        self.assertEqual(metrics.false_green_rate, 0.0)
        self.assertEqual(metrics.public_red_rate, 1.0)

    def test_dashboard_loader_accepts_multiple_dbs_and_adds_source_db(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_a = Path(temp_dir) / "a.sqlite"
            db_b = Path(temp_dir) / "b.sqlite"
            insert_run(db_a, self.run_row(run_id="run-a", model="model/a"))
            insert_run(db_b, self.run_row(run_id="run-b", model="model/b"))

            rows = load_dashboard_runs([db_a, db_b])

            self.assertEqual(set(rows["run_id"]), {"run-a", "run-b"})
            self.assertIn("source_db", rows.columns)
            self.assertEqual(set(rows["source_db"]), {str(db_a), str(db_b)})

    def test_xray_report_excludes_quarantined_rows_from_headline_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "results.sqlite"
            insert_run(db_path, self.run_row(run_id="run-a", scenario="dependency_api_change"))
            insert_run(
                db_path,
                self.run_row(
                    run_id="run-b",
                    scenario="env_bool_parser",
                    scenario_title="Env Bool Parser",
                    public_pass=1,
                    hidden_pass=1,
                ),
            )
            with connect(db_path) as connection:
                connection.execute(
                    "UPDATE scenario_audits SET audit_status = 'quarantine' WHERE scenario = 'env_bool_parser'"
                )
                connection.commit()

            report = make_xray_report(
                db_paths=[db_path],
                model="test/model",
                include_artifact_index=False,
            )

            self.assertIn("| Runs | 1 |", report)
            self.assertIn("`env_bool_parser` | quarantine", report)

    def test_xray_report_counts_latest_review_per_target_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "results.sqlite"
            insert_run(
                db_path,
                self.run_row(
                    run_id="run-a",
                    scenario="dependency_api_change",
                    model="opencode/north-mini-code-free",
                ),
            )
            base_review = {
                "target_run_id": "run-a",
                "target_model": "opencode/north-mini-code-free",
                "scenario": "dependency_api_change",
                "evaluator_model": "deepseek/deepseek-v4-pro",
                "schema_version": "ci-vibe-evaluator/v1",
                "validation_status": "valid",
                "verdict": "public_green_hidden_red",
                "root_cause": "old diagnosis",
                "missed_contract": "old contract",
                "patch_quality": 2,
                "debug_discipline": 2,
                "severity": "medium",
                "confidence": 0.8,
                "evidence_json": "[]",
                "recommendation": "old",
                "review_limits": "fixture",
            }
            upsert_evaluator_review(
                db_path,
                base_review
                | {
                    "review_dir": "runs/old",
                    "root_cause_category": "missed_hidden_contract",
                    "created_at": "2026-06-19T00:00:00+00:00",
                },
            )
            upsert_evaluator_review(
                db_path,
                base_review
                | {
                    "review_dir": "runs/new",
                    "root_cause_category": "edge_case_gap",
                    "root_cause": "new diagnosis",
                    "created_at": "2026-06-19T01:00:00+00:00",
                },
            )

            report = make_xray_report(
                db_paths=[db_path],
                model="opencode/north-mini-code-free",
                include_artifact_index=False,
            )

            self.assertIn("Public-green/hidden-red target runs reviewed: 1/1 (2 review rows indexed).", report)
            self.assertIn("| `edge_case_gap` | 1 |", report)
            self.assertNotIn("| `missed_hidden_contract` | 1 |", report)

    def test_patch_stats_and_review_minute_heuristic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            (repo / "a.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=CI Vibe Lab",
                    "-c",
                    "user.email=ci-vibe-lab@example.invalid",
                    "commit",
                    "-m",
                    "seed",
                ],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            (repo / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
            (repo / "b.txt").write_text("new\n", encoding="utf-8")

            stats = git_patch_stats(repo)

            self.assertEqual(stats.files_touched, 1)
            self.assertEqual(stats.added_lines, 1)
            self.assertEqual(stats.deleted_lines, 0)
            self.assertEqual(estimate_review_minutes(stats), 4.65)
            self.assertEqual(estimate_review_minutes(PatchStats(files_touched=100, added_lines=1000, deleted_lines=1000)), 30.0)

    def test_value_metrics_select_best_hidden_passing_attempt_and_manual_override(self) -> None:
        rows = [
            {
                "model": "model/a",
                "scenario": "generated_openapi_refresh",
                "public_pass": 1,
                "hidden_pass": 1,
                "patch_changed_lines": 20,
                "estimated_review_minutes": 8,
                "manual_review_minutes": "",
                "started_at": "2026-01-01T00:00:02+00:00",
            },
            {
                "model": "model/a",
                "scenario": "generated_openapi_refresh",
                "public_pass": 1,
                "hidden_pass": 1,
                "patch_changed_lines": 5,
                "estimated_review_minutes": 7,
                "manual_review_minutes": 4,
                "started_at": "2026-01-01T00:00:03+00:00",
            },
            {
                "model": "model/a",
                "scenario": "logger_warn_migration",
                "public_pass": 1,
                "hidden_pass": 0,
                "patch_changed_lines": 2,
                "estimated_review_minutes": 4,
                "started_at": "2026-01-01T00:00:04+00:00",
            },
        ]

        selected = select_best_patches(rows)
        metrics = compute_value_metrics(rows)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["patch_changed_lines"], 5)
        self.assertEqual(effective_review_minutes(selected[0]), 4.0)
        self.assertEqual(metrics.best_of_three_scenarios, 2)
        self.assertEqual(metrics.best_of_three_successes, 1)
        self.assertEqual(metrics.accepted_patches_per_review_hour, 15.0)

    def test_value_report_renders_expected_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "results.sqlite"
            insert_run(
                db_path,
                self.run_row(
                    run_id="run-value-1",
                    scenario="generated_openapi_refresh",
                    scenario_title="Generated OpenAPI Refresh",
                    challenge_pack="maintenance_value",
                    model="opencode/north-mini-code-free",
                    public_pass=1,
                    hidden_pass=1,
                    patch_files_touched=1,
                    patch_added_lines=4,
                    patch_deleted_lines=1,
                    patch_changed_lines=5,
                    estimated_review_minutes=4.5,
                ),
            )

            report = make_value_report(
                db_paths=[db_path],
                model="opencode/north-mini-code-free",
                pack="maintenance_value",
                include_artifact_index=True,
            )

            self.assertIn("# Maintenance Value Report", report)
            self.assertIn("Accepted patches / selected-review hour", report)
            self.assertIn("Accepted patches / all-attempt review hour", report)
            self.assertIn("Best-of-3 scenario success", report)
            self.assertIn("## Reviewability Table", report)
            self.assertIn("## Artifact Index", report)

    def test_ultimate_report_renders_full_run_comparison_and_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            north_db = root / "north.sqlite"
            deepseek_db = root / "deepseek.sqlite"
            partial_db = root / "glm.sqlite"
            insert_run(
                north_db,
                self.run_row(
                    run_id="north-ci",
                    scenario="dependency_api_change",
                    challenge_pack="ci_forensics",
                    model="opencode/north-mini-code-free",
                    public_pass=1,
                    hidden_pass=1,
                ),
            )
            insert_run(
                north_db,
                self.run_row(
                    run_id="north-product",
                    scenario="billing_proration",
                    scenario_title="Billing Proration",
                    challenge_pack="product_workflows",
                    model="opencode/north-mini-code-free",
                    public_pass=1,
                    hidden_pass=0,
                ),
            )
            insert_run(
                north_db,
                self.run_row(
                    run_id="north-maint-1",
                    scenario="generated_openapi_refresh",
                    scenario_title="Generated OpenAPI Refresh",
                    challenge_pack="maintenance_value",
                    model="opencode/north-mini-code-free",
                    public_pass=1,
                    hidden_pass=0,
                    estimated_review_minutes=4.0,
                ),
            )
            insert_run(
                north_db,
                self.run_row(
                    run_id="north-maint-2",
                    scenario="generated_openapi_refresh",
                    scenario_title="Generated OpenAPI Refresh",
                    challenge_pack="maintenance_value",
                    model="opencode/north-mini-code-free",
                    public_pass=1,
                    hidden_pass=1,
                    patch_changed_lines=4,
                    estimated_review_minutes=4.0,
                ),
            )
            insert_run(
                deepseek_db,
                self.run_row(
                    run_id="deep-product",
                    scenario="billing_proration",
                    scenario_title="Billing Proration",
                    challenge_pack="product_workflows",
                    model="deepseek/deepseek-v4-pro",
                    public_pass=1,
                    hidden_pass=1,
                ),
            )
            insert_run(
                partial_db,
                self.run_row(
                    run_id="glm-ci",
                    scenario="dependency_api_change",
                    challenge_pack="ci_forensics",
                    model="opencode-go/glm-5.2",
                    public_pass=1,
                    hidden_pass=0,
                ),
            )

            report = make_ultimate_report(
                north_db_paths=[north_db],
                deepseek_db_paths=[deepseek_db],
                partial_db_paths=[partial_db],
                out_path=root / "ultimate.md",
            )

            self.assertIn("# North Mini Code Ultimate Eval Report", report)
            self.assertIn("## Like-For-Like Control Comparison", report)
            self.assertIn("## Why DeepSeek Was Not Dramatically Better", report)
            self.assertIn("## Partial GLM-5.2 Snapshot", report)
            self.assertIn("## Reproduce This Report", report)
            self.assertIn("`billing_proration`", report)
            self.assertIn(str(north_db), report)


class EvaluatorTests(unittest.TestCase):
    def test_ingest_reviews_upserts_evaluator_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "results.sqlite"
            insert_run(
                db_path,
                DatabaseTests().run_row(
                    run_id="target-run-1",
                    scenario="metric_semantic_mismatch",
                    scenario_title="Metric Semantic Mismatch",
                    model="opencode/north-mini-code-free",
                ),
            )
            review_dir = root / "reviews" / "target-run-1"
            review_dir.mkdir(parents=True)
            (review_dir / "EVALUATION_PACKET.md").write_text(
                "\n".join(
                    [
                        "# Evaluation Packet",
                        "- Run ID: `target-run-1`",
                        "- Challenge: `metric_semantic_mismatch` - Metric Semantic Mismatch",
                        "- Model under test: `opencode/north-mini-code-free`",
                    ]
                ),
                encoding="utf-8",
            )
            (review_dir / "evaluation.json").write_text(
                json.dumps(
                    {
                        "schema_version": "ci-vibe-evaluator/v1",
                        "review_source": "evaluator_agent",
                        "validation_status": "valid",
                        "verdict": "public_green_hidden_red",
                        "root_cause_category": "wrong_fix_strategy",
                        "root_cause": "Conversion was placed in the wrong layer.",
                        "missed_contract": "compute must return raw values.",
                        "patch_quality": 2,
                        "debug_discipline": 3,
                        "severity": "medium",
                        "confidence": 0.95,
                        "evidence": [{"source": "hidden_test_output", "quote": "FAIL", "interpretation": "failed"}],
                        "recommendation": "Move conversion to dashboard_total.",
                        "review_limits": "Fixture review.",
                    }
                ),
                encoding="utf-8",
            )

            count = ingest_reviews(db_path, root / "reviews", evaluator_model="deepseek/deepseek-v4-pro")

            self.assertEqual(count, 1)
            with connect(db_path) as connection:
                row = connection.execute("SELECT * FROM evaluator_reviews").fetchone()
            self.assertEqual(row["target_run_id"], "target-run-1")
            self.assertEqual(row["target_model"], "opencode/north-mini-code-free")
            self.assertEqual(row["patch_quality"], 2)

    def test_ingest_reviews_enforces_pydantic_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "results.sqlite"
            insert_run(db_path, DatabaseTests().run_row(run_id="target-run-1"))
            review_dir = root / "reviews" / "target-run-1"
            review_dir.mkdir(parents=True)
            (review_dir / "EVALUATION_PACKET.md").write_text(
                "\n".join(
                    [
                        "# Evaluation Packet",
                        "- Run ID: `target-run-1`",
                        "- Challenge: `dependency_api_change` - Dependency API Change",
                        "- Model under test: `opencode/north-mini-code-free`",
                    ]
                ),
                encoding="utf-8",
            )
            (review_dir / "evaluation.json").write_text(
                json.dumps(
                    {
                        "schema_version": "ci-vibe-evaluator/v1",
                        "review_source": "evaluator_agent",
                        "validation_status": "valid",
                        "verdict": "public_green_hidden_red",
                        "root_cause_category": "semantic_architecture",
                        "root_cause": "Invalid taxonomy category.",
                        "missed_contract": "Fixture.",
                        "patch_quality": 2,
                        "debug_discipline": 3,
                        "severity": "medium",
                        "confidence": 0.95,
                        "evidence": [{"source": "hidden_test_output", "quote": "FAIL", "interpretation": "failed"}],
                        "recommendation": "Use an allowed category.",
                        "review_limits": "Fixture review.",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                ingest_reviews(db_path, root / "reviews", evaluator_model="deepseek/deepseek-v4-pro")

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
