import sqlite3
import os

db_path = 'agri_intel.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} does not exist.")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()

print(f"Database: {db_path}")
for (table_name,) in tables:
    count = c.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
    print(f"{table_name}: {count}")

# Check last_update metadata specifically
c.execute("SELECT value FROM app_metadata WHERE key='last_update'")
res = c.fetchone()
print(f"last_update: {res[0] if res else 'MISSING'}")

conn.close()
