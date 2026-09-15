"""
agents/data_reliability.py — Data Validation Agent
====================================================
Validates scraped market data before it is promoted to the production
database.  Acts as the quality gate in the ETL pipeline.

Checks performed:
    1. Completeness  — required fields must not be null
    2. Plausibility  — price changes > 50 % are flagged; > 300 % are rejected
    3. Uniqueness    — intra-batch duplicates are dropped
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataReliabilityAgent:
    """
    Validates scraped market data before promotion to the production database.
    Checks for:
    1. Completeness (Missing Values)
    2. Uniqueness (Duplicate Entries)
    3. Plausibility (Outliers vs Historical Data)
    """

    def __init__(self, db_manager: Any) -> None:
        self.dbm = db_manager

    def validate_batch(
        self, df: pd.DataFrame, batch_id: str
    ) -> tuple[pd.DataFrame, list[dict], dict[str, int]]:
        """
        Main validation pipeline.

        Returns:
            valid_df: DataFrame of records safe to promote.
            issues:   List of issue dicts for audit logging.
            stats:    Dict with keys total / valid / rejected.
        """
        issues: list[dict] = []
        valid_indices: list = []
        seen_keys: set = set()  # Track (date, commodity, mandi) for intra-batch deduplication

        if df.empty:
            return pd.DataFrame(), [], {"total": 0, "valid": 0, "rejected": 0}

        logger.info("Validating batch %s with %d records...", batch_id, len(df))

        for idx, row in df.iterrows():
            is_valid = True

            # 1. Missing Value Check
            if pd.isna(row['price_modal']) or pd.isna(row['commodity']) or pd.isna(row['mandi']):
                issues.append({
                    "batch_id": batch_id,
                    "date": row.get('date', datetime.now().strftime("%Y-%m-%d")),
                    "commodity": row.get('commodity', 'Unknown'),
                    "mandi": row.get('mandi', 'Unknown'),
                    "issue_type": "MISSING_DATA",
                    "severity": "CRITICAL",
                    "details": "Critical fields (Price/Commodity/Mandi) are missing.",
                    "raw_value": str(row.to_dict())
                })
                is_valid = False

            # 2. Plausibility Check (Outliers)
            if is_valid:
                try:
                    last_df = self.dbm.get_latest_prices(row['commodity'])
                    if not last_df.empty:
                        mandi_df = last_df[last_df['mandi'] == row['mandi']]
                        if not mandi_df.empty:
                            last_price = mandi_df.iloc[-1]['price_modal']
                            current_price = row['price_modal']
                            pct_change = abs((current_price - last_price) / last_price)

                            if pct_change > 0.5:  # 50 % jump — flag it
                                issues.append({
                                    "batch_id": batch_id,
                                    "date": row['date'],
                                    "commodity": row['commodity'],
                                    "mandi": row['mandi'],
                                    "issue_type": "OUTLIER_SHOCK",
                                    "severity": "WARNING",
                                    "details": (
                                        f"Price changed by {pct_change * 100:.1f}%"
                                        f" (Prev: {last_price}, Curr: {current_price})"
                                    ),
                                    "raw_value": str(current_price)
                                })
                                # Real shocks happen — only reject if statistically impossible.
                                if pct_change > 3.0:  # > 300 % — almost certainly bad data
                                    is_valid = False
                                    issues[-1]['severity'] = "CRITICAL"
                                    issues[-1]['details'] += " — REJECTED as improbable."
                except Exception as exc:
                    logger.warning("Validation error during outlier check: %s", exc)

            # 3. Duplicate Check (Intra-batch deduplication)
            if is_valid:
                dedup_key = (
                    str(row.get('date', '')),
                    str(row.get('commodity', '')),
                    str(row.get('mandi', '')),
                )
                if dedup_key in seen_keys:
                    issues.append({
                        "batch_id": batch_id,
                        "date": row.get('date', datetime.now().strftime("%Y-%m-%d")),
                        "commodity": row.get('commodity', 'Unknown'),
                        "mandi": row.get('mandi', 'Unknown'),
                        "issue_type": "DUPLICATE",
                        "severity": "WARNING",
                        "details": (
                            f"Duplicate record within batch for"
                            f" {dedup_key[1]} at {dedup_key[2]} on {dedup_key[0]}."
                        ),
                        "raw_value": str(row.to_dict())
                    })
                    is_valid = False
                else:
                    seen_keys.add(dedup_key)

            if is_valid:
                valid_indices.append(idx)

        valid_df = df.loc[valid_indices].copy()
        rejected_count = len(df) - len(valid_df)

        logger.info(
            "Batch %s validated — %d valid, %d rejected.",
            batch_id, len(valid_df), rejected_count,
        )
        return valid_df, issues, {
            "total": len(df),
            "valid": len(valid_df),
            "rejected": rejected_count,
        }


