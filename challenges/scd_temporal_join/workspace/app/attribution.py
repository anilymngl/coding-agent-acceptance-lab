import sqlite3


def setup_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    db.execute("CREATE TABLE user_regions (user_id INTEGER, region TEXT, valid_from DATE, valid_to DATE)")
    db.execute("CREATE TABLE orders (id INTEGER, user_id INTEGER, amount INTEGER, order_date DATE)")
    return db


def get_sales_by_region(db: sqlite3.Connection) -> list[dict]:
    query = """
        SELECT 
            ur.region,
            SUM(o.amount) as total_sales
        FROM orders o
        JOIN user_regions ur ON o.user_id = ur.user_id
        GROUP BY ur.region
        ORDER BY ur.region
    """
    db.row_factory = sqlite3.Row
    return [dict(row) for row in db.execute(query)]
