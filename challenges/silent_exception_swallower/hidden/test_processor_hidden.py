import unittest

from app.processor import process_batch, setup_db


class HiddenProcessorAcceptanceTests(unittest.TestCase):
    def test_valid_items_after_error_are_processed(self) -> None:
        db = setup_db()
        batch = [
            {"id": 1}, # Malformed
            {"id": 2, "name": "Bob"}, # Valid
            {"id": 3}, # Malformed
            {"id": 4, "name": "Charlie"}, # Valid
        ]
        
        process_batch(db, batch)
        
        count = db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        
        # If the agent wrapped the whole loop in a try/except, 
        # it will break on the first error and process 0 items.
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
