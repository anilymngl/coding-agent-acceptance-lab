class MockApiClient:
    def __init__(self, records: list[dict]):
        self.records = records
        self.page_size = 10

    def get_page(self, page_number: int) -> list[dict]:
        start = (page_number - 1) * self.page_size
        end = start + self.page_size
        return self.records[start:end]


def fetch_all_records(api_client: MockApiClient) -> list[dict]:
    all_records = []
    page = 1
    while True:
        records = api_client.get_page(page)
        if len(records) < 10:
            break
        all_records.extend(records)
        page += 1
    return all_records
