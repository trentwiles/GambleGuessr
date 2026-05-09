import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "db.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS duels_ranking_poll (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rating INTEGER NOT NULL,
                type TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )


def insert_duels_rating(rating: int, type: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO duels_ranking_poll (rating, type) VALUES (?, ?);",
            (rating, type),
        )
        return cur.lastrowid


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
