"""
Unit Tests for API Server
===========================
Tests all endpoints, auth, and error handling using FastAPI TestClient.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test API key before importing app
os.environ["AGRIINTEL_API_KEY"] = "test-api-key-12345"
os.environ["AGRIINTEL_DB_NAME"] = "test_agri_intel.db"
os.environ["AGRIINTEL_ENV"] = "test"

from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

VALID_HEADERS = {"x-api-key": "test-api-key-12345"}
INVALID_HEADERS = {"x-api-key": "wrong-key"}


class TestPublicEndpoints:
    """Tests for unauthenticated endpoints."""

    def test_home(self):
        """Test root endpoint."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "AgriIntel" in data["message"]

    def test_health_check(self):
        """Test health endpoint returns DB status."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "db" in data
        assert data["status"] in ("ok", "degraded")


class TestAuthentication:
    """Tests for API key authentication."""

    def test_missing_api_key(self):
        """Test that missing API key returns 422."""
        resp = client.get("/v1/price/Onion/Azadpur")
        assert resp.status_code == 422  # Missing header

    def test_invalid_api_key(self):
        """Test that invalid API key returns 403."""
        resp = client.get("/v1/price/Onion/Azadpur", headers=INVALID_HEADERS)
        assert resp.status_code == 403

    def test_valid_api_key(self):
        """Test that valid API key allows access."""
        resp = client.get("/v1/price/Onion/Azadpur", headers=VALID_HEADERS)
        # May be 404 (no data) but should NOT be 403
        assert resp.status_code in (200, 404)


class TestPriceEndpoint:
    """Tests for /v1/price/{commodity}/{mandi}."""

    def test_nonexistent_commodity(self):
        """Test 404 for non-existent commodity."""
        resp = client.get("/v1/price/NonExistent/Azadpur", headers=VALID_HEADERS)
        assert resp.status_code == 404

    def test_nonexistent_mandi(self):
        """Test 404 for non-existent mandi."""
        resp = client.get("/v1/price/Onion/FakeMandi123", headers=VALID_HEADERS)
        assert resp.status_code == 404


class TestRiskEndpoint:
    """Tests for /v1/risk/{commodity}/{mandi}."""

    def test_risk_nonexistent(self):
        """Test 404 for non-existent data."""
        resp = client.get("/v1/risk/NonExistent/FakeMandi", headers=VALID_HEADERS)
        assert resp.status_code == 404


class TestArbitrageEndpoint:
    """Tests for /v1/arbitrage/{commodity}/{mandi}."""

    def test_arbitrage_nonexistent(self):
        """Test 404 for non-existent commodity."""
        resp = client.get("/v1/arbitrage/NonExistent/FakeMandi", headers=VALID_HEADERS)
        assert resp.status_code == 404


class TestVoiceEndpoints:
    """Tests for voice interaction endpoints."""

    def test_voice_start(self):
        """Test voice session start."""
        resp = client.post(
            "/v1/voice/start",
            json={"phone_number": "9820012345"},
            headers=VALID_HEADERS,
        )
        # May be 200 or 503 (if voice deps not installed)
        assert resp.status_code in (200, 503)

    def test_voice_interact_invalid_session(self):
        """Test voice interaction with invalid session."""
        resp = client.post(
            "/v1/voice/interact",
            json={"session_id": "fake-session", "text_input": "hello"},
            headers=VALID_HEADERS,
        )
        # Should return 200 (with error response) or 503
        assert resp.status_code in (200, 503)
