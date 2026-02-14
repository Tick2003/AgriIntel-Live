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
            condition TEXT,
            wind_speed REAL,
            humidity REAL
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
    
    # Table: User Config (New Phase 4)
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_config (
            user_id TEXT PRIMARY KEY,
            risk_tolerance TEXT DEFAULT 'Medium',
            transport_cost REAL DEFAULT 0.0,
            default_mandi TEXT,
            default_commodity TEXT
        )
    ''')
    
    # --- MIGRATIONS ---
    # Check if 'wind_speed' exists in weather_logs (Phase 2 update)
    try:
        c.execute("SELECT wind_speed FROM weather_logs LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating: Adding 'wind_speed' and 'humidity' to weather_logs")
        try:
            c.execute("ALTER TABLE weather_logs ADD COLUMN wind_speed REAL DEFAULT 0.0")
            c.execute("ALTER TABLE weather_logs ADD COLUMN humidity REAL DEFAULT 0.0")
        except Exception as e:
            print(f"Migration warning: {e}")

    # Table: System Logs (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            source TEXT,
            message TEXT,
            metadata TEXT
        )
    ''')

    # Table: Forecast Logs (New Phase 5 - Performance Tracking)
    c.execute('''
        CREATE TABLE IF NOT EXISTS forecast_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gen_date TEXT,
            target_date TEXT,
            commodity TEXT,
            mandi TEXT,
            predicted_price REAL,
            actual_price REAL,
            model_version TEXT DEFAULT 'v1.0'
        )
    ''')

    # Table: Model Metrics (New Phase 5)
    c.execute('''
        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            commodity TEXT,
            mandi TEXT,
            mape REAL,
            rmse REAL,
            signal_accuracy REAL,
            sample_size INTEGER
        )
    ''')

    # Table: Raw Mandi Prices (Staging) - New Phase 6
    c.execute('''
        CREATE TABLE IF NOT EXISTS raw_mandi_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT,
            date TEXT,
            commodity TEXT,
            mandi TEXT,
            price_min REAL,
            price_max REAL,
            price_modal REAL,
            arrival REAL,
            ingestion_timestamp TEXT,
            status TEXT DEFAULT 'PENDING' 
        )
    ''')
    # status: PENDING, VALIDATED, REJECTED

    # Table: Data Quality Logs - New Phase 6
    c.execute('''
        CREATE TABLE IF NOT EXISTS data_quality_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT,
            date TEXT,
            commodity TEXT,
            mandi TEXT,
            issue_type TEXT,
            severity TEXT,
            details TEXT,
            raw_value TEXT
        )
    ''')

    # Table: Scraper Execution Stats - New Phase 6
    c.execute('''
        CREATE TABLE IF NOT EXISTS scraper_execution_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            status TEXT,
            duration_seconds REAL,
            records_fetched INTEGER,
            records_validated INTEGER,
            records_rejected INTEGER,
            error_message TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database {DB_NAME} initialized.")
    
    # Auto-Restore from CSV if DB is empty (Phase 5 - Git Sync)
    import_prices_from_csv()

def log_system_event(level, source, message, metadata=""):
    """Logs a system event to the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO system_logs (timestamp, level, source, message, metadata) VALUES (?, ?, ?, ?, ?)",
                  (timestamp, level, source, message, str(metadata)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Logging Failed: {e}")

def import_prices_from_csv():
    """Restores prices from CSV if DB table is empty."""
    import os
    if not os.path.exists("data/market_prices.csv"):
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM market_prices")
    count = c.fetchone()[0]
    
    if count == 0:
        print("Restoring data from data/market_prices.csv...")
        try:
            df = pd.read_csv("data/market_prices.csv")
            df.to_sql('market_prices', conn, if_exists='append', index=False)
            print(f"Restored {len(df)} records.")
        except Exception as e:
            print(f"Restore failed: {e}")
    conn.close()

def save_prices(df):
    """Save a pandas DataFrame of prices to the DB."""
    conn = sqlite3.connect(DB_NAME)
    
    # Filter for valid columns only
    valid_cols = ['date', 'commodity', 'mandi', 'price_min', 'price_max', 'price_modal', 'arrival']
    # Add optional unit if present, else it defaults in DB
    if 'unit' in df.columns:
        valid_cols.append('unit')
        
    # Only keep columns that are in df
    cols_to_save = [c for c in valid_cols if c in df.columns]
    
    df_clean = df[cols_to_save].copy()
    
    df_clean.to_sql('market_prices', conn, if_exists='append', index=False)
    conn.close()
    print(f"Saved {len(df_clean)} price records.")

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

def export_prices_to_csv():
    """Export market prices to CSV for Git tracking."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM market_prices ORDER BY date", conn)
    conn.close()
    
    # Ensure data dir exists
    import os
    if not os.path.exists("data"):
        os.makedirs("data")
        
    df.to_csv("data/market_prices.csv", index=False)
    print("Exported prices to data/market_prices.csv")


# --- PERFORMANCE TRACKING (Phase 5) ---
def log_forecast(gen_date, commodity, mandi, forecast_df):
    """
    Logs generated forecasts to DB for future accuracy checking.
    forecast_df must have ['date', 'forecast_price'] columns.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # Batch insert
        data_to_insert = []
        for _, row in forecast_df.iterrows():
            target_date = row['date'].strftime("%Y-%m-%d") if isinstance(row['date'], pd.Timestamp) else row['date']
            # Check if already logged for this gen_date + target_date
            # We allow multiple forecasts for same target from different generation dates (rolling)
            data_to_insert.append((
                gen_date, target_date, commodity, mandi, row['forecast_price']
            ))
            
        c.executemany('''
            INSERT INTO forecast_logs (gen_date, target_date, commodity, mandi, predicted_price)
            VALUES (?, ?, ?, ?, ?)
        ''', data_to_insert)
        
        conn.commit()
    except Exception as e:
        print(f"Failed to log forecast: {e}")
    finally:
        conn.close()

def log_model_metrics(date, commodity, mandi, mape, rmse, accuracy, sample_size):
    """Logs calculated performance metrics."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO model_metrics (date, commodity, mandi, mape, rmse, signal_accuracy, sample_size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, commodity, mandi, mape, rmse, accuracy, sample_size))
        conn.commit()
    except Exception as e:
        print(f"Failed to log metrics: {e}")
    finally:
        conn.close()

def get_performance_history(commodity, mandi):
    """Retrieves historical performance metrics."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM model_metrics WHERE commodity='{commodity}' AND mandi='{mandi}' ORDER BY date", conn)
    conn.close()
    return df

def get_forecast_vs_actuals(commodity, mandi):
    """
    Joins forecast logs with actual market prices to compare.
    Returns DF with [target_date, predicted_price, actual_price, error, error_pct]
    """
    conn = sqlite3.connect(DB_NAME)
    
    # We want to compare the '1-day ahead' or '7-day ahead' forecasts.
    # For simplicity in this view, we take the forecast generated 1 to 7 days prior to target.
    # Here we just fetch all matched pairs.
    
    query = f'''
        SELECT 
            f.target_date, 
            f.predicted_price, 
            m.price_modal as actual_price,
            f.gen_date
        FROM forecast_logs f
        JOIN market_prices m ON f.target_date = m.date AND f.commodity = m.commodity AND f.mandi = m.mandi
        WHERE f.commodity = '{commodity}' AND f.mandi = '{mandi}'
        ORDER BY f.target_date
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    
    if not df.empty:
        df['error'] = df['predicted_price'] - df['actual_price']
        df['error_pct'] = (df['error'].abs() / df['actual_price']) * 100
        
    return df

# --- DATA RELIABILITY HELPERS (Phase 6) ---

def save_raw_prices(df, batch_id):
    """Saves incoming scraped data to the raw staging table."""
    if df.empty:
        return
        
    conn = sqlite3.connect(DB_NAME)
    
    # Add metadata columns
    df['batch_id'] = batch_id
    df['ingestion_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['status'] = 'PENDING'
    
    df.to_sql('raw_mandi_prices', conn, if_exists='append', index=False)
    conn.close()

def log_quality_issues(issues_list):
    """
    Logs data quality issues. 
    issues_list: List of dicts {batch_id, date, commodity, mandi, issue_type, severity, details, raw_value}
    """
    if not issues_list:
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.executemany('''
        INSERT INTO data_quality_logs (batch_id, date, commodity, mandi, issue_type, severity, details, raw_value)
        VALUES (:batch_id, :date, :commodity, :mandi, :issue_type, :severity, :details, :raw_value)
    ''', issues_list)
    conn.commit()
    conn.close()

def log_scraper_execution(status, duration, fetched, validated, rejected, error_msg=""):
    """Logs the execution summary of the scraper run."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO scraper_execution_stats (timestamp, status, duration_seconds, records_fetched, records_validated, records_rejected, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, status, duration, fetched, validated, rejected, error_msg))
    conn.commit()
    conn.close()

def get_scraper_stats(limit=30):
    """Fetch scraper stats for dashboard."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM scraper_execution_stats ORDER BY timestamp DESC LIMIT {limit}", conn)
    
    # Calculate Success Rate
    success_rate = 0
    if not df.empty:
        success_count = len(df[df['status'] == 'SUCCESS'])
        success_rate = (success_count / len(df)) * 100
        
    conn.close()
    return df, success_rate

def get_recent_quality_alerts(limit=50):
    """Fetch recent data quality alerts."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM data_quality_logs ORDER BY date DESC LIMIT {limit}", conn)
    conn.close()
    return df

if __name__ == "__main__":
    init_db()
