"""
database/connection.py — Connection Pool & Schema Init
=======================================================
Thread-safe SQLite connection management and database initialization.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from contextlib import contextmanager
import bcrypt
import logging
import threading

logger = logging.getLogger(__name__)

# Thread-safe import of settings
try:
    from config import settings
    DB_NAME = settings.db.name
except ImportError:
    DB_NAME = "agri_intel.db"

# --- Connection Pool (Thread-Safe) ---
_local = threading.local()

@contextmanager
def get_connection():
    """Thread-safe database connection context manager.
    Reuses connections per-thread to avoid excessive open/close overhead."""
    conn = getattr(_local, 'connection', None)
    owned = False
    if conn is None:
        conn = sqlite3.connect(DB_NAME, timeout=30)
        conn.execute("PRAGMA busy_timeout=5000")
        _local.connection = conn
        owned = True
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        if owned:
            try:
                conn.close()
            except Exception:
                pass
            _local.connection = None


def init_db():
    """Initialize the database with necessary tables (v2.0-HARDENED)."""
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()
    
    try:
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
        
        # --- MIGRATIONS ---
        # Check if 'unit' exists in market_prices (Update)
        try:
            c.execute("SELECT unit FROM market_prices LIMIT 1")
        except sqlite3.OperationalError:
            try:
                c.execute("ALTER TABLE market_prices ADD COLUMN unit TEXT DEFAULT 'Rs/Quintal'")
            except sqlite3.OperationalError:
                logger.debug("Column 'unit' already exists or migration failed")

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
        
        # Cleanup Old Date Formats (Wed, Fri etc.) to fix sorting
        try:
            c.execute("DELETE FROM news_alerts WHERE substr(date, 1, 1) NOT IN ('0','1','2','3','4','5','6','7','8','9')")
            if c.rowcount > 0:
                logger.info(f"Cleaned up {c.rowcount} news items with old date format.")
        except sqlite3.OperationalError:
            logger.debug("news_alerts cleanup skipped")

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
            try:
                c.execute("ALTER TABLE weather_logs ADD COLUMN wind_speed REAL DEFAULT 0.0")
                c.execute("ALTER TABLE weather_logs ADD COLUMN humidity REAL DEFAULT 0.0")
            except sqlite3.OperationalError:
                logger.debug("Weather migration skipped")

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
                mae REAL,
                health_score REAL,
                signal_accuracy REAL,
                sample_size INTEGER
            )
        ''') 
        
        # Migration for Phase 7 (Performance Tracker)
        try:
            c.execute("SELECT mae FROM model_metrics LIMIT 1")
        except sqlite3.OperationalError:
            try:
                c.execute("ALTER TABLE model_metrics ADD COLUMN mae REAL DEFAULT 0.0")
                c.execute("ALTER TABLE model_metrics ADD COLUMN health_score REAL DEFAULT 0.0")
            except sqlite3.OperationalError:
                logger.debug("model_metrics migration skipped")

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
        
        # --- WAREHOUSE OPTIMIZATION (Phase 6) ---
        # Add Index for fast filtering on Commodity+Mandi+Date
        c.execute("CREATE INDEX IF NOT EXISTS idx_market_prices_cmd ON market_prices (commodity, mandi, date)")
        
        # --- SAAS ARCHITECTURE (Phase 7) ---
        c.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                plan_type TEXT DEFAULT 'Free',
                created_at TEXT
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password_hash TEXT,
                role TEXT DEFAULT 'Viewer',
                org_id INTEGER,
                created_at TEXT,
                FOREIGN KEY(org_id) REFERENCES organizations(id)
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS voice_call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_sid TEXT,
                phone_number TEXT,
                timestamp TEXT,
                language TEXT,
                region TEXT,
                transcript TEXT,
                intent TEXT,
                entities TEXT,
                api_used TEXT,
                response_text TEXT,
                confidence_score REAL,
                duration_seconds REAL
            )
        ''')

        # Commit all table creations FIRST before any data operations
        conn.commit()

        # Default Org/User for Demo — ONLY from environment variables
        try:
            c.execute("SELECT count(*) FROM organizations")
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO organizations (name, plan_type, created_at) VALUES ('Demo Org', 'Enterprise', ?)", 
                         (datetime.now().strftime("%Y-%m-%d"),))
                org_id = c.lastrowid
                
                # Read admin creds from environment (secure — no hardcoded fallback)
                admin_email = ""
                admin_password = ""
                try:
                    from config import settings as _cfg
                    admin_email = _cfg.security.default_admin_email
                    admin_password = _cfg.security.default_admin_password
                except ImportError:
                    import os as _os
                    admin_email = _os.environ.get("DEFAULT_ADMIN_EMAIL", "")
                    admin_password = _os.environ.get("DEFAULT_ADMIN_PASSWORD", "")
                
                if not admin_email or not admin_password:
                    logger.warning(
                        "No admin credentials configured. Set DEFAULT_ADMIN_EMAIL and "
                        "DEFAULT_ADMIN_PASSWORD environment variables to create the initial admin user. "
                        "Skipping default admin creation."
                    )
                    conn.commit()
                    return
                
                salt = bcrypt.gensalt()
                hashed_admin = bcrypt.hashpw(admin_password.encode('utf-8'), salt).decode('utf-8')
                c.execute("INSERT INTO users (email, password_hash, role, org_id, created_at) VALUES (?, ?, 'Admin', ?, ?)",
                         (admin_email, hashed_admin, org_id, datetime.now().strftime("%Y-%m-%d")))
                logger.info(f"Initialized Default SaaS Org & Admin: {admin_email}")
                conn.commit()
        except Exception as e:
            logger.error(f"SaaS Init Error: {e}", exc_info=True)

        # --- REAL-TIME UPGRADE (RACE Engine) ---

        # Table: Intraday Trades (Real-Time Tick Storage)
        c.execute('''
            CREATE TABLE IF NOT EXISTS intraday_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                commodity TEXT,
                mandi TEXT,
                price REAL,
                quantity REAL,
                trade_type TEXT
            )
        ''')
        # Index for fast real-time queries
        c.execute("CREATE INDEX IF NOT EXISTS idx_intraday_cmd ON intraday_trades (commodity, mandi, timestamp)")

        # Table: Ensemble Weights Log (RACE Model Weight Tracking)
        c.execute('''
            CREATE TABLE IF NOT EXISTS ensemble_weights_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                commodity TEXT,
                mandi TEXT,
                regime TEXT,
                model_name TEXT,
                weight REAL,
                cv_mape REAL
            )
        ''')

        # Migration: Add regime column to forecast_logs
        try:
            c.execute("SELECT regime FROM forecast_logs LIMIT 1")
        except sqlite3.OperationalError:
            try:
                c.execute("ALTER TABLE forecast_logs ADD COLUMN regime TEXT DEFAULT 'UNKNOWN'")
            except sqlite3.OperationalError:
                logger.debug("forecast_logs regime migration skipped")

        # Migration: Add model_version column to model_metrics (if missing)
        try:
            c.execute("SELECT model_version FROM model_metrics LIMIT 1")
        except sqlite3.OperationalError:
            try:
                c.execute("ALTER TABLE model_metrics ADD COLUMN model_version TEXT DEFAULT 'v1.0'")
            except sqlite3.OperationalError:
                logger.debug("model_metrics model_version migration skipped")

        conn.commit()
        
    except Exception as e:
        logger.error(f"init_db error: {e}", exc_info=True)
        # Try to commit whatever we have so far
        try:
            conn.commit()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
        
    # Auto-Restore from CSV if DB is empty
    try:
        from database.prices import import_prices_from_csv
        import_prices_from_csv()
    except Exception as e:
        logger.error(f"CSV import failed during init: {e}", exc_info=True)
