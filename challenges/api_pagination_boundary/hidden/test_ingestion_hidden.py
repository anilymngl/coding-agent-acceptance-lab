import unittest

from app.ingestion import MockApiClient, fetch_all_records


class HiddenIngestionAcceptanceTests(unittest.TestCase):
    def test_fetches_exact_page_boundary(self) -> None:
        mock_data = [{"id": i} for i in range(20)]
        client = MockApiClient(mock_data)
        results = fetch_all_records(client)
        self.assertEqual(len(results), 20)

    def test_fetches_empty_api(self) -> None:
        client = MockApiClient([])
        results = fetch_all_records(client)
        self.assertEqual(len(results), 0)

    def test_fetches_large_odd_number(self) -> None:
        mock_data = [{"id": i} for i in range(103)]
        client = MockApiClient(mock_data)
        results = fetch_all_records(client)
        self.assertEqual(len(results), 103)


if __name__ == "__main__":
    unittest.main()
