import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_NAME = "agri_intel.db"
# v1.1 - Force Update

def init_db():
    """Initialize the database with necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Table: Market Prices
    c.execute('''
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            commodity TEXT,
            mandi TEXT,
            price_min REAL,
            price_max REAL,
            price_modal REAL,
            arrival REAL,
            unit TEXT DEFAULT 'Rs/Quintal'
        )
    ''')
    
    # Table: News/Alerts
    c.execute('''
        CREATE TABLE IF NOT EXISTS news_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            title TEXT,
            source TEXT,
            url TEXT,
            sentiment TEXT
        )
    ''')

    # Table: Weather Logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            region TEXT,
            temperature REAL,
            rainfall REAL,
            condition TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # Table: Signal Logs (New Phase 3)
    c.execute('''
        CREATE TABLE IF NOT EXISTS signal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            commodity TEXT,
            mandi TEXT,
            signal TEXT,
            price_at_signal REAL,
            price_after_7d REAL,
            profitability_status TEXT
        )
    ''') 
    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized.")

def save_prices(df):
    """Save a pandas DataFrame of prices to the DB."""
    conn = sqlite3.connect(DB_NAME)
    # Ensure columns match
    # Expected DF cols: ['date', 'commodity', 'mandi', 'price_min', 'price_max', 'price_modal', 'arrival']
    df.to_sql('market_prices', conn, if_exists='append', index=False)
    conn.close()
    print(f"Saved {len(df)} price records.")

def get_latest_prices(commodity=None):
    """Retrieve prices from the DB."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM market_prices"
    if commodity:
        query += f" WHERE commodity = '{commodity}'"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def save_news(df):
    """Save news to DB, avoiding duplicates."""
    if df.empty:
        return

    conn = sqlite3.connect(DB_NAME)
    
    # 1. Get existing titles
    try:
        existing_titles = pd.read_sql("SELECT title FROM news_alerts", conn)['title'].tolist()
        existing_titles = set(existing_titles)
    except Exception:
        existing_titles = set()

    # 2. Filter new items
    if 'title' in df.columns:
        # Deduplicate input df first
        df = df.drop_duplicates(subset=['title'])
        # Filter against DB
        new_df = df[~df['title'].isin(existing_titles)]
        
        if not new_df.empty:
            new_df.to_sql('news_alerts', conn, if_exists='append', index=False)
            print(f"Added {len(new_df)} new news items.")
        else:
            print("No new unique news items found.")
            
    conn.close()

def get_latest_news():
    """Get latest news."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM news_alerts ORDER BY date DESC LIMIT 20", conn)
    conn.close()
    return df

def save_weather(df):
    """Save weather logs."""
    conn = sqlite3.connect(DB_NAME)
    df.to_sql('weather_logs', conn, if_exists='append', index=False)
    conn.close()

def get_weather_logs(region=None):
    """Get weather logs."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM weather_logs"
    if region:
        query += f" WHERE region = '{region}'"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_last_update():
    """Retrieve the last update timestamp from app_metadata."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("SELECT value FROM app_metadata WHERE key = 'last_update'")
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception:
        conn.close()
        return None

def set_last_update():
    """Set the last update timestamp in app_metadata to the current time."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO app_metadata (key, value) VALUES ('last_update', ?)", (now_str,))
    conn.commit()
    conn.close()

def get_unique_items(column):
    """Get distinct values for a column (commodity/mandi)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT {column} FROM market_prices ORDER BY {column}")
    items = [row[0] for row in cursor.fetchall()]
    conn.close()
    return items

# --- SIGNAL TRACKING (Phase 3) ---
def log_signal(date, commodity, mandi, signal, price_at_signal):
    """Logs a decision signal."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if exists for this date/commodity/mandi
    c.execute("SELECT id FROM signal_logs WHERE date=? AND commodity=? AND mandi=?", (date, commodity, mandi))
    if c.fetchone():
        conn.close()
        return # Already logged
        
    c.execute('''
        INSERT INTO signal_logs (date, commodity, mandi, signal, price_at_signal, price_after_7d, profitability_status)
        VALUES (?, ?, ?, ?, ?, NULL, NULL)
    ''', (date, commodity, mandi, signal, price_at_signal))
    conn.commit()
    conn.close()

def get_signal_stats(commodity, mandi):
    """
    Retrieves stats for 'Win Rate'. 
    Logic: 
    - Updates any NULL price_after_7d if data now exists.
    - Calculates profitability.
    """
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Update pending logs
    # Find logs > 7 days old with no outcome
    pending_df = pd.read_sql("SELECT * FROM signal_logs WHERE price_after_7d IS NULL", conn)
    
    if not pending_df.empty:
        c = conn.cursor()
        prices_df = pd.read_sql(f"SELECT date, price_modal FROM market_prices WHERE commodity='{commodity}' AND mandi='{mandi}'", conn)
        # Fix date parsing if stored as mixed format, assume YYYY-MM-DD
        prices_df['date'] = pd.to_datetime(prices_df['date'], errors='coerce')
        
        for _, row in pending_df.iterrows():
            try:
                signal_date = pd.to_datetime(row['date'])
                if pd.isna(signal_date): continue
                
                target_date = signal_date + timedelta(days=7)
                
                # Use nearest date match if exact date missing (robustness)
                # Find price on target date
                outcome_row = prices_df[prices_df['date'] >= target_date].sort_values('date').head(1)
                
                if not outcome_row.empty:
                    outcome_price = outcome_row['price_modal'].iloc[0]
                    price_now = row['price_at_signal']
                    signal = row['signal']
                    
                    status = "Neutral"
                    if signal == "SELL NOW":
                        if outcome_price < price_now: status = "Profitable"
                        else: status = "Loss"
                    elif (signal == "HOLD" or signal == "ACCUMULATE"):
                        if outcome_price > price_now: status = "Profitable"
                        else: status = "Loss"
                    elif signal == "WAIT / RISKY":
                        status = "N/A" # Neutral
                    else:
                        status = "Neutral"

                    c.execute("UPDATE signal_logs SET price_after_7d=?, profitability_status=? WHERE id=?", 
                              (outcome_price, status, row['id']))
            except Exception as e:
                print(f"Error processing log {row['id']}: {e}")
                continue
                
        conn.commit()

    # 2. Calculate Stats
    df = pd.read_sql(f"SELECT * FROM signal_logs WHERE commodity='{commodity}' AND mandi='{mandi}' AND profitability_status IS NOT NULL", conn)
    conn.close()
    
    if df.empty:
        return {"total": 0, "win_rate": 0, "profitable": 0}
        
    total = len(df[df['profitability_status'] != 'N/A'])
    profitable = len(df[df['profitability_status'] == 'Profitable'])
    
    win_rate = (profitable / total * 100) if total > 0 else 0
    
    return {
        "total": total,
        "win_rate": win_rate,
        "profitable": profitable
    }

if __name__ == "__main__":
    init_db()
