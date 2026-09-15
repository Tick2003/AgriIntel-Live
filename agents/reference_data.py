"""
agents/reference_data.py — Shared Reference Data
==================================================
Single source of truth for TRACKED_COMMODITIES and TRACKED_MARKETS.

All ETL modules, agents, and tests should import from here instead of
re-defining these lists locally.

Usage
-----
    from agents.reference_data import TRACKED_COMMODITIES, TRACKED_MARKETS
"""

# ---------------------------------------------------------------------------
# Commodities tracked by AgriIntel's data pipeline
# ---------------------------------------------------------------------------

TRACKED_COMMODITIES: list[str] = [
    # Vegetables
    "Onion", "Potato", "Tomato",
    # Cereals
    "Wheat", "Rice", "Maize",
    # Oilseeds
    "Soyabean", "Mustard",
    # Cash Crops
    "Cotton", "Sugarcane",
    # Pulses
    "Gram", "Tur", "Moong", "Masur", "Urad",
    # Fruits
    "Apple", "Banana", "Mango", "Grapes", "Orange",
    # Spices
    "Garlic", "Ginger", "Turmeric", "Jeera", "Chilli",
]

# ---------------------------------------------------------------------------
# APMC / eNAM mandis tracked by AgriIntel's data pipeline
# ---------------------------------------------------------------------------

TRACKED_MARKETS: list[str] = [
    # North
    "Azadpur", "Agra", "Bareilly", "Lucknow", "Varanasi", "Jaipur",
    # West
    "Indore", "Ahmedabad", "Surat", "Mumbai", "Vashi", "Pune",
    # South
    "Lasalgaon", "Kolar", "Bangalore", "Mysore", "Hubli", "Shimoga", "Bellary",
    "Chennai", "Coimbatore", "Madurai", "Hyderabad", "Warangal",
    # East
    "Kolkata", "Bhubaneswar", "Cuttack", "Patna", "Ranchi",
]

# ---------------------------------------------------------------------------
# GPS coordinates for each tracked mandi (used by the weather fetch pipeline)
# Source: approximate centre-point of each city/district
# ---------------------------------------------------------------------------

MANDI_COORDS: dict[str, dict[str, float]] = {
    "Azadpur":   {"lat": 28.7,  "lon": 77.1},   # Delhi
    "Lasalgaon": {"lat": 20.1,  "lon": 74.2},   # Nashik
    "Vashi":     {"lat": 19.0,  "lon": 73.0},   # Mumbai (Navi)
    "Kolar":     {"lat": 13.1,  "lon": 78.1},   # Karnataka
    "Indore":    {"lat": 22.7,  "lon": 75.8},   # MP
    "Pune":      {"lat": 18.5,  "lon": 73.8},
    "Jaipur":    {"lat": 26.9,  "lon": 75.7},
    "Ahmedabad": {"lat": 23.0,  "lon": 72.5},
    "Kolkata":   {"lat": 22.5,  "lon": 88.3},
    "Bengaluru": {"lat": 12.9,  "lon": 77.5},
    "Agra":      {"lat": 27.1,  "lon": 78.0},
    "Nasik":     {"lat": 19.9,  "lon": 73.7},
}

# ---------------------------------------------------------------------------
# Canonical counts — useful for test assertions
# ---------------------------------------------------------------------------

N_COMMODITIES: int = len(TRACKED_COMMODITIES)
N_MARKETS: int = len(TRACKED_MARKETS)
