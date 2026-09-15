"""
database — AgriIntel Database Package
======================================
Public API for all database operations.

Import style
------------
    # Preferred — explicit per-module imports:
    from database.prices import save_prices, get_latest_prices

    # Legacy — works via the backward-compat shim:
    import database.db_manager as dbm

All functions are re-exported here from ``database.db_manager`` so that
``from database import save_prices`` works without changes.
The authoritative re-export list lives in ``database/db_manager.py``;
this file simply delegates to it to avoid the two lists drifting.
"""

# Re-export everything from the canonical shim (single source of truth).
from database.db_manager import *  # noqa: F401, F403
from database.db_manager import __all__  # noqa: F401
