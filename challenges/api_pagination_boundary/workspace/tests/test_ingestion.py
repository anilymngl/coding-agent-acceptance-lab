import unittest

from app.ingestion import MockApiClient, fetch_all_records


class IngestionTests(unittest.TestCase):
    def test_fetches_all_twenty_five_records(self) -> None:
        mock_data = [{"id": i} for i in range(25)]
        client = MockApiClient(mock_data)
        
        results = fetch_all_records(client)
        
        self.assertEqual(len(results), 25)


if __name__ == "__main__":
    unittest.main()
