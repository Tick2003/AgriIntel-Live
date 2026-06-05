"""
AgriIntel — Real Market Price Fetcher
======================================
Fetches LIVE commodity prices from official Indian government sources.

Data Source Chain (in priority order):
    1. data.gov.in  — Official Open Government API (Resource: 9ef84268...)
    2. Agmarknet     — Direct HTML scraping (agmarknet.gov.in)
    3. Simulation    — Fallback if all real sources fail

API Key Management:
    • Set env var  DATA_GOV_IN_API_KEY
    • Or add to Streamlit secrets: st.secrets["DATA_GOV_IN_API_KEY"]
    • Register free at https://data.gov.in → My Account → Generate API Key
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import random
import time
import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_GOV_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
DATA_GOV_BASE_URL = "https://api.data.gov.in/resource"

# Commodities & Markets we track
TRACKED_COMMODITIES = [
    "Onion", "Potato", "Tomato", "Wheat", "Rice",
    "Maize", "Soyabean", "Mustard", "Cotton", "Sugarcane",
    "Gram", "Tur", "Moong", "Masur", "Urad",
    "Apple", "Banana", "Mango", "Grapes", "Orange",
    "Garlic", "Ginger", "Turmeric", "Jeera", "Chilli"
]

TRACKED_MARKETS = [
    "Azadpur", "Lasalgaon", "Vashi", "Kolar", "Indore",
    "Pune", "Mumbai", "Jaipur", "Ahmedabad", "Surat",
    "Kanpur", "Lucknow", "Varanasi", "Agra", "Bareilly",
    "Kolkata", "Bhubaneswar", "Cuttack", "Patna", "Ranchi",
    "Chennai", "Coimbatore", "Madurai", "Hyderabad", "Warangal",
    "Bangalore", "Mysore", "Hubli", "Shimoga", "Bellary"
]


def _get_api_key():
    """Retrieve data.gov.in API key from environment or Streamlit secrets."""
    # 1. Environment variable
    key = os.environ.get("DATA_GOV_IN_API_KEY", "")
    if key:
        return key

    # 2. Streamlit secrets
    try:
        import streamlit as st
        key = st.secrets.get("DATA_GOV_IN_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    return ""


# ---------------------------------------------------------------------------
# Source 1: data.gov.in API (Official Government)
# ---------------------------------------------------------------------------

def fetch_from_data_gov(api_key: str, limit: int = 1000) -> pd.DataFrame:
    """
    Fetch current daily commodity prices from data.gov.in.
    Returns DataFrame matching AgriIntel schema:
        date, commodity, mandi, price_min, price_max, price_modal, arrival
    """
    url = f"{DATA_GOV_BASE_URL}/{DATA_GOV_RESOURCE_ID}"

    params = {
        "api-key": api_key,
        "format": "json",
        "limit": limit,
        "offset": 0,
    }

    logger.info(f"Fetching from data.gov.in (limit={limit})...")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        records = data.get("records", [])
        if not records:
            logger.warning("data.gov.in returned 0 records.")
            return pd.DataFrame()

        logger.info(f"data.gov.in returned {len(records)} records.")

        # Map to our schema
        rows = []
        for rec in records:
            try:
                # data.gov.in field names (may vary slightly)
                commodity = rec.get("commodity", rec.get("Commodity", ""))
                market = rec.get("market", rec.get("Market", ""))
                min_price = float(rec.get("min_price", rec.get("Min_Price", 0)))
                max_price = float(rec.get("max_price", rec.get("Max_Price", 0)))
                modal_price = float(rec.get("modal_price", rec.get("Modal_Price", 0)))

                # Parse arrival date
                arrival_date = rec.get("arrival_date", rec.get("Arrival_Date", ""))
                if arrival_date:
                    # Try multiple date formats
                    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y"):
                        try:
                            dt = datetime.strptime(arrival_date, fmt)
                            arrival_date = dt.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue

                if not commodity or not market or modal_price <= 0:
                    continue

                rows.append({
                    "date": arrival_date or datetime.now().strftime("%Y-%m-%d"),
                    "commodity": commodity.strip().title(),
                    "mandi": market.strip().title(),
                    "price_min": min_price,
                    "price_max": max_price,
                    "price_modal": modal_price,
                    "arrival": float(rec.get("quantity", rec.get("Arrival", random.randint(50, 500)))),
                })
            except (ValueError, TypeError) as e:
                continue

        df = pd.DataFrame(rows)
        if not df.empty:
            logger.info(f"Parsed {len(df)} valid records from data.gov.in "
                        f"({df['commodity'].nunique()} commodities, {df['mandi'].nunique()} markets)")
        return df

    except requests.exceptions.Timeout:
        logger.warning("data.gov.in request timed out.")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        logger.error(f"data.gov.in HTTP error: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"data.gov.in fetch failed: {e}")
        return pd.DataFrame()


def fetch_from_data_gov_filtered(api_key: str, commodity: str = None,
                                   state: str = None) -> pd.DataFrame:
    """Fetch with optional filters for specific commodity/state."""
    url = f"{DATA_GOV_BASE_URL}/{DATA_GOV_RESOURCE_ID}"

    params = {
        "api-key": api_key,
        "format": "json",
        "limit": 500,
        "offset": 0,
    }

    if commodity:
        params["filters[commodity]"] = commodity
    if state:
        params["filters[state]"] = state

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])

        rows = []
        for rec in records:
            try:
                modal_price = float(rec.get("modal_price", rec.get("Modal_Price", 0)))
                if modal_price <= 0:
                    continue

                arrival_date = rec.get("arrival_date", rec.get("Arrival_Date", ""))
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y"):
                    try:
                        dt = datetime.strptime(arrival_date, fmt)
                        arrival_date = dt.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue

                rows.append({
                    "date": arrival_date or datetime.now().strftime("%Y-%m-%d"),
                    "commodity": rec.get("commodity", rec.get("Commodity", "")).strip().title(),
                    "mandi": rec.get("market", rec.get("Market", "")).strip().title(),
                    "price_min": float(rec.get("min_price", rec.get("Min_Price", 0))),
                    "price_max": float(rec.get("max_price", rec.get("Max_Price", 0))),
                    "price_modal": modal_price,
                    "arrival": float(rec.get("quantity", rec.get("Arrival", random.randint(50, 500)))),
                })
            except (ValueError, TypeError):
                continue

        return pd.DataFrame(rows)

    except Exception as e:
        logger.error(f"Filtered data.gov.in fetch failed: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Source 2: Direct Agmarknet Scraping
# ---------------------------------------------------------------------------

def fetch_from_agmarknet_direct() -> pd.DataFrame:
    """
    Scrape prices directly from agmarknet.gov.in.
    This is a backup if data.gov.in API is down.
    """
    logger.info("Attempting direct Agmarknet scraping...")

    try:
        from bs4 import BeautifulSoup

        # Agmarknet daily report page
        url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract ASP.NET form tokens for POST
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})

        if not viewstate or not event_validation:
            logger.warning("Could not find ASP.NET form tokens on Agmarknet.")
            return pd.DataFrame()

        all_rows = []

        # Query a subset of commodities
        for commodity in ["Onion", "Tomato", "Potato", "Wheat", "Rice"]:
            try:
                form_data = {
                    "__VIEWSTATE": viewstate.get("value", ""),
                    "__EVENTVALIDATION": event_validation.get("value", ""),
                    "ctl00$cph$ddlCommodity": commodity,
                    "ctl00$cph$btnGo": "Submit",
                }

                post_resp = session.post(url, data=form_data, headers=headers, timeout=15)
                post_soup = BeautifulSoup(post_resp.text, "html.parser")

                # Parse the results table
                table = post_soup.find("table", {"id": "cph_GridPriceData"})
                if not table:
                    continue

                for row in table.find_all("tr")[1:]:  # Skip header
                    cells = row.find_all("td")
                    if len(cells) >= 7:
                        all_rows.append({
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "commodity": commodity,
                            "mandi": cells[1].text.strip(),
                            "price_min": float(cells[4].text.strip() or 0),
                            "price_max": float(cells[5].text.strip() or 0),
                            "price_modal": float(cells[6].text.strip() or 0),
                            "arrival": float(cells[3].text.strip() or 0),
                        })

                time.sleep(1)  # Be respectful to the server
            except Exception as e:
                logger.warning(f"Agmarknet scrape failed for {commodity}: {e}")
                continue

        df = pd.DataFrame(all_rows)
        if not df.empty:
            logger.info(f"Scraped {len(df)} records from Agmarknet directly.")
        return df

    except Exception as e:
        logger.error(f"Agmarknet direct scraping failed: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Source 3: Simulation Fallback (Enhanced with realistic patterns)
# ---------------------------------------------------------------------------

def fetch_simulated_prices() -> pd.DataFrame:
    """
    Generates realistic simulated prices as final fallback.
    Uses realistic base prices per commodity and regional variance.
    """
    logger.info("Using simulated price generation (fallback).")

    # Realistic base prices (Rs/Quintal) as of 2025-2026
    BASE_PRICES = {
        "Onion": 2200, "Potato": 1400, "Tomato": 2800, "Wheat": 2600, "Rice": 3800,
        "Maize": 2100, "Soyabean": 4500, "Mustard": 5200, "Cotton": 6800, "Sugarcane": 3500,
        "Gram": 5100, "Tur": 7500, "Moong": 7200, "Masur": 5800, "Urad": 6500,
        "Apple": 8000, "Banana": 2500, "Mango": 4500, "Grapes": 5000, "Orange": 3800,
        "Garlic": 6000, "Ginger": 4000, "Turmeric": 9500, "Jeera": 25000, "Chilli": 12000,
    }

    data = []
    today = datetime.now().strftime("%Y-%m-%d")

    for com in TRACKED_COMMODITIES:
        base_price = BASE_PRICES.get(com, random.randint(2000, 5000))
        for mandi in TRACKED_MARKETS:
            # Regional variance (±15%)
            regional_factor = 1.0 + random.uniform(-0.15, 0.15)
            modal = int(base_price * regional_factor)

            data.append({
                "date": today,
                "commodity": com,
                "mandi": mandi,
                "price_min": modal - random.randint(50, 200),
                "price_max": modal + random.randint(50, 200),
                "price_modal": modal,
                "arrival": random.randint(50, 500),
            })

    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Main Public API — Cascading Fetch with Fallbacks
# ---------------------------------------------------------------------------

def get_all_commodities_data() -> pd.DataFrame:
    """
    Fetches today's commodity prices using cascading data sources:
        1. data.gov.in API (if API key available)
        2. Direct Agmarknet scraping
        3. Simulation fallback

    Returns DataFrame with columns:
        date, commodity, mandi, price_min, price_max, price_modal, arrival
    """
    source_used = "none"

    # ---- Source 1: data.gov.in ----
    api_key = _get_api_key()
    if api_key:
        print("📡 Fetching REAL prices from data.gov.in...")
        df = fetch_from_data_gov(api_key, limit=1500)
        if not df.empty:
            source_used = "data.gov.in"
            print(f"✅ Got {len(df)} real records from data.gov.in "
                  f"({df['commodity'].nunique()} commodities, {df['mandi'].nunique()} markets)")
            _log_source(source_used, len(df))
            return df
        else:
            print("⚠️ data.gov.in returned no data, trying next source...")
    else:
        print("ℹ️ No DATA_GOV_IN_API_KEY set. Skipping data.gov.in. "
              "(Register free at https://data.gov.in)")

    # ---- Source 2: Direct Agmarknet ----
    print("📡 Trying direct Agmarknet scraping...")
    df = fetch_from_agmarknet_direct()
    if not df.empty:
        source_used = "agmarknet_direct"
        print(f"✅ Scraped {len(df)} records from Agmarknet directly.")
        _log_source(source_used, len(df))
        return df
    else:
        print("⚠️ Agmarknet scraping failed, using simulation fallback...")

    # ---- Source 3: Simulation ----
    df = fetch_simulated_prices()
    source_used = "simulation"
    print(f"🔄 Generated {len(df)} simulated records (fallback).")
    _log_source(source_used, len(df))
    return df


def _log_source(source: str, record_count: int):
    """Log which data source was used for audit trail."""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import database.db_manager as dbm
        dbm.log_system_event(
            "INFO", "DATA_SOURCE",
            f"Price data fetched from: {source} ({record_count} records)"
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = get_all_commodities_data()
    print(f"\nResult: {len(df)} records")
    if not df.empty:
        print(df.head(10).to_string(index=False))
        print(f"\nCommodities: {df['commodity'].nunique()}")
        print(f"Markets: {df['mandi'].nunique()}")
