# 🌾 AgriIntel.in: National Unified Agricultural Intelligence Stack

**AgriIntel.in** is an authoritative, end-to-end **Conversational Intelligence & Market Analytics ecosystem** designed to revolutionize the agricultural lifecycle in India. It serves as a single source of truth for farmers, policymakers, and institutional stakeholders through a speech-first regional language interface.

[![CI — Test, Lint & Security](https://github.com/Tick2003/AgriIntel-Live/actions/workflows/ci.yml/badge.svg)](https://github.com/Tick2003/AgriIntel-Live/actions/workflows/ci.yml)
[![Daily Market Data Update](https://github.com/Tick2003/AgriIntel-Live/actions/workflows/daily_update.yml/badge.svg)](https://github.com/Tick2003/AgriIntel-Live/actions/workflows/daily_update.yml)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agriintel-live.streamlit.app/)

---

## 🏛️ The National Intelligence Stack

AgriIntel.in consolidates 20+ specialized AI agents into a unified, high-performance architecture:

### 🎙️ 1. Conversational Access Stack (Voice Gateway)
*   **Telephony-Ready Infrastructure**: Real-time voice interaction layer for standard phone calls (Hindi and English).
*   **Multi-Turn Dialogue Management**: Sustained conversational context across sessions.
*   **Telecom Mapping**: Automatic region-aware language detection via carrier circle mapping.

### 🧠 2. RACE Forecasting & Real-Time Trading Stack
*   **RACE Forecaster (Regime-Adaptive Competitive Ensemble)**: Patent-grade engine combining HMM (Hidden Markov Model) regime classification (Stable/Volatile/Crisis) with dynamic inverse-MAPE weighted ensembles across **XGBoost**, **LightGBM**, and **CatBoost**.
*   **High-Frequency Intraday Simulation Engine**: Daemon-driven simulator generating live eNAM bid/ask and completed trades every 2-3s, biased by weather stress and news sentiment.
*   **Bloomberg-Style Trading Desk UI**: Streamlit page with non-blocking `@st.fragment` rendering live order books, scrolling trade tickers, and Plotly intraday charts.
*   **3σ Shock Sentinel & Risk Augmentation**: Statistical sentinel flagging ticks exceeding 3σ deviation, instantly augmenting baseline risk score (+20 pts) in <5 seconds.

### 🚛 3. Supply Chain & Logistics Stack
*   **Spatial Arbitrage Corridor Engine**: Maps mandi networks using Dijkstra shortest-path algorithms to optimize route profits (factoring tolls, distance, and transport costs).
*   **Computer Vision Grading**: Visual produce scanning returning objective commercial grades (Grade A/B/C) with automatic pricing recommendations.
*   **Agri-Credit & B2B Matchmaking**: Farmers/exporters matchmaking and creditworthiness scoring.
*   **Smart Resource Planning**: Crop rotation (Simplex Algorithm) and inventory level optimization (EOQ).

---

## 📖 Essential Documentation

*   📜 **[Technical Architecture](ARCHITECTURE.md)** — Deep-dive into the Multi-Agent System (MMAS) and mathematical foundations.
*   📖 **[The AgriIntel.in Story](PRODUCT_STORY.md)** — A comprehensive, layman-friendly guide to every feature.
*   📋 **[Changelog](CHANGELOG.md)** — Release history and notable changes.
*   🔬 **[Reproduce Results](REPRODUCE.md)** — Step-by-step guide to reproduce forecast results from scratch.

---

## 📦 Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Tick2003/AgriIntel-Live.git
cd AgriIntel-Live
```

### 2. Create & Activate a Virtual Environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

### 3. Install Dependencies
All production dependencies are **pinned to exact versions** in `requirements.txt` for reproducible installs:
```bash
pip install -r requirements.txt
```

Install dev/test extras:
```bash
pip install -e ".[dev]"
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
# Then edit .env — at minimum set DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD
```

Key variables (see [.env.example](.env.example) for the full list):

| Variable | Required | Description |
|---|---|---|
| `DEFAULT_ADMIN_EMAIL` | ✅ | Admin account email for first-run bootstrap |
| `DEFAULT_ADMIN_PASSWORD` | ✅ | Admin account password (≥12 chars) |
| `DATA_GOV_IN_API_KEY` | Optional | data.gov.in API key for real price data |
| `OWM_API_KEY` | Optional | OpenWeatherMap API key for live weather |
| `AGRIINTEL_ENV` | Optional | `development` / `staging` / `production` (default: `development`) |

### 5. Run the App
```bash
# Streamlit UI
streamlit run app/main.py

# FastAPI backend
uvicorn api_server:app --reload
```

---

## 🧪 Running Tests

### Quick (offline, no network required)
```bash
pytest -m "not integration" -v --tb=short
```

### With coverage report
```bash
pytest -m "not integration" \
  --cov=app --cov=agents --cov=database --cov=etl --cov=cv --cov=utils \
  --cov-report=term-missing \
  --cov-fail-under=50
```

### Full suite (includes integration tests that hit real APIs)
```bash
pytest -v
```

### Lint & security check
```bash
ruff check .
bandit -c pyproject.toml -r agents/ etl/ database/ utils/ cv/ api_server.py -ll
```

> **CI** enforces `pytest -m "not integration"` + `ruff check .` + `bandit` on every push and pull request via `.github/workflows/ci.yml`.

---

## 🔄 Autonomous Data Pipeline

**AgriIntel.in** features a fully autonomous, self-healing data pipeline that runs daily at 00:00 UTC via GitHub Actions:

```
GitHub Actions (00:00 UTC daily)
    └── etl/data_loader.py --skip-swarm
            ├── Fetch commodity prices  (data.gov.in → Agmarknet scraper → simulation fallback)
            ├── DataReliabilityAgent    (completeness + plausibility + duplicate checks)
            ├── Fetch agricultural news (Google News RSS)
            ├── Fetch weather           (Open-Meteo / OpenWeatherMap for 12 mandis)
            └── Export data/market_prices.csv  (auto-committed back to repo)
```

*   **Cascading Price Sources**: Real API → Agmarknet scraper → enhanced simulation fallback — never fails silently.
*   **Data Quality Gate**: `DataReliabilityAgent` validates every batch before it reaches the production database, logging `MISSING_DATA`, `OUTLIER_SHOCK`, and `DUPLICATE` issues to an audit table.
*   **Model Accuracy Tracking**: Continuous MAPE/RMSE calculation for automated retraining triggers.
*   **Experiment Traceability**: Every RACE forecast run writes a JSON manifest to `data/run_manifests/` containing model weights, regime, RMSE, and metadata.
*   **CI Mode vs Full Mode**: `--skip-swarm` runs a lightweight data-only refresh (used in the daily CI job). Omit the flag for the full Intelligence Swarm (Forecast + Risk + Decision agents).

To trigger a manual data refresh locally:
```bash
# Lightweight — data only, no ML training (~30 seconds)
python etl/data_loader.py --skip-swarm

# Full update — data + ML swarm (~5 minutes)
python etl/data_loader.py
```

---

*Intelligence for the Soil. Power for the Farmer.*
