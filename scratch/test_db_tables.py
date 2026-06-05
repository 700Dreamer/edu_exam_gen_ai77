import asyncio
import os
import sys
import sqlite3

# Set up project path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.models import create_db_and_tables

async def main():
    print("Initializing auth/audit log database tables...")
    await create_db_and_tables()
    print("Tables initialized successfully.")
    
    # Let's inspect the sqlite file to verify
    db_path = os.path.join(BASE_DIR, 'eduquest_history.db')
    print(f"Checking SQLite database file at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Existing database tables:")
    for t in tables:
        print(f" - {t[0]}")
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
