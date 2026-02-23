import sqlite3

DB_NAME = "bot.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_db() as db:
        cursor = db.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            used INTEGER DEFAULT 0,
            sub INTEGER DEFAULT 0,
            active INTEGER DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending (
            owner_msg_id INTEGER PRIMARY KEY,
            user_id INTEGER
        )
        """)

        db.commit()