"""
tests/test_auth_manager.py
===========================
Tests for AuthAgent security hardening.

Verifies that:
- DEFAULT_ADMIN_PASSWORD is required in non-test environments.
- AuthAgent raises RuntimeError at startup when the env var is absent.
- AuthAgent initialises cleanly when the env var is present.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAuthManagerSecurity:
    """Security hardening tests for AuthAgent."""

    def test_raises_when_password_missing_in_development(self, monkeypatch):
        """AuthAgent must raise RuntimeError when DEFAULT_ADMIN_PASSWORD is unset
        and AGRIINTEL_ENV is 'development'."""
        monkeypatch.setenv("AGRIINTEL_ENV", "development")
        monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

        from agents.auth_manager import AuthAgent

        with pytest.raises(RuntimeError, match="DEFAULT_ADMIN_PASSWORD"):
            AuthAgent._validate_admin_credentials()

    def test_raises_when_password_missing_in_production(self, monkeypatch):
        """AuthAgent must raise RuntimeError when DEFAULT_ADMIN_PASSWORD is unset
        and AGRIINTEL_ENV is 'production'."""
        monkeypatch.setenv("AGRIINTEL_ENV", "production")
        monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

        from agents.auth_manager import AuthAgent

        with pytest.raises(RuntimeError, match="DEFAULT_ADMIN_PASSWORD"):
            AuthAgent._validate_admin_credentials()

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

    def test_error_message_is_helpful(self, monkeypatch):
        """Error message should tell the developer what to do."""
        monkeypatch.setenv("AGRIINTEL_ENV", "development")
        monkeypatch.delenv("DEFAULT_ADMIN_PASSWORD", raising=False)

        from agents.auth_manager import AuthAgent

        with pytest.raises(RuntimeError) as exc_info:
            AuthAgent._validate_admin_credentials()

        error_text = str(exc_info.value)
        assert ".env" in error_text or ".env.example" in error_text
