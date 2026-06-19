import unittest

from app.config import merge_config


class HiddenConfigAcceptanceTests(unittest.TestCase):
    def test_three_level_deep_merge(self) -> None:
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"c": 99}}}
        merged = merge_config(base, override)
        self.assertEqual(merged["a"]["b"]["c"], 99)
        self.assertEqual(merged["a"]["b"]["d"], 2)

    def test_override_adds_new_nested_keys(self) -> None:
        base = {"server": {"host": "localhost"}}
        override = {"server": {"timeout": 30}, "logging": {"level": "INFO"}}
        merged = merge_config(base, override)
        self.assertEqual(merged["server"]["host"], "localhost")
        self.assertEqual(merged["server"]["timeout"], 30)
        self.assertEqual(merged["logging"]["level"], "INFO")

    def test_base_is_not_mutated(self) -> None:
        base = {"a": {"x": 1}}
        override = {"a": {"y": 2}}
        merge_config(base, override)
        self.assertNotIn("y", base["a"])


if __name__ == "__main__":
    unittest.main()
