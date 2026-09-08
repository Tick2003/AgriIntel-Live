"""
tests/test_utils.py — Unit tests for utils/graph_algo.py and utils/telecom_mapper.py
"""

import pytest

# ---------------------------------------------------------------------------
# MandiGraph / Dijkstra tests
# ---------------------------------------------------------------------------

class TestMandiGraph:
    """Tests for the Dijkstra-based spatial arbitrage engine."""

    def setup_method(self):
        from utils.graph_algo import MandiGraph
        self.mg = MandiGraph()
        self.mg.add_route("Delhi", "Agra", 200)
        self.mg.add_route("Agra", "Jaipur", 240)
        self.mg.add_route("Delhi", "Jaipur", 280)
        self.mg.add_route("Agra", "Lucknow", 350)

    def test_graph_has_nodes(self):
        assert "Delhi" in self.mg.graph
        assert "Agra" in self.mg.graph
        assert "Jaipur" in self.mg.graph

    def test_bidirectional_routes(self):
        """add_route must create edges in both directions."""
        # Delhi → Agra
        assert any(n == "Agra" for n, _ in self.mg.graph["Delhi"])
        # Agra → Delhi (reverse)
        assert any(n == "Delhi" for n, _ in self.mg.graph["Agra"])

    def test_shortest_path_direct(self):
        distances, _ = self.mg._get_shortest_paths("Delhi")
        assert distances["Agra"] == 200

    def test_shortest_path_via_intermediate(self):
        """Delhi→Lucknow goes via Agra (200+350=550)."""
        distances, _ = self.mg._get_shortest_paths("Delhi")
        assert distances["Lucknow"] == 550

    def test_shortest_path_chooses_min(self):
        """Delhi→Jaipur: direct (280) should win over via Agra (200+240=440)."""
        distances, _ = self.mg._get_shortest_paths("Delhi")
        assert distances["Jaipur"] == 280

    def test_find_best_profit_route_returns_best(self):
        prices = {"Agra": 2000, "Jaipur": 3000, "Lucknow": 1500}
        best, ranked = self.mg.find_best_profit_route("Delhi", quantity_tons=1, commodity_prices=prices)
        assert best is not None
        assert "mandi" in best
        assert "net_profit" in best
        # Ranked list should be sorted descending by net_profit
        profits = [o["net_profit"] for o in ranked]
        assert profits == sorted(profits, reverse=True)

    def test_find_best_profit_route_unknown_mandi(self):
        """If source not connected to price mandi, it should be skipped."""
        prices = {"NonExistent": 9999}
        best, ranked = self.mg.find_best_profit_route("Delhi", quantity_tons=1, commodity_prices=prices)
        assert best is None
        assert ranked == []

    def test_get_demo_graph(self):
        from utils.graph_algo import get_demo_graph
        demo = get_demo_graph()
        assert "Cuttack" in demo.graph
        assert "Bhubaneswar" in demo.graph


# ---------------------------------------------------------------------------
# Demo graph integration
# ---------------------------------------------------------------------------

class TestDemoGraphIntegration:
    """End-to-end test using the pre-wired Odisha demo graph."""

    def setup_method(self):
        from utils.graph_algo import get_demo_graph
        self.mg = get_demo_graph()

    def test_distances_reachable(self):
        distances, _ = self.mg._get_shortest_paths("Cuttack")
        assert distances["Bhubaneswar"] < float("inf")
        assert distances["Jatni"] < float("inf")

    def test_profit_route_real_prices(self):
        prices = {
            "Bhubaneswar": 2500,
            "Jatni": 2300,
            "Puri": 2800,
        }
        best, ranked = self.mg.find_best_profit_route("Cuttack", quantity_tons=2, commodity_prices=prices)
        assert best is not None
        assert len(ranked) == 3


# ---------------------------------------------------------------------------
# TelecomMapper tests
# ---------------------------------------------------------------------------

class TestTelecomMapper:
    """Tests for the telecom circle → state/language mapper."""

    def setup_method(self):
        from utils.telecom_mapper import TelecomMapper
        self.mapper = TelecomMapper()

    def test_circle_lang_map_populated(self):
        assert len(self.mapper.circle_lang_map) > 10

    def test_known_states_in_map(self):
        assert "Maharashtra" in self.mapper.circle_lang_map
        assert "Delhi" in self.mapper.circle_lang_map
        assert "Karnataka" in self.mapper.circle_lang_map

    def test_detect_returns_tuple(self):
        result = self.mapper.detect_region_and_language("+919876543210")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_detect_unknown_number_fallback(self):
        region, lang = self.mapper.detect_region_and_language("12345")
        assert isinstance(region, str)
        assert isinstance(lang, str)

    def test_ten_digit_number_prefixed(self):
        """10-digit numbers should get +91 prefix automatically."""
        region, lang = self.mapper.detect_region_and_language("9820012345")
        assert isinstance(region, str)
