# Changelog

All notable changes to AgriIntel.in are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [2.1.0] — 2026-09-15

### Added
- **`--skip-swarm` CLI flag** on `etl/data_loader.py` — enables lightweight data-only ETL runs without triggering the ML Intelligence Swarm. Used by the daily CI job to prevent resource exhaustion on GitHub-hosted runners.
- **`daily_update.yml` GitHub Actions workflow** — fully operational daily data pipeline running at 00:00 UTC. Fetches prices, news, and weather for all 12 tracked mandis and auto-commits `data/market_prices.csv` back to the repo.
- **`DataReliabilityAgent` in the ETL audit trail** — every batch now goes through completeness, plausibility (±50%/±300% price-change thresholds), and intra-batch deduplication checks before reaching the production database.
- MLflow experiment tracking for every RACE forecast run (params, metrics, regime tags)
- `REPRODUCE.md` — step-by-step guide to reproduce forecast results from scratch
- `Dockerfile` — multi-stage build with non-root user and healthcheck
- `docker-compose.yml` — Streamlit UI + FastAPI backend services with named volumes
- `.pre-commit-config.yaml` — ruff lint/format, file hygiene, bandit security hooks
- `Makefile` — developer shortcuts (`make test`, `make coverage`, `make docker-up`, etc.)
- Bandit security scanning step in CI pipeline
- Codecov coverage upload in CI pipeline

### Changed
- **Daily data pipeline (`daily_update.yml`)**: Updated to `actions/checkout@v4` / `actions/setup-python@v5` / `actions/cache@v4`. Pipeline is now green on every scheduled run.
- **`requirements-etl.txt`**: Added all transitive ETL dependencies (`statsmodels`, `joblib`, `beautifulsoup4`, `bcrypt`) that were missing and caused CI import failures.
- `database/db_manager.py` — completed backward-compatible shim; all 30 functions now re-exported from domain sub-modules (`connection`, `prices`, `auth_db`, `signals`, `forecasts`, `etl_db`, `system`, `realtime`)
- All logging in `etl/data_loader.py` and `agents/data_reliability.py` now uses structured `logging` module — no more `print()` statements anywhere in the pipeline

### Fixed
- GitHub Actions `daily_update` workflow previously failing with `ModuleNotFoundError` due to missing `bcrypt`, `statsmodels`, `joblib`, and `beautifulsoup4` in `requirements-etl.txt`
- GitHub Actions `daily_update` workflow previously failing with Node 20 deprecation warnings from outdated `@v3` action versions
- `etl/data_loader.py` swarm execution previously causing OOM / timeout on CI runners — resolved via `--skip-swarm` flag

---

## [2.0.0] — 2026-09-01

### Added
- **RACE Forecaster** — Regime-Adaptive Competitive Ensemble (XGBoost + LightGBM + CatBoost) with HMM regime classification
- **Bloomberg-Style Trading Desk** — Real-time eNAM order book, trade ticker, intraday Plotly charts
- **3σ Shock Sentinel** — flags price ticks exceeding 3-sigma deviation, augments risk score in < 5 seconds
- **Spatial Arbitrage Engine** — Dijkstra's shortest-path mandi network for route profit optimization
- **Computer Vision Grading** — Grade A/B/C produce classification module
- **Agri-Credit & B2B Matchmaking** — creditworthiness scoring and exporter matchmaking
- **FastAPI REST API** — `/v1/price`, `/v1/risk`, `/v1/arbitrage`, `/v1/voice/*` endpoints with API key auth
- **Multi-Agent System (MMAA)** — 20+ specialized AI agents in unified architecture
- **Run Manifests** — every RACE forecast writes JSON to `data/run_manifests/` (commodity, mandi, regime, weights, RMSE)
- Comprehensive CI pipeline with pytest, ruff, coverage enforcement
- All production dependencies pinned to exact versions in `requirements.txt`
- `.env.example` with 20+ documented environment variables
- `agents/reference_data.py` — canonical commodity/market lists (DRY across ETL modules)
- `app/theme/` — split `terminal_theme.py` god-file into `tokens.py` + `css.py`
- `tests/test_auth_manager.py` — security tests for credential validation
- `agents/auth_manager.py` — runtime guard: raises `RuntimeError` at startup if `DEFAULT_ADMIN_PASSWORD` unset

### Changed
- All `print()` statements across ETL pipeline replaced with structured `logging`
- Bare `except` blocks in `ensemble.py` replaced with typed `Exception as e` + `logger.warning()`
- Database refactored from monolith into domain-focused sub-modules

### Security
- Admin password required at runtime (`AGRIINTEL_ENV != test`)
- bcrypt password hashing for all user accounts
- API endpoints protected with API key authentication

---

## [1.0.0] — 2026-06-01

### Added
- Initial release: voice-first agricultural intelligence platform
- Price forecasting with XGBoost baseline model
- Market data ingestion from data.gov.in API and Agmarknet scraping
- Streamlit multi-page UI with terminal-style dark theme
- SQLite database for price, news, weather, and signal storage
- Hindi and English voice interface via gTTS and SpeechRecognition

[Unreleased]: https://github.com/Tick2003/AgriIntel-Live/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/Tick2003/AgriIntel-Live/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/Tick2003/AgriIntel-Live/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Tick2003/AgriIntel-Live/releases/tag/v1.0.0
