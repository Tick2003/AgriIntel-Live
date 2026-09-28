"""
database/auth_db.py — User & Organization Operations
======================================================
"""

import logging

from database.connection import get_connection

logger = logging.getLogger(__name__)


def get_user_by_email(email: str) -> dict | None:
    """Retrieve user details for Auth."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, email, password_hash, role, org_id FROM users WHERE email=?", (email,))
            row = c.fetchone()
            if row:
                 return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3], "org_id": row[4]}
            return None
    except Exception as e:
        logger.error("get_user_by_email failed for %s: %s", email, e)
        return None


def get_org_details(org_id: int) -> dict | None:
    """Retrieve Organization details."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT name, plan_type FROM organizations WHERE id=?", (org_id,))
            row = c.fetchone()
            if row:
                 return {"name": row[0], "plan_type": row[1]}
            return None
    except Exception as e:
        logger.error("get_org_details failed for org_id=%s: %s", org_id, e)
        return None

