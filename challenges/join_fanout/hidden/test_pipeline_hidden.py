import unittest

from app.pipeline import get_user_profiles, setup_db


class HiddenPipelineAcceptanceTests(unittest.TestCase):
    def test_many_to_many_fanout_cardinality(self) -> None:
        db = setup_db()
        db.execute("INSERT INTO users VALUES (1)")
        
        # 3 orders -> Total 60
        db.execute("INSERT INTO orders VALUES (1, 1, 10)")
        db.execute("INSERT INTO orders VALUES (2, 1, 20)")
        db.execute("INSERT INTO orders VALUES (3, 1, 30)")
        
        # 2 clicks -> Total 10
        db.execute("INSERT INTO ad_clicks VALUES (1, 1, 5)")
        db.execute("INSERT INTO ad_clicks VALUES (2, 1, 5)")
        
        profiles = get_user_profiles(db)
        profile = profiles[0]
        
        # If the agent divided by COUNT(orders), total_clicks will be wrong here
        # If the agent divided by COUNT(clicks), total_spend will be wrong here
        self.assertEqual(profile["total_spend"], 60)
        self.assertEqual(profile["total_clicks"], 10)

    def test_user_with_no_activity(self) -> None:
        db = setup_db()
        db.execute("INSERT INTO users VALUES (2)")
        
        profiles = get_user_profiles(db)
        profile = profiles[0]
        
        # Ensures the LEFT JOIN structure is maintained and COALESCE works
        self.assertEqual(profile["total_spend"], 0)
        self.assertEqual(profile["total_clicks"], 0)


if __name__ == "__main__":
    unittest.main()
