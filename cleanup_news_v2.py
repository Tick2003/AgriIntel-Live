import sqlite3

DB_NAME = "agri_intel.db"

def cleanup():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Use rowid since ID might be missing or not auto-increment in old schema
    c.execute('''
        DELETE FROM news_alerts 
        WHERE rowid NOT IN (
            SELECT min(rowid) 
            FROM news_alerts 
            GROUP BY title
        )
    ''')
    print(f"Cleanup complete. Rows affected: {c.rowcount}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    cleanup()
