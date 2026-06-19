import unittest

from app.analytics import compute, dashboard_total


class HiddenAnalyticsAcceptanceTests(unittest.TestCase):
    def test_compute_returns_raw_source_value(self) -> None:
        """compute() is the low-level API -- it must NOT normalize units."""
        self.assertAlmostEqual(compute("ecommerce_revenue"), 7500.0)
        self.assertAlmostEqual(compute("subscription_revenue"), 29.98)
        self.assertAlmostEqual(compute("refund_total"), 1500.0)

    def test_two_cents_metrics_combine_to_dollars(self) -> None:
        """Proves the fix generalizes -- refund_total is also in cents."""
        total = dashboard_total(["ecommerce_revenue", "refund_total"])
        self.assertAlmostEqual(total, 90.00, places=2)

    def test_single_dollar_metric_is_not_double_converted(self) -> None:
        """A dollar metric alone should pass through at face value."""
        total = dashboard_total(["subscription_revenue"])
        self.assertAlmostEqual(total, 29.98, places=2)


if __name__ == "__main__":
    unittest.main()
