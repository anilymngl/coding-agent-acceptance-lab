import sqlite3


def setup_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (id INTEGER)")
    db.execute("CREATE TABLE orders (id INTEGER, user_id INTEGER, amount INTEGER)")
    db.execute("CREATE TABLE ad_clicks (id INTEGER, user_id INTEGER, clicks INTEGER)")
    return db


def get_user_profiles(db: sqlite3.Connection) -> list[dict]:
    query = """
        SELECT 
            u.id as user_id,
            COALESCE(SUM(o.amount), 0) as total_spend,
            COALESCE(SUM(c.clicks), 0) as total_clicks
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        LEFT JOIN ad_clicks c ON u.id = c.user_id
        GROUP BY u.id
    """
    db.row_factory = sqlite3.Row
    return [dict(row) for row in db.execute(query)]
