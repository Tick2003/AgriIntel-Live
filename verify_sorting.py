
import sqlite3
import pandas as pd

def test_sorting():
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.execute("CREATE TABLE news (date TEXT, title TEXT)")
    
    # Insert examples
    examples = [
        ("Wed, 11 Feb 2026 08:00:00 GMT", "Old News (Wednesday)"),
        ("Fri, 14 Feb 2026 08:00:00 GMT", "New News (Friday)")
    ]
    
    c.executemany("INSERT INTO news VALUES (?, ?)", examples)
    conn.commit()
    
    print("--- Query with ORDER BY date DESC ---")
    df = pd.read_sql("SELECT * FROM news ORDER BY date DESC", conn)
    print(df)
    
    if df.iloc[0]['title'] == "Old News (Wednesday)":
        print("\n❌ ISSUE CONFIRMED: 'Wed' sorts before 'Fri' in DESC order.")
    else:
        print("\n✅ Sorting is correct (unexpected).")

if __name__ == "__main__":
    test_sorting()
