import unittest

from app.transformer import extract_hashtags


class TransformerTests(unittest.TestCase):
    def test_extract_hashtags_first(self) -> None:
        self.assertEqual(extract_hashtags("hello #world"), ["#world"])
        
    def test_extract_hashtags_second(self) -> None:
        self.assertEqual(extract_hashtags("learning #python"), ["#python"])


if __name__ == "__main__":
    unittest.main()
