# Reproducing AgriIntel Forecast Results from Scratch

This guide walks you through a clean end-to-end reproduction of a RACE forecast run — from an empty environment to verified results — with no external data dependencies.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | ≥ 3.10 |
| Git | ≥ 2.40 |
| (Optional) Docker | ≥ 24 |

---

## Step 1 — Clone & Set Up Environment

```bash
git clone https://github.com/Tick2003/AgriIntel-Live.git
cd AgriIntel-Live

# Create isolated virtual environment
python -m venv .venv

# Activate
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# Install all pinned dependencies (deterministic)
pip install -r requirements.txt
pip install -e ".[dev]"
```

All production dependencies are **pinned to exact versions** in `requirements.txt`, ensuring byte-for-byte reproducible installs.

---

## Step 2 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
AGRIINTEL_ENV=development
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=your_secure_password_here
```

> For offline reproduction (no real API keys needed), leave `DATA_GOV_IN_API_KEY` and `OWM_API_KEY` blank — the system will use simulated data.

---

## Step 3 — Initialize the Database

```bash
python -c "from database.db_manager import init_db; init_db()"
```

This creates `agri_intel.db` with all tables and, if `data/market_prices.csv` exists, restores historical price data.

---

## Step 4 — Run the Test Suite (Verify Environment)

```bash
# Fast offline suite — should pass 112/112
pytest -m "not integration" -v --tb=short
```

If all 112 tests pass, the environment is correctly set up.

---

## Step 5 — Trigger a RACE Forecast Run

```python
import pandas as pd
from agents.forecast_engine.ensemble import RACEForecaster

# Load sample price data (uses simulation if DB is empty)
from etl.agmarknet_scraper import get_simulated_prices
prices = get_simulated_prices("Onion", "Azadpur", days=90)

# Initialise the RACE engine
forecaster = RACEForecaster(commodity="Onion", mandi="Azadpur")

# Fit and forecast — this logs to MLflow automatically
forecast_df, manifest = forecaster.fit_and_forecast(prices, horizon=7)
print(forecast_df)
print("Run manifest:", manifest)
```

---

## Step 6 — Inspect MLflow Run Logs

Every RACE forecast run is automatically tracked with MLflow:

```bash
# Launch MLflow UI (reads from local ./mlruns directory)
mlflow ui --port 5000
# Open http://localhost:5000
```

You will see:
- **Parameters**: `commodity`, `mandi`, `horizon`, `n_samples`, `n_features`
- **Metrics**: `rmse_xgb`, `rmse_lgb`, `rmse_cat`, `regime_confidence`, `ensemble_rmse`
- **Tags**: `regime` (STABLE / VOLATILE / CRISIS), `model_version`
- **Artifacts**: `model_weights.json` (XGB/LGB/CAT weights)

---

## Step 7 — Inspect JSON Run Manifests

Each run also writes a JSON manifest to `data/run_manifests/`:

```bash
ls data/run_manifests/
# e.g.: Onion_Azadpur_20260901_143022.json

cat data/run_manifests/Onion_Azadpur_20260901_143022.json
```

Manifest contains: `commodity`, `mandi`, `generated_at`, `regime`, `regime_confidence`, `model_weights`, `cv_mapes`, `ensemble_rmse`, `horizon_days`, `n_training_samples`.

---

## Reproducibility Guarantees

| Component | Method |
|---|---|
| Dependencies | Exact-version `requirements.txt` |
| Random seeds | XGBoost `seed=42`, LightGBM `random_state=42`, CatBoost `random_seed=42` |
| HMM init | Fixed `random_state=42` in hmmlearn |
| Database | `init_db()` + `data/market_prices.csv` CSV restore |
| Experiment logs | MLflow file-system backend (`./mlruns/`) |
| Run manifests | JSON files in `data/run_manifests/` |

---

## Docker Reproduction (Zero-Setup)

```bash
# Build the image
docker build -t agriintel:latest .

# Run with your .env file
docker-compose up -d

# View MLflow UI (port forwarded)
open http://localhost:5000
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `RuntimeError: DEFAULT_ADMIN_PASSWORD not set` | Add `DEFAULT_ADMIN_PASSWORD` to `.env` or set `AGRIINTEL_ENV=test` |
| `ImportError: No module named 'mlflow'` | Run `pip install -r requirements.txt` again |
| Tests hang at collection | The `--cov` flag with heavy ML imports can slow collection; run without `--cov` first |
| `data/market_prices.csv` not found | Normal — the system uses simulated prices; real data requires API keys |
