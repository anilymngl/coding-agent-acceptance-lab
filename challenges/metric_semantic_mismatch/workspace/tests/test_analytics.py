import unittest

from app.analytics import dashboard_total


class AnalyticsTests(unittest.TestCase):
    def test_combined_revenue_normalizes_to_dollars(self) -> None:
        total = dashboard_total(["ecommerce_revenue", "subscription_revenue"])
        self.assertAlmostEqual(total, 104.98, places=2)


if __name__ == "__main__":
    unittest.main()
