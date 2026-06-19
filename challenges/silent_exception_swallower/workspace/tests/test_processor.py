import unittest

from app.processor import process_batch, setup_db


class ProcessorTests(unittest.TestCase):
    def test_batch_handles_malformed_items(self) -> None:
        db = setup_db()
        batch = [
            {"id": 1, "name": "Alice"},
            {"id": 2}, # Missing 'name', should be skipped gracefully
        ]
        
        # This currently crashes with KeyError
        process_batch(db, batch)


if __name__ == "__main__":
    unittest.main()
