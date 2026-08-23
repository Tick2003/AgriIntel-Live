"""
AgriIntel — Centralized Configuration
=======================================
All application settings in one place.
Uses environment variables with sensible dev defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration."""
    name: str = os.environ.get("AGRIINTEL_DB_NAME", "agri_intel.db")
    # For PostgreSQL migration:
    url: str = os.environ.get("DATABASE_URL", "")
    pool_size: int = int(os.environ.get("DB_POOL_SIZE", "5"))
    max_overflow: int = int(os.environ.get("DB_MAX_OVERFLOW", "10"))


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    api_key: str = os.environ.get("AGRIINTEL_API_KEY", "")
    secret_key: str = os.environ.get("AGRIINTEL_SECRET_KEY", os.urandom(32).hex())
    session_timeout_hours: int = int(os.environ.get("SESSION_TIMEOUT_HOURS", "8"))
    max_login_attempts: int = int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5"))
    lockout_duration_minutes: int = int(os.environ.get("LOCKOUT_DURATION_MINUTES", "15"))
    # Default admin setup (only used on first run if DB is empty)
    default_admin_email: str = os.environ.get("DEFAULT_ADMIN_EMAIL", "")
    default_admin_password: str = os.environ.get("DEFAULT_ADMIN_PASSWORD", "")


@dataclass
class ETLConfig:
    """ETL pipeline configuration."""
    data_gov_api_key: str = os.environ.get("DATA_GOV_IN_API_KEY", "")
    owm_api_key: str = os.environ.get("OWM_API_KEY", "")
    staleness_threshold_hours: int = int(os.environ.get("STALENESS_THRESHOLD_HOURS", "6"))
    lock_file: str = os.environ.get("UPDATE_LOCK_FILE", ".update.lock")
    max_swarm_pairs: int = int(os.environ.get("MAX_SWARM_PAIRS", "100"))
    request_timeout: int = int(os.environ.get("REQUEST_TIMEOUT", "30"))


@dataclass
class AppConfig:
    """General application configuration."""
    environment: str = os.environ.get("AGRIINTEL_ENV", "development")
    debug: bool = os.environ.get("AGRIINTEL_DEBUG", "false").lower() == "true"
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    api_base_url: str = os.environ.get("API_BASE_URL", "http://localhost:8000")
    cache_ttl: int = int(os.environ.get("CACHE_TTL", "600"))
    
    # Data retention
    intraday_retention_hours: int = int(os.environ.get("INTRADAY_RETENTION_HOURS", "72"))
    log_retention_days: int = int(os.environ.get("LOG_RETENTION_DAYS", "90"))

    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@dataclass
class Settings:
    """Root settings container."""
    app: AppConfig = field(default_factory=AppConfig)
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    etl: ETLConfig = field(default_factory=ETLConfig)


# Module-level singleton
settings = Settings()
