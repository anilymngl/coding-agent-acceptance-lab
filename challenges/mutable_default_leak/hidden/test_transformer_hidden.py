import unittest

from app.transformer import extract_hashtags


class HiddenTransformerAcceptanceTests(unittest.TestCase):
    def test_function_is_stateless_in_loop(self) -> None:
        # Even if the agent cleared the state in the visible test,
        # this will fail if the function itself is still stateful.
        self.assertEqual(extract_hashtags("#one"), ["#one"])
        self.assertEqual(extract_hashtags("#two"), ["#two"])
        self.assertEqual(extract_hashtags("#three"), ["#three"])


if __name__ == "__main__":
    unittest.main()
