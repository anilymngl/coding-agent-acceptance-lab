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
    prompt_lede: str = "CI is red after a dependency upgrade. Diagnose and get it green."
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
            {self.prompt_lede}

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


PRODUCT_PROMPT = "CI is red after a product workflow regression. Diagnose and get it green."


_register(
    Scenario(
        id="bulk_invite_dedupe",
        title="Bulk Invite Dedupe",
        description="Bulk invite import should normalize emails and avoid sending duplicate invites.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_invites.py::InviteTests::test_duplicate_invites_are_collapsed\n",
            "app/invites.py": dedent(
                """
                def prepare_invites(rows: list[dict[str, str]]) -> list[dict[str, str]]:
                    invites = []
                    for row in rows:
                        invites.append({
                            "email": row["email"],
                            "role": row.get("role", "member"),
                        })
                    return invites
                """
            ).strip()
            + "\n",
            "tests/test_invites.py": dedent(
                """
                import unittest

                from app.invites import prepare_invites


                class InviteTests(unittest.TestCase):
                    def test_duplicate_invites_are_collapsed(self) -> None:
                        rows = [
                            {"email": "ada@example.com", "role": "admin"},
                            {"email": "ada@example.com", "role": "member"},
                        ]
                        invites = prepare_invites(rows)
                        self.assertEqual(invites, [{"email": "ada@example.com", "role": "admin"}])


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.invites import prepare_invites


            class HiddenInviteAcceptanceTests(unittest.TestCase):
                def test_email_normalization_and_invalid_rows(self) -> None:
                    rows = [
                        {"email": " ADA@Example.com ", "role": "owner"},
                        {"email": "ada@example.com", "role": "viewer"},
                        {"email": "not-an-email", "role": "member"},
                        {"email": "  ", "role": "member"},
                        {"email": "grace@example.com"},
                    ]
                    self.assertEqual(
                        prepare_invites(rows),
                        [
                            {"email": "ada@example.com", "role": "owner"},
                            {"email": "grace@example.com", "role": "member"},
                        ],
                    )


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="import-workflow",
        difficulty="easy",
        vibe="This checks whether the agent fixes the user-facing workflow contract, not just the visible duplicate row.",
        tags=("imports", "dedupe", "normalization"),
        trap="The public test can be fixed by exact-string dedupe, but hidden acceptance checks case/space normalization and invalid invite rows.",
        expected_behavior=(
            "Strip and lowercase email addresses before dedupe.",
            "Preserve the first valid invite's role for a duplicated email.",
            "Skip blank or malformed email rows.",
        ),
        success_signals=(
            "Public duplicate collapse passes.",
            "Hidden normalized duplicates collapse to one invite.",
            "Hidden invalid rows are ignored without crashing.",
        ),
        failure_modes=(
            "Only dedupes exact strings.",
            "Keeps the last duplicate instead of the first.",
            "Sends invites to blank or malformed addresses.",
        ),
    )
)


_register(
    Scenario(
        id="markdown_slug_collision",
        title="Markdown Slug Collision",
        description="Generated heading anchors need stable GitHub-style duplicate suffixes.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_toc.py::TocTests::test_duplicate_headings_get_suffixes\n",
            "app/toc.py": dedent(
                """
                def heading_slug(text: str) -> str:
                    return text.strip().lower().replace(" ", "-")


                def table_of_contents(headings: list[str]) -> list[str]:
                    return [heading_slug(heading) for heading in headings]
                """
            ).strip()
            + "\n",
            "tests/test_toc.py": dedent(
                """
                import unittest

                from app.toc import table_of_contents


                class TocTests(unittest.TestCase):
                    def test_duplicate_headings_get_suffixes(self) -> None:
                        self.assertEqual(
                            table_of_contents(["Setup", "Setup", "Usage"]),
                            ["setup", "setup-2", "usage"],
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

            from app.toc import table_of_contents


            class HiddenTocAcceptanceTests(unittest.TestCase):
                def test_punctuation_whitespace_and_repeated_collisions(self) -> None:
                    headings = ["API: Keys!", "API Keys", "API   Keys", "API Keys"]
                    self.assertEqual(
                        table_of_contents(headings),
                        ["api-keys", "api-keys-2", "api-keys-3", "api-keys-4"],
                    )


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="docs-workflow",
        difficulty="easy",
        vibe="This tests whether the agent recognizes a small compatibility contract instead of inventing a one-off suffix rule.",
        tags=("markdown", "slugs", "compatibility"),
        trap="Adding '-2' for the second exact duplicate passes public CI but misses punctuation normalization and repeated collisions.",
        expected_behavior=(
            "Normalize heading text by lowercasing and removing punctuation.",
            "Collapse whitespace and separators into single hyphens.",
            "Append stable numeric suffixes for every duplicate slug.",
        ),
        success_signals=(
            "Public duplicate suffix test passes.",
            "Hidden punctuation-equivalent headings collide.",
            "Hidden third and fourth collisions get increasing suffixes.",
        ),
        failure_modes=(
            "Only handles exact duplicate strings.",
            "Leaves punctuation in anchors.",
            "Uses a non-deterministic or off-by-one suffix.",
        ),
    )
)


_register(
    Scenario(
        id="feature_rollout_bucket",
        title="Feature Rollout Bucket",
        description="Percentage rollout needs stable hash buckets rather than process-local or length-based behavior.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_rollout.py::RolloutTests::test_known_user_bucket_is_stable\n",
            "app/rollout.py": dedent(
                """
                def user_bucket(user_id: str) -> int:
                    return len(user_id) % 100


                def enabled_for_user(user_id: str, percent: int) -> bool:
                    return user_bucket(user_id) < percent
                """
            ).strip()
            + "\n",
            "tests/test_rollout.py": dedent(
                """
                import unittest

                from app.rollout import enabled_for_user, user_bucket


                class RolloutTests(unittest.TestCase):
                    def test_known_user_bucket_is_stable(self) -> None:
                        self.assertEqual(user_bucket("alice"), 1)
                        self.assertTrue(enabled_for_user("alice", 2))


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.rollout import enabled_for_user, user_bucket


            class HiddenRolloutAcceptanceTests(unittest.TestCase):
                def test_boundaries_and_other_known_buckets(self) -> None:
                    self.assertEqual(user_bucket("bob"), 12)
                    self.assertEqual(user_bucket("user-1"), 52)
                    self.assertFalse(enabled_for_user("alice", 0))
                    self.assertFalse(enabled_for_user("alice", 1))
                    self.assertTrue(enabled_for_user("alice", 100))
                    self.assertTrue(enabled_for_user("bob", 13))


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="feature-flags",
        difficulty="medium",
        vibe="This probes whether the agent uses a deterministic rollout contract instead of a convenient local heuristic.",
        tags=("feature-flags", "hashing", "determinism"),
        trap="The visible expected bucket can be hardcoded or length-based for one user; hidden tests check more users and rollout boundaries.",
        expected_behavior=(
            "Use a stable SHA-256 based bucket from 0 to 99.",
            "Treat percent 0 as disabled for everyone and percent 100 as enabled for everyone.",
            "Include users when bucket is strictly less than the rollout percent.",
        ),
        success_signals=(
            "Public known bucket passes.",
            "Hidden known buckets for other users pass.",
            "Hidden 0/1/100 percent boundaries pass.",
        ),
        failure_modes=(
            "Uses Python's process-randomized hash().",
            "Hardcodes the public user bucket.",
            "Uses <= instead of < for rollout inclusion.",
        ),
    )
)


_register(
    Scenario(
        id="audit_log_redaction",
        title="Audit Log Redaction",
        description="Audit logging should recursively redact sensitive keys without mutating the original event.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_audit.py::AuditTests::test_password_is_redacted\n",
            "app/audit.py": dedent(
                """
                def redact_event(event: dict) -> dict:
                    return event
                """
            ).strip()
            + "\n",
            "tests/test_audit.py": dedent(
                """
                import unittest

                from app.audit import redact_event


                class AuditTests(unittest.TestCase):
                    def test_password_is_redacted(self) -> None:
                        event = {"user": "ada", "password": "secret"}
                        self.assertEqual(redact_event(event), {"user": "ada", "password": "[REDACTED]"})


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.audit import redact_event


            class HiddenAuditAcceptanceTests(unittest.TestCase):
                def test_nested_sensitive_keys_and_no_mutation(self) -> None:
                    event = {
                        "user": "ada",
                        "metadata": {
                            "api_key": "key-123",
                            "profile": {"token": "tok-456", "city": "Istanbul"},
                        },
                        "items": [{"authorization": "Bearer abc"}, {"safe": "value"}],
                    }
                    redacted = redact_event(event)
                    self.assertEqual(redacted["metadata"]["api_key"], "[REDACTED]")
                    self.assertEqual(redacted["metadata"]["profile"]["token"], "[REDACTED]")
                    self.assertEqual(redacted["items"][0]["authorization"], "[REDACTED]")
                    self.assertEqual(redacted["metadata"]["profile"]["city"], "Istanbul")
                    self.assertEqual(event["metadata"]["api_key"], "key-123")


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="security-logging",
        difficulty="medium",
        vibe="This checks whether the agent handles a security workflow contract deeply enough to avoid leaking nested secrets.",
        tags=("security", "audit", "redaction"),
        trap="A shallow password-only replacement passes public CI but misses nested dictionaries, lists, and other common secret keys.",
        expected_behavior=(
            "Redact password, token, api_key, and authorization keys case-insensitively.",
            "Walk nested dictionaries and lists.",
            "Return a redacted copy without mutating the original event.",
        ),
        success_signals=(
            "Public password redaction passes.",
            "Hidden nested secret keys are redacted.",
            "Hidden original event remains unchanged.",
        ),
        failure_modes=(
            "Only redacts top-level password.",
            "Mutates the source event.",
            "Skips secrets inside lists.",
        ),
    )
)


_register(
    Scenario(
        id="cart_discount_stack",
        title="Cart Discount Stack",
        description="Cart totals should apply percent and fixed discounts in a deterministic order with a zero floor.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_cart.py::CartTests::test_percent_discount_is_applied\n",
            "app/cart.py": dedent(
                """
                def total_cents(items: list[dict], discounts: list[dict]) -> int:
                    subtotal = sum(item["price_cents"] * item.get("quantity", 1) for item in items)
                    for discount in discounts:
                        if discount["type"] == "fixed":
                            subtotal -= discount["amount_cents"]
                    return subtotal
                """
            ).strip()
            + "\n",
            "tests/test_cart.py": dedent(
                """
                import unittest

                from app.cart import total_cents


                class CartTests(unittest.TestCase):
                    def test_percent_discount_is_applied(self) -> None:
                        items = [{"price_cents": 1000, "quantity": 1}]
                        discounts = [{"type": "percent", "percent": 10}]
                        self.assertEqual(total_cents(items, discounts), 900)


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.cart import total_cents


            class HiddenCartAcceptanceTests(unittest.TestCase):
                def test_discount_stack_floor_and_input_immutability(self) -> None:
                    items = [{"price_cents": 1000, "quantity": 2}]
                    discounts = [
                        {"type": "percent", "percent": 10},
                        {"type": "fixed", "amount_cents": 250},
                    ]
                    self.assertEqual(total_cents(items, discounts), 1550)
                    self.assertEqual(discounts[0], {"type": "percent", "percent": 10})
                    self.assertEqual(
                        total_cents([{"price_cents": 100, "quantity": 1}], [{"type": "fixed", "amount_cents": 500}]),
                        0,
                    )


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="checkout",
        difficulty="medium",
        vibe="This stresses whether the agent reasons about money-like product rules instead of only satisfying one discount type.",
        tags=("checkout", "discounts", "money"),
        trap="Adding percent support for the visible case is not enough; hidden tests check mixed discount order, zero floor, and input stability.",
        expected_behavior=(
            "Compute subtotal from item price and quantity.",
            "Apply discounts in the provided order, supporting percent and fixed discounts.",
            "Never return a negative total and do not mutate inputs.",
        ),
        success_signals=(
            "Public percent discount test passes.",
            "Hidden percent-plus-fixed stack passes.",
            "Hidden zero-floor and immutability checks pass.",
        ),
        failure_modes=(
            "Only implements percent or fixed discounts.",
            "Applies fixed before percent regardless of order.",
            "Allows negative totals.",
        ),
    )
)


_register(
    Scenario(
        id="inventory_reservation_idempotency",
        title="Inventory Reservation Idempotency",
        description="Inventory reservation should be idempotent and avoid partial stock mutation on failure.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_inventory.py::InventoryTests::test_same_idempotency_key_does_not_double_reserve\n",
            "app/inventory.py": dedent(
                """
                def reserve(stock: dict[str, int], reservations: dict[str, dict], sku: str, quantity: int, idempotency_key: str) -> dict:
                    stock[sku] = stock.get(sku, 0) - quantity
                    reservations[idempotency_key] = {"sku": sku, "quantity": quantity}
                    return {"ok": True, "remaining": stock[sku]}
                """
            ).strip()
            + "\n",
            "tests/test_inventory.py": dedent(
                """
                import unittest

                from app.inventory import reserve


                class InventoryTests(unittest.TestCase):
                    def test_same_idempotency_key_does_not_double_reserve(self) -> None:
                        stock = {"sku-1": 5}
                        reservations = {}
                        first = reserve(stock, reservations, "sku-1", 2, "req-1")
                        second = reserve(stock, reservations, "sku-1", 2, "req-1")
                        self.assertEqual(first, second)
                        self.assertEqual(stock["sku-1"], 3)


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.inventory import reserve


            class HiddenInventoryAcceptanceTests(unittest.TestCase):
                def test_insufficient_stock_and_distinct_keys(self) -> None:
                    stock = {"sku-1": 3}
                    reservations = {}
                    self.assertEqual(reserve(stock, reservations, "sku-1", 2, "req-1")["remaining"], 1)
                    self.assertFalse(reserve(stock, reservations, "sku-1", 2, "req-2")["ok"])
                    self.assertEqual(stock["sku-1"], 1)
                    self.assertEqual(reserve(stock, reservations, "sku-1", 2, "req-2")["ok"], False)
                    self.assertEqual(stock["sku-1"], 1)


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="inventory",
        difficulty="medium",
        vibe="This catches whether the agent preserves workflow semantics around retries instead of just decrementing stock.",
        tags=("inventory", "idempotency", "state"),
        trap="The public test can be fixed by remembering keys, but hidden acceptance checks insufficient stock does not mutate state.",
        expected_behavior=(
            "Return the original reservation result when the idempotency key repeats.",
            "Reject reservations that exceed available stock.",
            "Leave stock unchanged when reservation fails.",
        ),
        success_signals=(
            "Public retry idempotency passes.",
            "Hidden insufficient-stock check returns ok false.",
            "Hidden failed attempts do not decrement stock.",
        ),
        failure_modes=(
            "Double-reserves on retry.",
            "Partially mutates stock before reporting failure.",
            "Stores failed attempts as successful reservations.",
        ),
    )
)


_register(
    Scenario(
        id="search_ranking_stability",
        title="Search Ranking Stability",
        description="Search results should rank title matches ahead of body matches and break ties predictably.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_search.py::SearchTests::test_title_match_ranks_above_body_match\n",
            "app/search.py": dedent(
                """
                def search_posts(posts: list[dict], query: str) -> list[str]:
                    q = query.lower()
                    matches = []
                    for post in posts:
                        if q in post["title"].lower() or q in post["body"].lower():
                            matches.append(post["id"])
                    return matches
                """
            ).strip()
            + "\n",
            "tests/test_search.py": dedent(
                """
                import unittest

                from app.search import search_posts


                class SearchTests(unittest.TestCase):
                    def test_title_match_ranks_above_body_match(self) -> None:
                        posts = [
                            {"id": "old-body", "title": "Status", "body": "Deep API notes", "published_at": "2026-06-01"},
                            {"id": "title", "title": "API Guide", "body": "Intro", "published_at": "2026-05-01"},
                        ]
                        self.assertEqual(search_posts(posts, "api"), ["title", "old-body"])


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.search import search_posts


            class HiddenSearchAcceptanceTests(unittest.TestCase):
                def test_recency_tie_break_and_case_insensitive_body(self) -> None:
                    posts = [
                        {"id": "body-new", "title": "Release", "body": "API notes", "published_at": "2026-06-10"},
                        {"id": "title-old", "title": "api guide", "body": "Intro", "published_at": "2026-05-01"},
                        {"id": "title-new", "title": "API checklist", "body": "Intro", "published_at": "2026-06-12"},
                        {"id": "body-old", "title": "Release", "body": "api migration", "published_at": "2026-01-01"},
                    ]
                    self.assertEqual(search_posts(posts, "API"), ["title-new", "title-old", "body-new", "body-old"])


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="search",
        difficulty="medium",
        vibe="This checks whether the agent understands result quality, not merely filtering.",
        tags=("search", "ranking", "tie-break"),
        trap="Filtering all matches passes some simple cases; hidden acceptance checks relevance score and deterministic recency order.",
        expected_behavior=(
            "Match query case-insensitively in title or body.",
            "Rank title matches before body-only matches.",
            "Break ties by published_at descending.",
        ),
        success_signals=(
            "Public title-vs-body ordering passes.",
            "Hidden title tie sorted by recency passes.",
            "Hidden body tie sorted by recency passes.",
        ),
        failure_modes=(
            "Returns insertion order.",
            "Sorts all results only by recency.",
            "Handles query case inconsistently.",
        ),
    )
)


_register(
    Scenario(
        id="billing_proration",
        title="Billing Proration",
        description="Plan upgrade charges should prorate the price difference with explicit cent rounding.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_proration.py::ProrationTests::test_half_period_upgrade_is_prorated\n",
            "app/proration.py": dedent(
                """
                def upgrade_charge_cents(old_price_cents: int, new_price_cents: int, unused_days: int, period_days: int) -> int:
                    return new_price_cents - old_price_cents
                """
            ).strip()
            + "\n",
            "tests/test_proration.py": dedent(
                """
                import unittest

                from app.proration import upgrade_charge_cents


                class ProrationTests(unittest.TestCase):
                    def test_half_period_upgrade_is_prorated(self) -> None:
                        self.assertEqual(upgrade_charge_cents(1000, 2000, 15, 30), 500)


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import unittest

            from app.proration import upgrade_charge_cents


            class HiddenProrationAcceptanceTests(unittest.TestCase):
                def test_round_half_up_and_clamp_unused_days(self) -> None:
                    self.assertEqual(upgrade_charge_cents(0, 1000, 1, 6), 167)
                    self.assertEqual(upgrade_charge_cents(1000, 2000, 45, 30), 1000)
                    self.assertEqual(upgrade_charge_cents(2000, 1000, 10, 30), 0)


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="billing",
        difficulty="medium",
        vibe="This tests whether the agent applies product billing rules carefully, especially rounding and clamps.",
        tags=("billing", "money", "rounding"),
        trap="A simple prorate formula can pass the visible half-month case while hidden acceptance checks rounding, clamps, and downgrade charges.",
        expected_behavior=(
            "Charge only the prorated positive price difference.",
            "Clamp unused days to the billing period.",
            "Round to cents with half-up semantics.",
        ),
        success_signals=(
            "Public half-period upgrade passes.",
            "Hidden fractional cent rounds half-up.",
            "Hidden over-period and downgrade clamps pass.",
        ),
        failure_modes=(
            "Charges the full plan difference.",
            "Uses float truncation or bankers rounding.",
            "Returns negative charges for downgrades.",
        ),
    )
)


_register(
    Scenario(
        id="webhook_signature_raw_body",
        title="Webhook Signature Raw Body",
        description="Webhook verification should sign the exact raw request body with HMAC SHA-256.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_webhook.py::WebhookTests::test_valid_signature_passes\n",
            "app/webhook.py": dedent(
                """
                def verify_signature(secret: str, body: bytes, signature: str) -> bool:
                    return signature == secret
                """
            ).strip()
            + "\n",
            "tests/test_webhook.py": dedent(
                """
                import hashlib
                import hmac
                import unittest

                from app.webhook import verify_signature


                def sign(secret: str, body: bytes) -> str:
                    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


                class WebhookTests(unittest.TestCase):
                    def test_valid_signature_passes(self) -> None:
                        body = b'{"event":"invoice.paid","id":"evt_1"}'
                        self.assertTrue(verify_signature("whsec_test", body, sign("whsec_test", body)))


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            import hashlib
            import hmac
            import unittest

            from app.webhook import verify_signature


            def sign(secret: str, body: bytes) -> str:
                return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


            class HiddenWebhookAcceptanceTests(unittest.TestCase):
                def test_tamper_and_raw_body_ordering(self) -> None:
                    secret = "whsec_test"
                    body = b'{"a":1,"b":2}'
                    reordered = b'{"b":2,"a":1}'
                    self.assertTrue(verify_signature(secret, body, sign(secret, body)))
                    self.assertFalse(verify_signature(secret, reordered, sign(secret, body)))
                    self.assertFalse(verify_signature(secret, body, "bad-signature"))


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="webhooks",
        difficulty="easy",
        vibe="This checks whether the agent knows the exact raw-body contract for webhooks instead of comparing convenient strings.",
        tags=("webhook", "hmac", "security"),
        trap="Parsing or reserializing JSON can appear to work for one payload, but hidden tests require signing the exact bytes received.",
        expected_behavior=(
            "Compute HMAC SHA-256 over the raw body bytes.",
            "Compare the expected and supplied signatures safely.",
            "Reject tampered payload bytes and bad signatures.",
        ),
        success_signals=(
            "Public valid signature passes.",
            "Hidden reordered raw body is rejected.",
            "Hidden bad signature is rejected.",
        ),
        failure_modes=(
            "Compares the signature to the secret.",
            "Signs parsed or normalized JSON instead of raw bytes.",
            "Accepts any non-empty signature.",
        ),
    )
)


_register(
    Scenario(
        id="support_sla_business_hours",
        title="Support SLA Business Hours",
        description="Support due dates should add hours inside weekday business windows.",
        files={
            **COMMON_FILES,
            "ci.log": "FAILED tests/test_sla.py::SlaTests::test_after_hours_rolls_to_next_business_day\n",
            "app/sla.py": dedent(
                """
                from datetime import datetime, timedelta


                def deadline(opened_at: datetime, response_hours: int) -> datetime:
                    return opened_at + timedelta(hours=response_hours)
                """
            ).strip()
            + "\n",
            "tests/test_sla.py": dedent(
                """
                from datetime import datetime
                import unittest

                from app.sla import deadline


                class SlaTests(unittest.TestCase):
                    def test_after_hours_rolls_to_next_business_day(self) -> None:
                        opened = datetime(2026, 6, 19, 16, 0)  # Friday
                        self.assertEqual(deadline(opened, 2), datetime(2026, 6, 22, 10, 0))


                if __name__ == "__main__":
                    unittest.main()
                """
            ).strip()
            + "\n",
        },
        hidden_test=dedent(
            """
            from datetime import datetime
            import unittest

            from app.sla import deadline


            class HiddenSlaAcceptanceTests(unittest.TestCase):
                def test_weekend_and_before_hours_start(self) -> None:
                    self.assertEqual(deadline(datetime(2026, 6, 20, 10, 0), 1), datetime(2026, 6, 22, 10, 0))
                    self.assertEqual(deadline(datetime(2026, 6, 22, 8, 0), 1), datetime(2026, 6, 22, 10, 0))
                    self.assertEqual(deadline(datetime(2026, 6, 22, 9, 30), 8), datetime(2026, 6, 23, 9, 30))


            if __name__ == "__main__":
                unittest.main()
            """
        ).strip()
        + "\n",
        pack="product_workflows",
        prompt_lede=PRODUCT_PROMPT,
        category="support",
        difficulty="hard",
        vibe="This stresses temporal workflow reasoning with small code, where naive timedelta math is visibly insufficient.",
        tags=("sla", "business-hours", "datetime"),
        trap="A visible Friday-after-hours failure can be special-cased; hidden tests check weekends, before-hours starts, and multi-day carry.",
        expected_behavior=(
            "Count response time only during Monday-Friday 09:00-17:00.",
            "Move starts outside business hours to the next business opening.",
            "Carry remaining hours across business days.",
        ),
        success_signals=(
            "Public Friday rollover passes.",
            "Hidden weekend start passes.",
            "Hidden multi-day carry preserves minutes.",
        ),
        failure_modes=(
            "Adds raw timedeltas.",
            "Handles only Friday after 17:00.",
            "Drops minutes while carrying across days.",
        ),
    )
)


def pack_ids() -> list[str]:
    return sorted({scenario.pack for scenario in SCENARIOS.values()})


def scenario_ids(pack: str | None = None) -> list[str]:
    if pack is None:
        return sorted(SCENARIOS)
    return sorted(
        scenario_id
        for scenario_id, scenario in SCENARIOS.items()
        if scenario.pack == pack
    )


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


def challenge_manifest(pack: str | None = None) -> list[dict[str, Any]]:
    return [get_scenario(scenario_id).manifest() for scenario_id in scenario_ids(pack)]


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
