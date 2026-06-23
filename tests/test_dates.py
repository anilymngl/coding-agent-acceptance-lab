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