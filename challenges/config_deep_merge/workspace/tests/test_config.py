import unittest

from app.config import merge_config


class ConfigTests(unittest.TestCase):
    def test_nested_override_preserves_base_keys(self) -> None:
        base = {
            "database": {"host": "localhost", "port": 5432},
            "debug": False,
        }
        override = {
            "database": {"port": 5433},
        }
        merged = merge_config(base, override)
        self.assertEqual(merged["database"]["host"], "localhost")
        self.assertEqual(merged["database"]["port"], 5433)
        self.assertFalse(merged["debug"])


if __name__ == "__main__":
    unittest.main()
