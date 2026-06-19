import sqlite3

def setup_db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE records (id INTEGER, name TEXT)")
    return db

def process_batch(db: sqlite3.Connection, batch: list[dict]) -> None:
    """Insert a batch of items into the database."""
    for item in batch:
        db.execute("INSERT INTO records VALUES (?, ?)", (item["id"], item["name"]))
