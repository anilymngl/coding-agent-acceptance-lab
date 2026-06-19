import unittest

from app.attribution import get_sales_by_region, setup_db


class HiddenAttributionAcceptanceTests(unittest.TestCase):
    def test_complex_movements_with_multiple_users(self) -> None:
        db = setup_db()
        
        # User 1 moves North -> South
        db.execute("INSERT INTO users VALUES (1, 'Bob')")
        db.execute("INSERT INTO user_regions VALUES (1, 'North', '2024-01-01', '2024-03-31')")
        db.execute("INSERT INTO user_regions VALUES (1, 'South', '2024-04-01', '2024-12-31')")
        
        # User 2 stays in North
        db.execute("INSERT INTO users VALUES (2, 'Charlie')")
        db.execute("INSERT INTO user_regions VALUES (2, 'North', '2024-01-01', '2024-12-31')")
        
        # Orders for User 1
        db.execute("INSERT INTO orders VALUES (1, 1, 10, '2024-02-15')") # North
        db.execute("INSERT INTO orders VALUES (2, 1, 20, '2024-05-10')") # South
        db.execute("INSERT INTO orders VALUES (3, 1, 30, '2024-11-20')") # South
        
        # Orders for User 2
        db.execute("INSERT INTO orders VALUES (4, 2, 50, '2024-06-15')") # North
        db.execute("INSERT INTO orders VALUES (5, 2, 50, '2024-09-01')") # North
        
        results = {row["region"]: row["total_sales"] for row in get_sales_by_region(db)}
        
        # North = 10 (Bob) + 100 (Charlie) = 110
        # South = 50 (Bob)
        self.assertEqual(results.get("North", 0), 110)
        self.assertEqual(results.get("South", 0), 50)


if __name__ == "__main__":
    unittest.main()
