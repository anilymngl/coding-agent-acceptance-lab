import unittest

from app.attribution import get_sales_by_region, setup_db


class AttributionTests(unittest.TestCase):
    def test_orders_attributed_to_historical_region(self) -> None:
        db = setup_db()
        db.execute("INSERT INTO users VALUES (1, 'Alice')")
        
        # Alice lived in East for the first half of the year
        db.execute("INSERT INTO user_regions VALUES (1, 'East', '2024-01-01', '2024-06-30')")
        
        # Alice moved to West for the second half
        db.execute("INSERT INTO user_regions VALUES (1, 'West', '2024-07-01', '2024-12-31')")
        
        # Order 1: March (should go to East)
        db.execute("INSERT INTO orders VALUES (1, 1, 100, '2024-03-15')")
        
        # Order 2: August (should go to West)
        db.execute("INSERT INTO orders VALUES (2, 1, 50, '2024-08-10')")
        
        results = {row["region"]: row["total_sales"] for row in get_sales_by_region(db)}
        
        self.assertEqual(results.get("East", 0), 100)
        self.assertEqual(results.get("West", 0), 50)


if __name__ == "__main__":
    unittest.main()
