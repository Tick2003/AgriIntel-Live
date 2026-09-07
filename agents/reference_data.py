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
# Canonical counts — useful for test assertions
# ---------------------------------------------------------------------------

N_COMMODITIES: int = len(TRACKED_COMMODITIES)
N_MARKETS: int = len(TRACKED_MARKETS)
