# AgriIntel System Architecture & Documentation

## 📖 Introduction
AgriIntel is a live simulated market intelligence dashboard for agricultural commodities in India. It leverages a multi-agent system to process real-time (simulated) data, forecast prices using machine learning, detect market shocks, and assess risk.

---

## 🏗️ System Architecture

The following diagram illustrates the high-level data flow and component interaction within the AgriIntel system.

```mermaid
graph TD
    User((User)) -->|Interacts| UI(Streamlit Dashboard)
    
    subgraph "Application Layer (app/)"
        UI -->|Selects Commodity/Region| Controller(main.py)
    end
    
    subgraph "Data Layer (database/ & etl/)"
        Controller -->|Request Data| DB[(SQLite Database)]
        ETL(Simulated ETL Process) -->|Writes| DB
    end
    
    subgraph "Agent Layer (agents/)"
        Controller -->|1. Check Logs| Ag1(DataHealthAgent)
        Controller -->|2. Generate Preds| Ag2(ForecastingAgent)
        Controller -->|3. Monitor| Ag3(AnomalyDetectionEngine)
        Controller -->|4. Assess Risk| Ag4(MarketRiskEngine)
        Controller -->|5. Explain| Ag5(AIExplanationAgent)
        
        Ag2 -->|Forecasts| Ag3
        Ag3 -->|Shock Flags| Ag4
        Ag4 -->|Risk Score| Ag5
    end
    
    Ag5 -->|Natural Language Report| UI
    Ag2 -->|Chart Data| UI
```

---

## 🔌 Module Breakdown (Tip to Toe)

### 1. Application Layer (`app/`)
This layer handles the visual presentation and user inputs.

#### `app/main.py`
The entry point of the Streamlit application.
*   **Initialization**: Configures the page layout, title, and loads custom CSS.
*   **Dependencies**: Imports all Agents and Utils.
*   **State Management & Performance**: Uses `@st.cache_data(ttl=3600)` to cache expensive operations (Data Loading, Model Training, Risk Scoring) for 1 hour, ensuring instant page navigation.
*   **Execution Loop**:
    1.  **Sidebar**: Collects user preference (Commodity, Mandi).
    2.  **Data Fetch**: Calls `get_live_data` (Cached) to retrieve historical traces.
    3.  **Agent Chain**: Sequentially calls agents (most are Cached):
        *   `health` -> `forecast` -> `shock` -> `risk` -> `explain`
    4.  **UI Routing**: Switches between views ("Market Overview", "Price Forecast", etc.) based on sidebar selection.

#### `app/utils.py`
Helper utilities for the frontend.
*   `get_db_options()`: Queries `market_prices` table for distinct Commodities and Mandis to populate dropdowns.
*   `get_live_data(commodity, mandi)`: Retrievals sorted time-series data. Includes intelligent fallbacks (dummy data) if the database is empty.
*   `load_css()`: Injectable CSS for styling the dashboard (custom colors, card aesthetics).

---

### 2. Agent Layer (`agents/`)
The "Brains" of the application. Each agent is a specialized class with a specific responsibility.

#### `agents/forecast_execution.py` (`ForecastingAgent`)
**Purpose**: Predict future prices (30 days out) using a Robust Hybrid ML approach.
*   **Algorithm**: **Trend Decomposition (Linear Regression) + Residual Modeling (XGBoost)**.
*   **Key Features**:
    *   **Trend + Residual Strategy**: Solves the "Flat-line" problem of tree-based models.
        1.  **Detrend**: Fits a linear trend to the price history to capture long-term direction.
        2.  **Residuals**: Trains XGBoost on the *residuals* (Price - Trend) to capture volatility and seasonality.
        3.  **Recombine**: Final Forecast = Projected Trend + Predicted Residuals.
    *   **Recursive Forecasting**: Uses a recursive window strategy where future predictions become inputs for subsequent steps.
    *   **Dynamic Confidence Intervals**: Calculates RMSE on a hidden validation set and scales uncertainty over time (Confidence Interval = Forecast +/- 1.96 * RMSE * sqrt(t)).

#### `agents/risk_scoring.py` (`MarketRiskEngine`)
**Purpose**: Quantify market stability.
*   **Algorithm**: Weighted Scoring System.
*   **Inputs**: Shock severity, Forecast volatility, Historical volatility.
*   **Scoring Logic**:
    *   Base Score: 0
    *   **+50**: High Severity Shock detected.
    *   **+20**: Medium Severity Shock / High Forecast Uncertainty.
    *   **+30**: High Daily Volatility (>2%).
*   **Output**: A clean 0-100 score and a "Risk Regime" label (Stable vs. Volatile).

#### `agents/shock_monitoring.py` (`AnomalyDetectionEngine`)
**Purpose**: Detect sudden, abnormal market moves.
*   **Algorithm**: Threshold-based Anomaly Detection.
*   **Thresholds**:
    *   **>15% Change**: "High" Severity.
    *   **>5% Change**: "Medium" Severity.
    *   **Else**: Normal.
*   **Usage**: Prevents users from being blindsided by sudden crashes or spikes.

#### `agents/data_health.py` (`DataHealthAgent`)
**Purpose**: Ensure trust in the underlying data.
*   **Checks**:
    1.  **Completeness**: Are there missing dates in the timeline?
    2.  **Validity**: Are there '0' price values?
*   **Output**: Renders a status badge (OK/Critical) on the dashboard (currently hidden in main view but calculated).

#### `agents/explanation_report.py` (`AIExplanationAgent`)
**Purpose**: translate numbers into words.
*   **Function**: Takes the outputs of all other agents (Risk Score, Shock Status, Forecast Trend) and fills a natural language template.
*   **Future**: Designed to be the integration point for LLM (Gemini/GPT) APIs for generated market commentary.

---

### 3. Data & ETL Layer

#### `database/db_manager.py`
Handles all SQLite interactions.
*   **File**: `agri_intel.db`
*   **Schema**:
    *   **`market_prices`**: `date` (TEXT), `commodity` (TEXT), `mandi` (TEXT), `price_modal` (REAL), `arrival` (REAL).
    *   **`news_alerts`**: `date`, `title`, `source`, `sentiment`.
    *   **`weather_logs`**: `date`, `region`, `temperature`, `rainfall`.
    *   **`signal_logs`**: Stores historical signals (`date`, `signal`, `price_at_signal`, `price_after_7d`, `profitability_status`) for the Win Rate tracker.

#### `etl/data_loader.py`
The simulation engine.
*   **`seed_historical_data()`**: Generates 90 days of realistic "Random Walk" price history for multiple commodities/mandis. Used to initialize the app.
*   **`fetch_real_weather()`**: Connects to the **Open-Meteo API** to fetch *actual* live weather for specific Mandi coordinates (Lat/Lon mapped).
*   **`fetch_mandi_prices_simulated()`**: Generates daily price updates with realistic noise to simulate a live market feed in the absence of a paid Agmarknet API subscription.

---

## 🛠️ Configuration & Setup

1.  **Prerequisites**: Python 3.8+
2.  **Dependencies**: Listed in `requirements.txt` (Streamlit, Pandas, Plotly, XGBoost).
3.  **First Run**:
    ```bash
    # 1. Install
    pip install -r requirements.txt
    
    # 2. Seed Database (Vital for first run)
    python etl/data_loader.py seed
    
    # 3. Launch
    streamlit run app/main.py
    ```
