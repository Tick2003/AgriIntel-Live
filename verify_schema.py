import sqlite3
import pandas as pd

DB_NAME = "agri_intel.db"

def check_schema():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA table_info(news_alerts)")
    columns = c.fetchall()
    print("Columns:", columns)
    
    # Also check if duplicates exist
    c.execute("SELECT title, count(*) FROM news_alerts GROUP BY title HAVING count(*) > 1")
    dupes = c.fetchall()
    print(f"Duplicate Titless: {len(dupes)}")
    conn.close()

if __name__ == "__main__":
    check_schema()
