# Changelog

All notable changes to AgriIntel.in are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- MLflow experiment tracking for every RACE forecast run (params, metrics, regime tags)
- `REPRODUCE.md` — step-by-step guide to reproduce forecast results from scratch
- `Dockerfile` — multi-stage build with non-root user and healthcheck
- `docker-compose.yml` — Streamlit UI + FastAPI backend services with named volumes
- `.pre-commit-config.yaml` — ruff lint/format, file hygiene, bandit security hooks
- `Makefile` — developer shortcuts (`make test`, `make coverage`, `make docker-up`, etc.)
- Bandit security scanning step in CI pipeline
- Codecov coverage upload in CI pipeline

### Changed
- `database/db_manager.py` — completed backward-compatible shim; all 30 functions now re-exported from domain sub-modules (`connection`, `prices`, `auth_db`, `signals`, `forecasts`, `etl_db`, `system`, `realtime`)
- `etl/data_loader.py` — replaced last `print()` with `logger.warning()` (all ETL modules now 100% structured logging)

### Fixed
- All 34 test failures caused by empty `db_manager.py` shim after database split

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

[Unreleased]: https://github.com/Tick2003/AgriIntel-Live/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/Tick2003/AgriIntel-Live/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Tick2003/AgriIntel-Live/releases/tag/v1.0.0
