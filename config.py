"""
AgriIntel — Centralized Configuration
=======================================
All application settings in one place.
Uses environment variables with sensible dev defaults.

Hardened: env-var parsing is crash-proof (bad integers fall back
to defaults with a warning instead of a ValueError).
"""

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


def _safe_int(env_key: str, default: int) -> int:
    """Read an integer from an env var without crashing on garbage values."""
    raw = os.environ.get(env_key, "")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "Invalid integer for env var %s=%r, using default %d",
            env_key, raw, default,
        )
        return default


def _safe_bool(env_key: str, default: bool = False) -> bool:
    """Read a boolean from an env var (true/1/yes → True, else False)."""
    raw = os.environ.get(env_key, "")
    if not raw:
        return default
    return raw.strip().lower() in ("true", "1", "yes")


@dataclass
class DatabaseConfig:
    """Database configuration."""
    name: str = ""
    # For PostgreSQL migration:
    url: str = ""
    pool_size: int = 5
    max_overflow: int = 10

    def __post_init__(self) -> None:
        self.name = self.name or os.environ.get("AGRIINTEL_DB_NAME", "agri_intel.db")
        self.url = self.url or os.environ.get("DATABASE_URL", "")
        self.pool_size = _safe_int("DB_POOL_SIZE", self.pool_size)
        self.max_overflow = _safe_int("DB_MAX_OVERFLOW", self.max_overflow)


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    api_key: str = ""
    secret_key: str = ""
    session_timeout_hours: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    # Default admin setup (only used on first run if DB is empty)
    default_admin_email: str = ""
    default_admin_password: str = ""

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("AGRIINTEL_API_KEY", "")
        self.secret_key = self.secret_key or os.environ.get("AGRIINTEL_SECRET_KEY", "")
        # Deterministic fallback for dev — production MUST set the env var.
        # Using a fixed dev-only key avoids session invalidation on restart.
        if not self.secret_key:
            self.secret_key = os.urandom(32).hex()
            logger.debug(
                "AGRIINTEL_SECRET_KEY not set — generated ephemeral key. "
                "Sessions will not survive restarts."
            )
        self.session_timeout_hours = _safe_int("SESSION_TIMEOUT_HOURS", self.session_timeout_hours)
        self.max_login_attempts = _safe_int("MAX_LOGIN_ATTEMPTS", self.max_login_attempts)
        self.lockout_duration_minutes = _safe_int("LOCKOUT_DURATION_MINUTES", self.lockout_duration_minutes)
        self.default_admin_email = self.default_admin_email or os.environ.get("DEFAULT_ADMIN_EMAIL", "")
        self.default_admin_password = self.default_admin_password or os.environ.get("DEFAULT_ADMIN_PASSWORD", "")


@dataclass
class ETLConfig:
    """ETL pipeline configuration."""
    data_gov_api_key: str = ""
    owm_api_key: str = ""
    staleness_threshold_hours: int = 6
    lock_file: str = ".update.lock"
    max_swarm_pairs: int = 100
    request_timeout: int = 30

    def __post_init__(self) -> None:
        self.data_gov_api_key = self.data_gov_api_key or os.environ.get("DATA_GOV_IN_API_KEY", "")
        self.owm_api_key = self.owm_api_key or os.environ.get("OWM_API_KEY", "")
        self.staleness_threshold_hours = _safe_int("STALENESS_THRESHOLD_HOURS", self.staleness_threshold_hours)
        self.lock_file = self.lock_file if self.lock_file != ".update.lock" else os.environ.get("UPDATE_LOCK_FILE", ".update.lock")
        self.max_swarm_pairs = _safe_int("MAX_SWARM_PAIRS", self.max_swarm_pairs)
        self.request_timeout = _safe_int("REQUEST_TIMEOUT", self.request_timeout)


@dataclass
class AppConfig:
    """General application configuration."""
    environment: str = ""
    debug: bool = False
    log_level: str = "INFO"
    api_base_url: str = "http://localhost:8000"
    cache_ttl: int = 600

    # Data retention
    intraday_retention_hours: int = 72
    log_retention_days: int = 90

    def __post_init__(self) -> None:
        self.environment = self.environment or os.environ.get("AGRIINTEL_ENV", "development")
        self.debug = self.debug or _safe_bool("AGRIINTEL_DEBUG", False)
        self.log_level = self.log_level if self.log_level != "INFO" else os.environ.get("LOG_LEVEL", "INFO")
        self.api_base_url = (
            self.api_base_url
            if self.api_base_url != "http://localhost:8000"
            else os.environ.get("API_BASE_URL", "http://localhost:8000")
        )
        self.cache_ttl = _safe_int("CACHE_TTL", self.cache_ttl)
        self.intraday_retention_hours = _safe_int("INTRADAY_RETENTION_HOURS", self.intraday_retention_hours)
        self.log_retention_days = _safe_int("LOG_RETENTION_DAYS", self.log_retention_days)

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
