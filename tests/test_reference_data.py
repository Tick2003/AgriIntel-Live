"""
tests/test_reference_data.py — Unit tests for agents/reference_data.py

Validates that the canonical commodity/market lists are well-formed and
consistent — critical since all ETL modules depend on this as a single
source of truth.
"""

import pytest


class TestTrackedCommodities:
    """Tests for the TRACKED_COMMODITIES canonical list."""

    def setup_method(self):
        from agents.reference_data import TRACKED_COMMODITIES
        self.commodities = TRACKED_COMMODITIES

    def test_is_list(self):
        assert isinstance(self.commodities, list)

    def test_non_empty(self):
        assert len(self.commodities) > 0

    def test_contains_key_crops(self):
        """Core crops that drive Indian agri markets must be present."""
        assert "Onion" in self.commodities
        assert "Tomato" in self.commodities
        assert "Potato" in self.commodities

    def test_all_strings(self):
        for item in self.commodities:
            assert isinstance(item, str), f"Expected str, got {type(item)} for {item!r}"

    def test_no_empty_strings(self):
        for item in self.commodities:
            assert item.strip() != "", "Empty string found in TRACKED_COMMODITIES"

    def test_no_duplicates(self):
        assert len(self.commodities) == len(set(self.commodities)), \
            "Duplicate entries found in TRACKED_COMMODITIES"


class TestTrackedMarkets:
    """Tests for the TRACKED_MARKETS canonical list."""

    def setup_method(self):
        from agents.reference_data import TRACKED_MARKETS
        self.markets = TRACKED_MARKETS

    def test_is_list(self):
        assert isinstance(self.markets, list)

    def test_non_empty(self):
        assert len(self.markets) > 0

    def test_contains_key_mandis(self):
        """Key national mandis must be present."""
        assert "Azadpur" in self.markets

    def test_all_strings(self):
        for item in self.markets:
            assert isinstance(item, str), f"Expected str, got {type(item)} for {item!r}"

    def test_no_empty_strings(self):
        for item in self.markets:
            assert item.strip() != "", "Empty string found in TRACKED_MARKETS"

    def test_no_duplicates(self):
        assert len(self.markets) == len(set(self.markets)), \
            "Duplicate entries found in TRACKED_MARKETS"


class TestReferenceDataConsistency:
    """Cross-list consistency checks."""

    def test_both_exports_present(self):
        """Module must export both constants (ETL modules depend on both)."""
        import agents.reference_data as ref
        assert hasattr(ref, "TRACKED_COMMODITIES")
        assert hasattr(ref, "TRACKED_MARKETS")

    def test_reasonable_sizes(self):
        from agents.reference_data import TRACKED_COMMODITIES, TRACKED_MARKETS
        # Sanity: at least 5 commodities and 5 markets
        assert len(TRACKED_COMMODITIES) >= 5
        assert len(TRACKED_MARKETS) >= 5
