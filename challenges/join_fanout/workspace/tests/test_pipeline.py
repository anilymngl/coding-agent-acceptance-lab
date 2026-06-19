import unittest

from app.pipeline import get_user_profiles, setup_db


class PipelineTests(unittest.TestCase):
    def test_profile_metrics(self) -> None:
        db = setup_db()
        db.execute("INSERT INTO users VALUES (1)")
        
        # User 1 has 2 orders totaling 150
        db.execute("INSERT INTO orders VALUES (1, 1, 100)")
        db.execute("INSERT INTO orders VALUES (2, 1, 50)")
        
        # User 1 has 1 click record totaling 5 clicks
        db.execute("INSERT INTO ad_clicks VALUES (1, 1, 5)")
        
        profiles = get_user_profiles(db)
        self.assertEqual(len(profiles), 1)
        profile = profiles[0]
        
        self.assertEqual(profile["total_spend"], 150)
        self.assertEqual(profile["total_clicks"], 5)  # Fails here: returns 10


if __name__ == "__main__":
    unittest.main()
