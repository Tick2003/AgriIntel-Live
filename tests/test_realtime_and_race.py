"""
Unit Test Suite for Real-Time Terminal & RACE Forecasting Engine
================================================================
Verifies correct operations of:
1. Real-Time Tick Stream Generator
2. RACE Forecaster & Regime Detection
3. Intraday Shock Detection
4. Real-Time Risk Score Augmentation
"""

import sys
import os
import time
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.db_manager as dbm
from etl.realtime_stream import (
    start_realtime_generator,
    stop_realtime_generator,
    get_stream_status,
    get_intraday_trades
)
from agents.forecast_engine.ensemble import RACEForecaster, ForecastResult
from agents.forecast_execution import ForecastingAgent
from agents.shock_monitoring import AnomalyDetectionEngine
from agents.risk_scoring import MarketRiskEngine


class TestRealtimeAndRace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize test/dev DB
        dbm.init_db()

    def setUp(self):
        # Stop generator if running from previous tests
        stop_realtime_generator()

    def tearDown(self):
        stop_realtime_generator()

    def test_01_realtime_generator(self):
        """Test start, status, and stop of Real-Time Generator."""
        status = get_stream_status()
        self.assertFalse(status["is_running"])

        # Start generator
        start_realtime_generator("Potato", "Agra")
        time.sleep(1) # wait briefly

        status = get_stream_status()
        self.assertTrue(status["is_running"])
        self.assertEqual(status["commodity"], "Potato")
        self.assertEqual(status["mandi"], "Agra")

        # Let it generate a few ticks
        time.sleep(4)

        status = get_stream_status()
        self.assertGreater(status["ticks_generated"], 0)

        # Retrieve ticks from DB
        df = get_intraday_trades("Potato", "Agra", limit=10)
        self.assertFalse(df.empty)
        self.assertIn("trade_type", df.columns)
        self.assertIn("price", df.columns)
        self.assertIn("quantity", df.columns)

        # Stop generator
        stop_realtime_generator()
        status = get_stream_status()
        self.assertFalse(status["is_running"])

    def test_02_race_forecaster_fit_and_predict(self):
        """Test RACEForecaster training and 30-day forecasting."""
        # Create dummy price history (90 days)
        np.random.seed(42)
        dates = pd.date_range(end=datetime.today().date(), periods=90)
        prices = 2000 + np.cumsum(np.random.normal(0, 30, 90))
        arrival = np.random.randint(100, 500, 90)

        df = pd.DataFrame({
            "date": dates,
            "price": prices,
            "arrival": arrival,
            "commodity": ["Tomato"] * 90,
            "mandi": ["Agra"] * 90
        })

        forecaster = RACEForecaster()
        result = forecaster.forecast(df, "Tomato", "Agra", horizon=30)

        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(len(result.forecast_df), 30)
        self.assertIn("forecast_price", result.forecast_df.columns)
        self.assertIn("lower_bound", result.forecast_df.columns)
        self.assertIn("upper_bound", result.forecast_df.columns)
        self.assertIn("XGBoost", result.model_weights)
        self.assertGreaterEqual(result.confidence, 0.0)

    def test_03_intraday_shock_detection(self):
        """Test 3-sigma intraday shock detection engine."""
        # Create normal and shock ticks
        normal_ticks = pd.DataFrame([
            {"timestamp": "2026-06-01 10:00:00", "price": 100.0, "quantity": 10, "trade_type": "TRADE"},
            {"timestamp": "2026-06-01 10:01:00", "price": 101.0, "quantity": 12, "trade_type": "TRADE"},
            {"timestamp": "2026-06-01 10:02:00", "price": 99.0, "quantity": 8, "trade_type": "TRADE"},
            {"timestamp": "2026-06-01 10:03:00", "price": 100.5, "quantity": 11, "trade_type": "TRADE"},
        ])

        shock_ticks = pd.DataFrame([
            {"timestamp": "2026-06-01 10:00:00", "price": 100.0, "quantity": 10, "trade_type": "TRADE"},
            {"timestamp": "2026-06-01 10:01:00", "price": 101.0, "quantity": 12, "trade_type": "TRADE"},
            {"timestamp": "2026-06-01 10:02:00", "price": 118.0, "quantity": 8, "trade_type": "TRADE"},  # +18% shock
            {"timestamp": "2026-06-01 10:03:00", "price": 100.5, "quantity": 11, "trade_type": "TRADE"},
        ])

        engine = AnomalyDetectionEngine()

        # Test normal
        res_normal = engine.detect_intraday_shocks(normal_ticks, daily_modal_price=100.0)
        self.assertFalse(res_normal["is_shock"])
        self.assertEqual(res_normal["severity"], "None")

        # Test shock
        res_shock = engine.detect_intraday_shocks(shock_ticks, daily_modal_price=100.0)
        self.assertTrue(res_shock["is_shock"])
        self.assertIn(res_shock["severity"], ["Medium", "High", "Critical"])
        self.assertGreater(len(res_shock["shocks"]), 0)
        self.assertEqual(res_shock["shocks"][0]["price"], 118.0)

    def test_04_realtime_risk_augmentation(self):
        """Test risk score augmentation logic with intraday shocks."""
        risk_engine = MarketRiskEngine()

        base_risk = {
            "risk_score": 40,
            "risk_level": "Moderate",
            "regime": "Stable",
            "breakdown": {"Volatility": 20, "Market Shocks": 10, "News Sentiment": 5, "Supply/Weather": 5},
            "explanation_tags": ["Normal Volatility"]
        }

        # Case 1: No intraday shock
        no_shock = {"is_shock": False, "severity": "None", "shocks": []}
        res_no_shock = risk_engine.calculate_realtime_risk(base_risk, no_shock)
        self.assertEqual(res_no_shock["risk_score"], 40)
        self.assertEqual(res_no_shock["intraday_risk_delta"], 0)

        # Case 2: Critical intraday shock (+20)
        critical_shock = {"is_shock": True, "severity": "Critical", "shocks": [{"price": 120.0}]}
        res_critical = risk_engine.calculate_realtime_risk(base_risk, critical_shock)
        self.assertEqual(res_critical["risk_score"], 60)
        self.assertEqual(res_critical["intraday_risk_delta"], 20)
        self.assertEqual(res_critical["risk_level"], "High")
        self.assertIn("Intraday Shocks", res_critical["breakdown"])
        self.assertEqual(res_critical["breakdown"]["Intraday Shocks"], 20)


if __name__ == "__main__":
    unittest.main()
