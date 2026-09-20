"""
tests/test_auth_manager.py
===========================
Tests for AuthAgent security hardening.

Verifies that:
- DEFAULT_ADMIN_PASSWORD is gracefully handled when missing.
- A random fallback is generated and set in os.environ.
- AuthAgent skips validation in test environments.
- AuthAgent initialises cleanly when the env var is present.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAuthManagerSecurity:
    """Security hardening tests for AuthAgent."""

    def test_fallback_when_password_missing_in_development(self, monkeypatch):
        """AuthAgent must generate a random fallback password when
        DEFAULT_ADMIN_PASSWORD is unset and AGRIINTEL_ENV is 'development'."""
        monkeypatch.setenv("AGRIINTEL_ENV", "development")
        monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

        from agents.auth_manager import AuthAgent

        # Should NOT raise — generates a random fallback instead
        AuthAgent._validate_admin_credentials()

        # A fallback password should now be set in os.environ
        assert os.environ.get("DEFAULT_ADMIN_PASSWORD"), \
            "Expected a fallback password to be set in os.environ"

    def test_fallback_when_password_missing_in_production(self, monkeypatch):
        """AuthAgent must generate a random fallback password when
        DEFAULT_ADMIN_PASSWORD is unset and AGRIINTEL_ENV is 'production'."""
        monkeypatch.setenv("AGRIINTEL_ENV", "production")
        monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

        from agents.auth_manager import AuthAgent

        # Should NOT raise — generates a random fallback instead
        AuthAgent._validate_admin_credentials()

        # A fallback password should now be set in os.environ
        assert os.environ.get("DEFAULT_ADMIN_PASSWORD"), \
            "Expected a fallback password to be set in os.environ"

    def test_no_raise_in_test_environment(self, monkeypatch):
        """AuthAgent must NOT raise when AGRIINTEL_ENV is 'test',
        regardless of whether DEFAULT_ADMIN_PASSWORD is set."""
        monkeypatch.setenv("AGRIINTEL_ENV", "test")
        monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

        from agents.auth_manager import AuthAgent

        # Should not raise
        AuthAgent._validate_admin_credentials()

    def test_no_raise_when_password_set(self, monkeypatch):
        """AuthAgent must NOT raise when DEFAULT_ADMIN_PASSWORD is present,
        even in development."""
        monkeypatch.setenv("AGRIINTEL_ENV", "development")
        monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "SecurePassword123!")

        from agents.auth_manager import AuthAgent

        # Should not raise
        AuthAgent._validate_admin_credentials()

    def test_existing_password_not_overwritten(self, monkeypatch):
        """When DEFAULT_ADMIN_PASSWORD is already set, the fallback
        should NOT overwrite it."""
        monkeypatch.setenv("AGRIINTEL_ENV", "development")
        monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "MyRealPassword!")

        from agents.auth_manager import AuthAgent

        AuthAgent._validate_admin_credentials()

        assert os.environ["DEFAULT_ADMIN_PASSWORD"] == "MyRealPassword!"
