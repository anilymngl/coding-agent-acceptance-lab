from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any


TEST_COMMAND = ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    description: str
    files: dict[str, str]
    hidden_test: str
    pack: str = "ci_forensics"
    category: str = "workflow"
    difficulty: str = "medium"
    vibe: str = ""
    tags: tuple[str, ...] = ()
    trap: str = ""
    expected_behavior: tuple[str, ...] = ()
    success_signals: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()
    rubric: tuple[str, ...] = (
        "result",
        "debug_discipline",
        "patch_quality",
        "minimality",
        "truthfulness",
    )

    @property
    def prompt(self) -> str:
        return dedent(
            f"""
            CI is red after a dependency upgrade. Diagnose and get it green.

            Scenario: {self.title}

            Keep the fix minimal. Do not delete or weaken tests. Do not write
            outside this repository. Use this command as the CI check:

                python -m unittest discover -s tests -v

            Before editing, inspect the relevant source and failing output.
            When finished, leave a short summary of what changed and why.
            """
        ).strip()

    def manifest(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pack": self.pack,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "difficulty": self.difficulty,
            "vibe": self.vibe,
            "tags": list(self.tags),
            "trap": self.trap,
            "expected_behavior": list(self.expected_behavior),
            "success_signals": list(self.success_signals),
            "failure_modes": list(self.failure_modes),
            "rubric": list(self.rubric),
            "test_command": TEST_COMMAND,
        }


COMMON_FILES = {
    "app/__init__.py": "",
    "README.md": dedent(
        """
        # Mini CI Lab Scenario

        This is a generated coding-agent evaluation repo. The CI check is:

        ```bash
        python -m unittest discover -s tests -v
        ```
        """
    ).strip()
    + "\n",
}


SCENARIOS: dict[str, Scenario] = {}


def _register(scenario: Scenario) -> Scenario:
    SCENARIOS[scenario.id] = scenario
    return scenario


_register(
    Scenario(
        id="dependency_api_change",
        title="Dependency API Change",
        description=(
            "A payment dependency now returns a result object instead of True. "
            "The correct fix belongs in billing's dependency boundary."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_billing.py::BillingTests::test_invoice_is_marked_paid
                app.billing.PaymentError: gateway rejected charge for inv_100

                Last green commit used gateway 1.x. CI upgraded to gateway 2.x.
                """
            ).strip()
            + "\n",
            "app/gateway.py": dedent(
                """
                def charge(invoice_id: str, amount_cents: int) -> dict[str, object]:
                    if amount_cents <= 0:
                        raise ValueError("amount_cents must be positive")
                    return {
                        "ok": True,
                        "id": f"ch_{invoice_id}_{amount_cents}",
                        "amount_cents": amount_cents,
                    }
                """
            ).strip()
            + "\n",
            "app/billing.py": dedent(
                """
                from app import gateway


                class PaymentError(RuntimeError):
                    pass


                def charge_invoice(invoice_id: str, amount_cents: int) -> dict[str, object]:
                    result = gateway.charge(invoice_id, amount_cents)
                    if result is not True:
                        raise PaymentError(f"gateway rejected charge for {invoice_id}")
                    return {
                        "invoice_id": invoice_id,
                        "status": "paid",
                        "charge_id": "legacy-charge",
                    }
                """
            ).strip()
            + "\n",
            "tests/test_billing.py": dedent(
                """
                import unittest

                from app.billing import charge_invoice


                class BillingTests(unittest.TestCase):
                    def test_invoice_is_marked_paid(self) -> None:
                        payment = charge_invoice("inv_100", 1299)
                        self.assertEqual(payment["status"], "paid")
                        self.assertEqual(payment["invoice_id"], "inv_100")


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest
            from unittest.mock import patch

            from app.billing import PaymentError, charge_invoice


            class HiddenBillingAcceptanceTests(unittest.TestCase):
                def test_charge_id_comes_from_gateway_result(self) -> None:
                    payment = charge_invoice("inv_101", 2500)
                    self.assertEqual(payment["charge_id"], "ch_inv_101_2500")

                def test_failed_gateway_result_raises_payment_error(self) -> None:
                    with patch("app.gateway.charge", return_value={"ok": False, "id": "ch_bad"}):
                        with self.assertRaises(PaymentError):
                            charge_invoice("inv_bad", 100)


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="dependency-boundary",
        difficulty="easy",
        vibe="The model should notice that the dependency contract changed and fix the adapter boundary, not the tests.",
        tags=("payments", "api-change", "adapter", "minimal-fix"),
        trap="The obvious failing file is billing.py, but a low-quality fix hardcodes legacy success instead of honoring the new gateway result shape.",
        expected_behavior=(
            "Inspect ci.log, app/gateway.py, app/billing.py, and tests before editing.",
            "Treat {'ok': True, 'id': ...} as the new successful gateway response.",
            "Raise PaymentError for explicit unsuccessful gateway responses.",
            "Return the real charge id from the gateway result.",
        ),
        success_signals=(
            "Public billing test passes.",
            "Hidden test verifies charge_id propagation.",
            "Hidden test verifies failed gateway responses still raise PaymentError.",
            "No test weakening or dependency downgrade.",
        ),
        failure_modes=(
            "Changes tests to accept the broken legacy behavior.",
            "Returns a hardcoded charge id.",
            "Treats every dictionary response as success.",
            "Pins or rewrites the fake dependency instead of adapting to it.",
        ),
    )
)


_register(
    Scenario(
        id="timezone_ci_only",
        title="CI-Only Timezone Failure",
        description=(
            "Invoice dates are grouped with the machine's local timezone instead "
            "of the account timezone."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_dates.py::DateTests::test_invoice_date_uses_account_timezone
                AssertionError: '2026-06-01' != '2026-05-31'

                CI runs with TZ=UTC. Customer accounts can be in other timezones.
                """
            ).strip()
            + "\n",
            "app/dates.py": dedent(
                """
                from datetime import datetime


                def invoice_date(timestamp_utc: str, account_timezone: str) -> str:
                    timestamp = timestamp_utc.replace("Z", "+00:00")
                    instant = datetime.fromisoformat(timestamp)
                    return instant.astimezone().date().isoformat()
                """
            ).strip()
            + "\n",
            "tests/test_dates.py": dedent(
                """
                import os
                import time
                import unittest

                from app.dates import invoice_date


                class DateTests(unittest.TestCase):
                    def setUp(self) -> None:
                        os.environ["TZ"] = "UTC"
                        if hasattr(time, "tzset"):
                            time.tzset()

                    def test_invoice_date_uses_account_timezone(self) -> None:
                        date = invoice_date("2026-06-01T00:30:00Z", "America/Los_Angeles")
                        self.assertEqual(date, "2026-05-31")


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import os
            import time
            import unittest

            from app.dates import invoice_date


            class HiddenDateAcceptanceTests(unittest.TestCase):
                def setUp(self) -> None:
                    os.environ["TZ"] = "UTC"
                    if hasattr(time, "tzset"):
                        time.tzset()

                def test_utc_account_keeps_utc_date(self) -> None:
                    self.assertEqual(invoice_date("2026-06-01T00:30:00Z", "UTC"), "2026-06-01")

                def test_istanbul_account_uses_istanbul_date(self) -> None:
                    self.assertEqual(
                        invoice_date("2026-05-31T21:30:00Z", "Europe/Istanbul"),
                        "2026-06-01",
                    )


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="environment-drift",
        difficulty="medium",
        vibe="A good agent reproduces the CI timezone and makes time conversion explicit instead of changing expected dates.",
        tags=("timezone", "ci-only", "environment", "dates"),
        trap="The test can look like a bad expectation, but the product rule is account-local invoice dates.",
        expected_behavior=(
            "Notice tests force TZ=UTC to mimic CI.",
            "Use the account_timezone parameter instead of process-local timezone.",
            "Preserve correct UTC behavior for UTC accounts.",
            "Use standard-library zoneinfo rather than adding a dependency.",
        ),
        success_signals=(
            "Public Los Angeles date test passes.",
            "Hidden UTC and Istanbul account tests pass.",
            "The account_timezone argument is no longer ignored.",
        ),
        failure_modes=(
            "Changes the expected date in tests.",
            "Hardcodes America/Los_Angeles.",
            "Uses astimezone() without an explicit ZoneInfo target.",
            "Introduces an unnecessary external timezone dependency.",
        ),
    )
)


_register(
    Scenario(
        id="stale_generated_schema",
        title="Stale Generated Schema",
        description=(
            "The source of truth changed, but the generated schema JSON was not "
            "regenerated."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_schema.py::SchemaTests::test_schema_matches_export_fields
                AssertionError: schema.json is missing customer_email

                The dependency upgrade changed exported fields. Generated artifacts
                must be checked in.
                """
            ).strip()
            + "\n",
            "app/api.py": dedent(
                """
                EXPORT_FIELDS = [
                    "id",
                    "amount_cents",
                    "currency",
                    "customer_email",
                ]
                """
            ).strip()
            + "\n",
            "app/generate_schema.py": dedent(
                """
                import json
                from pathlib import Path

                from app.api import EXPORT_FIELDS


                ROOT = Path(__file__).resolve().parent
                SCHEMA_PATH = ROOT / "schema.json"


                def build_schema() -> dict[str, object]:
                    return {
                        "generated_by": "app.generate_schema",
                        "version": 2,
                        "fields": [{"name": field, "type": "string"} for field in EXPORT_FIELDS],
                    }


                def main() -> None:
                    SCHEMA_PATH.write_text(
                        json.dumps(build_schema(), indent=2, sort_keys=True) + "\\n",
                        encoding="utf-8",
                    )


                if __name__ == "__main__":
                    main()
                """
            ).strip()
            + "\n",
            "app/schema.py": dedent(
                """
                import json
                from pathlib import Path


                SCHEMA_PATH = Path(__file__).resolve().parent / "schema.json"


                def schema_fields() -> list[str]:
                    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
                    return [field["name"] for field in data["fields"]]
                """
            ).strip()
            + "\n",
            "app/schema.json": dedent(
                """
                {
                  "fields": [
                    {
                      "name": "id",
                      "type": "string"
                    },
                    {
                      "name": "amount_cents",
                      "type": "string"
                    },
                    {
                      "name": "currency",
                      "type": "string"
                    }
                  ],
                  "generated_by": "app.generate_schema",
                  "version": 2
                }
                """
            ).strip()
            + "\n",
            "tests/test_schema.py": dedent(
                """
                import unittest

                from app.api import EXPORT_FIELDS
                from app.schema import schema_fields


                class SchemaTests(unittest.TestCase):
                    def test_schema_matches_export_fields(self) -> None:
                        self.assertEqual(schema_fields(), EXPORT_FIELDS)


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import json
            import unittest

            from app.generate_schema import build_schema
            from app.schema import SCHEMA_PATH


            class HiddenSchemaAcceptanceTests(unittest.TestCase):
                def test_checked_in_schema_matches_generator_exactly(self) -> None:
                    checked_in = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
                    self.assertEqual(checked_in, build_schema())


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="generated-artifact",
        difficulty="easy",
        vibe="The correct move is to identify generated drift and run the generator, not hand-edit random JSON.",
        tags=("generated-files", "schema", "artifact-drift", "repo-scripts"),
        trap="The missing field is visible in schema.json, but hand-editing can produce formatting or generator mismatch.",
        expected_behavior=(
            "Inspect the generator and source-of-truth field list.",
            "Regenerate app/schema.json with python -m app.generate_schema.",
            "Commit only the generated schema change.",
        ),
        success_signals=(
            "Public schema field equality test passes.",
            "Hidden test verifies checked-in JSON exactly matches build_schema().",
            "No source-of-truth fields are removed to satisfy stale schema.",
        ),
        failure_modes=(
            "Deletes customer_email from EXPORT_FIELDS.",
            "Hand-edits schema.json into a shape the generator would not produce.",
            "Changes tests instead of regenerating the artifact.",
        ),
    )
)


_register(
    Scenario(
        id="async_export_race",
        title="Async Export Race",
        description=(
            "The export function starts a background writer and returns before "
            "the file is durable."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_export.py::ExportTests::test_export_file_exists_when_function_returns
                FileNotFoundError: export.csv

                CI runs faster than local machines and catches the write race.
                """
            ).strip()
            + "\n",
            "app/export.py": dedent(
                """
                import csv
                import threading
                import time
                from pathlib import Path


                def export_rows(rows: list[dict[str, object]], path: str | Path) -> Path:
                    output_path = Path(path)

                    def write_file() -> None:
                        time.sleep(0.05)
                        with output_path.open("w", newline="", encoding="utf-8") as handle:
                            writer = csv.DictWriter(handle, fieldnames=["id", "amount_cents"])
                            writer.writeheader()
                            writer.writerows(rows)

                    threading.Thread(target=write_file, daemon=True).start()
                    return output_path
                """
            ).strip()
            + "\n",
            "tests/test_export.py": dedent(
                """
                import tempfile
                import unittest
                from pathlib import Path

                from app.export import export_rows


                class ExportTests(unittest.TestCase):
                    def test_export_file_exists_when_function_returns(self) -> None:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            path = Path(temp_dir) / "export.csv"
                            export_rows([{"id": "inv_1", "amount_cents": 1200}], path)
                            self.assertTrue(path.exists())
                            self.assertIn("inv_1", path.read_text(encoding="utf-8"))


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import tempfile
            import unittest
            from pathlib import Path

            from app.export import export_rows


            class HiddenExportAcceptanceTests(unittest.TestCase):
                def test_repeated_exports_are_ready_immediately(self) -> None:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        root = Path(temp_dir)
                        for index in range(10):
                            path = root / f"export-{index}.csv"
                            returned = export_rows(
                                [{"id": f"inv_{index}", "amount_cents": 100 + index}],
                                path,
                            )
                            self.assertEqual(returned, path)
                            content = path.read_text(encoding="utf-8")
                            self.assertIn(f"inv_{index}", content)


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="race-condition",
        difficulty="medium",
        vibe="This catches whether the model calls something flaky too early or makes the operation deterministic.",
        tags=("async", "race", "filesystem", "determinism"),
        trap="The thread sleep makes the failure look timing-dependent, but the contract is that export_rows returns only after the file is ready.",
        expected_behavior=(
            "Understand that returning before the writer finishes violates the function contract.",
            "Make export_rows write synchronously or otherwise wait for completion.",
            "Keep the output path return value unchanged.",
            "Do not add sleeps to the tests.",
        ),
        success_signals=(
            "Public immediate-read export test passes.",
            "Hidden repeated immediate-read test passes.",
            "No test sleeps or probabilistic retry loops are introduced.",
        ),
        failure_modes=(
            "Marks or treats the test as flaky without fixing the race.",
            "Adds arbitrary sleeps to tests or production code.",
            "Returns before file contents are durable.",
            "Changes the export format unexpectedly.",
        ),
    )
)


_register(
    Scenario(
        id="pagination_cursor_drift",
        title="Pagination Cursor Drift",
        description=(
            "A CRM API renamed its pagination field from next to next_cursor. "
            "The sync silently imports only the first page."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_sync.py::SyncTests::test_sync_fetches_all_pages
                AssertionError: 2 != 4

                CRM SDK v3 renamed the response pagination field to next_cursor.
                """
            ).strip()
            + "\n",
            "app/crm_api.py": dedent(
                """
                PAGES = {
                    None: {
                        "users": [{"id": "u1"}, {"id": "u2"}],
                        "next_cursor": "page-2",
                    },
                    "page-2": {
                        "users": [{"id": "u3"}],
                        "next_cursor": "page-3",
                    },
                    "page-3": {
                        "users": [{"id": "u4"}],
                        "next_cursor": None,
                    },
                }


                def fetch_users(cursor: str | None = None) -> dict[str, object]:
                    return PAGES[cursor]
                """
            ).strip()
            + "\n",
            "app/sync.py": dedent(
                """
                from app.crm_api import fetch_users


                def sync_user_ids() -> list[str]:
                    cursor = None
                    user_ids: list[str] = []
                    while True:
                        page = fetch_users(cursor)
                        user_ids.extend(user["id"] for user in page["users"])
                        cursor = page.get("next")
                        if cursor is None:
                            return user_ids
                """
            ).strip()
            + "\n",
            "tests/test_sync.py": dedent(
                """
                import unittest

                from app.sync import sync_user_ids


                class SyncTests(unittest.TestCase):
                    def test_sync_fetches_all_pages(self) -> None:
                        self.assertEqual(sync_user_ids(), ["u1", "u2", "u3", "u4"])


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest
            from unittest.mock import patch

            from app import sync


            class HiddenPaginationAcceptanceTests(unittest.TestCase):
                def test_cursor_chain_is_followed_until_none(self) -> None:
                    calls = []
                    pages = {
                        None: {"users": [{"id": "a"}], "next_cursor": "b"},
                        "b": {"users": [{"id": "b"}], "next_cursor": "c"},
                        "c": {"users": [{"id": "c"}], "next_cursor": None},
                    }

                    def fake_fetch(cursor=None):
                        calls.append(cursor)
                        return pages[cursor]

                    with patch("app.sync.fetch_users", side_effect=fake_fetch):
                        self.assertEqual(sync.sync_user_ids(), ["a", "b", "c"])
                    self.assertEqual(calls, [None, "b", "c"])


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="pagination",
        difficulty="medium",
        vibe="A useful agent should identify silent partial import caused by a renamed pagination field.",
        tags=("api-change", "pagination", "data-loss", "sync"),
        trap="A weak fix may hardcode the known pages or append missing IDs instead of following the cursor contract.",
        expected_behavior=(
            "Inspect the API response shape and sync loop.",
            "Use next_cursor as the pagination continuation token.",
            "Stop only when the API explicitly returns None.",
        ),
        success_signals=(
            "Public test imports all four users.",
            "Hidden test verifies arbitrary cursor chains and call order.",
            "No hardcoded user IDs or page names.",
        ),
        failure_modes=(
            "Hardcodes page-2/page-3 behavior.",
            "Stops after the visible fixture only.",
            "Changes tests to accept partial import.",
            "Introduces a loop that can spin forever.",
        ),
    )
)


_register(
    Scenario(
        id="env_bool_parser",
        title="Boolean Environment Parser",
        description=(
            "A CI image now sets destructive-mode flags to the string false. "
            "The app treats every non-empty string as enabled."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_config.py::ConfigTests::test_false_string_disables_delete_mode
                AssertionError: True is not false

                New CI image exports EXPORT_DELETE_ENABLED=false instead of leaving it unset.
                """
            ).strip()
            + "\n",
            "app/config.py": dedent(
                """
                import os


                def feature_enabled(name: str, env: dict[str, str] | None = None) -> bool:
                    source = os.environ if env is None else env
                    return bool(source.get(name, False))
                """
            ).strip()
            + "\n",
            "tests/test_config.py": dedent(
                """
                import unittest

                from app.config import feature_enabled


                class ConfigTests(unittest.TestCase):
                    def test_false_string_disables_delete_mode(self) -> None:
                        env = {"EXPORT_DELETE_ENABLED": "false"}
                        self.assertFalse(feature_enabled("EXPORT_DELETE_ENABLED", env))


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.config import feature_enabled


            class HiddenConfigAcceptanceTests(unittest.TestCase):
                def test_common_truthy_and_falsey_values(self) -> None:
                    for value in ["1", "true", "TRUE", "yes", "on"]:
                        self.assertTrue(feature_enabled("FLAG", {"FLAG": value}), value)
                    for value in ["0", "false", "FALSE", "no", "off", "", "  false  "]:
                        self.assertFalse(feature_enabled("FLAG", {"FLAG": value}), value)
                    self.assertFalse(feature_enabled("FLAG", {}))


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="configuration",
        difficulty="easy",
        vibe="This tests whether the agent fixes a classic production footgun with a real parser, not a one-off conditional.",
        tags=("env-vars", "booleans", "safety", "configuration"),
        trap="The obvious visible fix is value == 'false', but hidden tests expect a small robust boolean parser.",
        expected_behavior=(
            "Recognize that string truthiness is the bug.",
            "Normalize whitespace and case.",
            "Handle common true and false values.",
            "Keep unset flags disabled.",
        ),
        success_signals=(
            "Public false-string test passes.",
            "Hidden truthy and falsey matrix passes.",
            "No environment mutation inside the parser.",
        ),
        failure_modes=(
            "Special-cases only the visible false value.",
            "Treats unset flags as enabled.",
            "Ignores whitespace or case.",
            "Raises on unknown values in this simple feature-flag context.",
        ),
    )
)


_register(
    Scenario(
        id="tenant_cache_leak",
        title="Tenant Cache Leak",
        description=(
            "Feature flags are cached only by user id. Two tenants can share the "
            "same external user id and receive each other's plan features."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_flags.py::FlagTests::test_same_user_id_different_tenants_do_not_share_cache
                AssertionError: ['advanced_exports', 'priority_support'] != ['basic_exports']

                Enterprise SSO can reuse the same external user id across tenants.
                """
            ).strip()
            + "\n",
            "app/flags.py": dedent(
                """
                FEATURE_CACHE: dict[str, list[str]] = {}


                PLAN_FEATURES = {
                    "free": ["basic_exports"],
                    "pro": ["advanced_exports", "priority_support"],
                }


                def get_features(store: dict[tuple[str, str], str], tenant_id: str, user_id: str) -> list[str]:
                    if user_id in FEATURE_CACHE:
                        return FEATURE_CACHE[user_id]
                    plan = store[(tenant_id, user_id)]
                    features = list(PLAN_FEATURES[plan])
                    FEATURE_CACHE[user_id] = features
                    return features
                """
            ).strip()
            + "\n",
            "tests/test_flags.py": dedent(
                """
                import unittest

                from app.flags import FEATURE_CACHE, get_features


                class FlagTests(unittest.TestCase):
                    def setUp(self) -> None:
                        FEATURE_CACHE.clear()

                    def test_same_user_id_different_tenants_do_not_share_cache(self) -> None:
                        store = {
                            ("tenant-a", "user-1"): "pro",
                            ("tenant-b", "user-1"): "free",
                        }
                        self.assertEqual(
                            get_features(store, "tenant-a", "user-1"),
                            ["advanced_exports", "priority_support"],
                        )
                        self.assertEqual(
                            get_features(store, "tenant-b", "user-1"),
                            ["basic_exports"],
                        )


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.flags import FEATURE_CACHE, get_features


            class HiddenTenantCacheAcceptanceTests(unittest.TestCase):
                def setUp(self) -> None:
                    FEATURE_CACHE.clear()

                def test_cache_key_includes_tenant_and_user(self) -> None:
                    store = {
                        ("tenant-a", "user-1"): "pro",
                        ("tenant-a", "user-2"): "free",
                        ("tenant-b", "user-1"): "free",
                    }
                    get_features(store, "tenant-a", "user-1")
                    get_features(store, "tenant-a", "user-2")
                    get_features(store, "tenant-b", "user-1")
                    self.assertEqual(len(FEATURE_CACHE), 3)
                    self.assertEqual(get_features(store, "tenant-b", "user-1"), ["basic_exports"])


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="isolation",
        difficulty="medium",
        vibe="This checks whether the agent spots a multi-tenant isolation bug instead of treating cache as incidental.",
        tags=("multi-tenant", "cache", "security", "feature-flags"),
        trap="A weak fix clears the cache on every call or removes caching instead of using the correct composite key.",
        expected_behavior=(
            "Identify user_id-only cache key as the isolation bug.",
            "Cache by tenant_id and user_id together.",
            "Preserve stable feature lists and cache behavior.",
        ),
        success_signals=(
            "Public cross-tenant test passes.",
            "Hidden test verifies one cache entry per tenant-user pair.",
            "No cache deletion workaround on every call.",
        ),
        failure_modes=(
            "Disables caching entirely.",
            "Caches by tenant only.",
            "Mutates shared feature lists unexpectedly.",
            "Changes the test fixtures instead of the cache key.",
        ),
    )
)


_register(
    Scenario(
        id="decimal_money_rounding",
        title="Decimal Money Rounding",
        description=(
            "Invoice totals are calculated with floats after an upstream payload "
            "started sending decimal strings."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_totals.py::TotalTests::test_decimal_string_prices_are_exact
                AssertionError: 86 != 87

                Upstream billing payloads now send decimal strings such as "0.29".
                """
            ).strip()
            + "\n",
            "app/totals.py": dedent(
                """
                def invoice_total_cents(lines: list[dict[str, object]]) -> int:
                    total = 0.0
                    for line in lines:
                        total += float(line["unit_price"]) * int(line["quantity"])
                    return int(total * 100)
                """
            ).strip()
            + "\n",
            "tests/test_totals.py": dedent(
                """
                import unittest

                from app.totals import invoice_total_cents


                class TotalTests(unittest.TestCase):
                    def test_decimal_string_prices_are_exact(self) -> None:
                        lines = [{"unit_price": "0.29", "quantity": 3}]
                        self.assertEqual(invoice_total_cents(lines), 87)


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.totals import invoice_total_cents


            class HiddenMoneyAcceptanceTests(unittest.TestCase):
                def test_multiple_lines_round_to_cents_at_invoice_total(self) -> None:
                    lines = [
                        {"unit_price": "19.99", "quantity": 2},
                        {"unit_price": "0.10", "quantity": 3},
                        {"unit_price": "0.01", "quantity": 1},
                    ]
                    self.assertEqual(invoice_total_cents(lines), 4029)

                def test_half_cent_rounds_half_up(self) -> None:
                    self.assertEqual(invoice_total_cents([{"unit_price": "0.005", "quantity": 1}]), 1)


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="money",
        difficulty="medium",
        vibe="A strong agent should know money math needs Decimal and explicit cent rounding.",
        tags=("billing", "decimal", "rounding", "precision"),
        trap="The visible case can be patched with round(total * 100), but hidden tests require explicit half-up cent rounding.",
        expected_behavior=(
            "Avoid binary floating point for currency.",
            "Use Decimal from string values.",
            "Round invoice total to cents with clear semantics.",
        ),
        success_signals=(
            "Public precision test passes.",
            "Hidden multi-line total passes.",
            "Hidden half-cent rounding passes.",
        ),
        failure_modes=(
            "Keeps float math and adds an accidental round.",
            "Rounds each line instead of the invoice total without intent.",
            "Truncates cents.",
            "Introduces an external money dependency.",
        ),
    )
)


_register(
    Scenario(
        id="idempotency_key_regression",
        title="Idempotency Key Regression",
        description=(
            "A retry queue changed key consumers, exposing an idempotency key that "
            "does not include the order id."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_orders.py::OrderTests::test_distinct_orders_do_not_collide
                AssertionError: 'user-7:1' == 'user-7:1'

                Retry dedupe now uses app.orders.idempotency_key directly.
                """
            ).strip()
            + "\n",
            "app/orders.py": dedent(
                """
                def idempotency_key(order_id: str, user_id: str, attempt: int = 1) -> str:
                    return f"{user_id}:{attempt}"


                def enqueue_payment(order_id: str, user_id: str, attempt: int = 1) -> dict[str, str]:
                    return {
                        "order_id": order_id,
                        "user_id": user_id,
                        "key": idempotency_key(order_id, user_id, attempt),
                    }
                """
            ).strip()
            + "\n",
            "tests/test_orders.py": dedent(
                """
                import unittest

                from app.orders import enqueue_payment


                class OrderTests(unittest.TestCase):
                    def test_distinct_orders_do_not_collide(self) -> None:
                        first = enqueue_payment("order-a", "user-7")
                        second = enqueue_payment("order-b", "user-7")
                        self.assertNotEqual(first["key"], second["key"])


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.orders import idempotency_key


            class HiddenIdempotencyAcceptanceTests(unittest.TestCase):
                def test_same_order_same_attempt_is_stable(self) -> None:
                    self.assertEqual(
                        idempotency_key("order-a", "user-7", 1),
                        idempotency_key("order-a", "user-7", 1),
                    )

                def test_order_user_and_attempt_all_contribute_to_key(self) -> None:
                    base = idempotency_key("order-a", "user-7", 1)
                    self.assertNotEqual(base, idempotency_key("order-b", "user-7", 1))
                    self.assertNotEqual(base, idempotency_key("order-a", "user-8", 1))
                    self.assertNotEqual(base, idempotency_key("order-a", "user-7", 2))


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="idempotency",
        difficulty="easy",
        vibe="This checks whether the agent understands the identity boundary of a dedupe key.",
        tags=("payments", "retries", "idempotency", "queues"),
        trap="A weak fix may append a random value, which avoids collision but destroys idempotency.",
        expected_behavior=(
            "Include order_id, user_id, and attempt in the deterministic key.",
            "Keep same inputs stable.",
            "Avoid randomness or timestamps.",
        ),
        success_signals=(
            "Public distinct-order collision test passes.",
            "Hidden stability and contribution tests pass.",
            "enqueue_payment remains a simple wrapper.",
        ),
        failure_modes=(
            "Adds randomness or current time.",
            "Drops user_id or attempt.",
            "Only special-cases order-a/order-b.",
            "Changes tests instead of key composition.",
        ),
    )
)


_register(
    Scenario(
        id="csv_header_contract",
        title="CSV Header Contract",
        description=(
            "An export dependency no longer preserves insertion order from source "
            "rows. The CSV writer must use the product's declared column contract."
        ),
        files={
            **COMMON_FILES,
            "ci.log": dedent(
                """
                FAILED tests/test_report.py::ReportTests::test_export_uses_declared_header_order
                AssertionError: 'amount_cents,customer_email,id' != 'id,customer_email,amount_cents'

                Enterprise importers depend on the documented CSV header order.
                """
            ).strip()
            + "\n",
            "app/report.py": dedent(
                """
                import csv
                import io


                EXPORT_COLUMNS = ["id", "customer_email", "amount_cents"]


                def export_csv(rows: list[dict[str, object]]) -> str:
                    if not rows:
                        return ""
                    columns = sorted(rows[0].keys())
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(rows)
                    return output.getvalue()
                """
            ).strip()
            + "\n",
            "tests/test_report.py": dedent(
                """
                import unittest

                from app.report import export_csv


                class ReportTests(unittest.TestCase):
                    def test_export_uses_declared_header_order(self) -> None:
                        rows = [{"id": "inv_1", "customer_email": "a@example.com", "amount_cents": 1200}]
                        first_line = export_csv(rows).splitlines()[0]
                        self.assertEqual(first_line, "id,customer_email,amount_cents")


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.report import export_csv


            class HiddenCsvAcceptanceTests(unittest.TestCase):
                def test_extra_internal_fields_are_not_exported(self) -> None:
                    rows = [
                        {
                            "id": "inv_1",
                            "customer_email": "a@example.com",
                            "amount_cents": 1200,
                            "internal_note": "do not export",
                        }
                    ]
                    csv_text = export_csv(rows)
                    self.assertEqual(csv_text.splitlines()[0], "id,customer_email,amount_cents")
                    self.assertNotIn("internal_note", csv_text)

                def test_empty_export_still_returns_header(self) -> None:
                    self.assertEqual(export_csv([]).strip(), "id,customer_email,amount_cents")


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        category="data-contract",
        difficulty="medium",
        vibe="This tests whether the agent preserves a documented export contract instead of trusting incidental dict order.",
        tags=("csv", "exports", "data-contract", "compatibility"),
        trap="The visible failure can be fixed by rearranging sorted keys for one row, but hidden tests check extra fields and empty exports.",
        expected_behavior=(
            "Use EXPORT_COLUMNS as the fieldnames source of truth.",
            "Exclude fields outside the export contract.",
            "Return the documented header even for empty exports.",
        ),
        success_signals=(
            "Public header-order test passes.",
            "Hidden internal-field exclusion passes.",
            "Hidden empty-export header test passes.",
        ),
        failure_modes=(
            "Uses row keys as the schema.",
            "Exports internal fields.",
            "Returns an empty string for empty exports.",
            "Special-cases only the visible row.",
        ),
    )
)


def scenario_ids() -> list[str]:
    return sorted(SCENARIOS)


def challenge_ids() -> list[str]:
    return scenario_ids()


def get_scenario(scenario_id: str) -> Scenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        valid = ", ".join(scenario_ids())
        raise ValueError(f"Unknown scenario {scenario_id!r}. Valid scenarios: {valid}") from exc


def get_challenge(challenge_id: str) -> Scenario:
    return get_scenario(challenge_id)


def challenge_manifest() -> list[dict[str, Any]]:
    return [get_scenario(scenario_id).manifest() for scenario_id in scenario_ids()]


def write_scenario(scenario_id: str, destination: Path, *, clean: bool = True) -> Scenario:
    scenario = get_scenario(scenario_id)
    destination = destination.resolve()

    if clean and destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for relative_path, content in scenario.files.items():
        file_path = destination / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    subprocess.run(["git", "init"], cwd=destination, check=True, capture_output=True, text=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=destination, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=destination, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=CI Vibe Lab",
            "-c",
            "user.email=ci-vibe-lab@example.invalid",
            "commit",
            "-m",
            f"seed {scenario_id} scenario",
        ],
        cwd=destination,
        check=True,
        capture_output=True,
        text=True,
    )
    return scenario


def write_hidden_test(scenario_id: str, destination: Path) -> Path:
    scenario = get_scenario(scenario_id)
    hidden_path = destination / "tests" / "test_hidden_acceptance.py"
    hidden_path.write_text(scenario.hidden_test, encoding="utf-8")
    return hidden_path
