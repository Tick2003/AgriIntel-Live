# AgriIntel System Architecture & Documentation

## 📖 Introduction
AgriIntel is a live simulated market intelligence dashboard for agricultural commodities in India. It leverages a multi-agent system to process real-time (simulated) data, forecast prices using machine learning, detect market shocks, and assess risk.

**Version 2.0 (Full Scale)** now includes Computer Vision, Linguistics, Logistics Optimization, and a Business Layer (Fintech/B2B).

---

## 🏗️ System Architecture

The following diagram illustrates the high-level data flow and component interaction within the AgriIntel system.

```mermaid
graph TD
    User((User)) -->|Interacts| UI(Streamlit Dashboard)
    
    subgraph "Application Layer"
        UI -->|Selects Page| Controller(main.py)
        Controller -->|Voice/Text| Chat(Chatbot Interface)
    end
    
    subgraph "Data Layer"
        Controller -->|Request Data| DB[(SQLite Database)]
        ETL(Simulated ETL Process) -->|Writes| DB
        Weather(OpenWeatherMap API) -->|updates| DB
    end
    
    subgraph "Intelligence Swarm (agents/)"
        Controller -->|1. Check Health| Ag1(DataHealthAgent)
        Controller -->|2. Forecast| Ag2(ForecastingAgent)
        Controller -->|3. Risk/Shock| Ag3(RiskEngine)
        Controller -->|4. Explain| Ag4(IntelligenceCore)
        
        Controller -->|5. Optimize| Opt(OptimizationEngine)
        Controller -->|6. Transact| Biz(BusinessEngine)
        Controller -->|7. Translate| Lang(LanguageManager)
    end

    subgraph "Specialized Modules"
        Controller -->|Route Opt| Graph(MandiGraph)
        Controller -->|Image| CV(GradingModel)
    end
```

---

## 🔌 Module Breakdown (Tip to Toe)

### 1. Application Layer (`app/`)
This layer handles the visual presentation and user inputs.

#### `app/main.py`
The entry point.
*   **Initialization**: Configures page, loads CSS, and initializes the `agents` dictionary.
*   **Gatekeeper**: `AuthAgent` handles login/session.
*   **Navigation**:
    *   **Dashboard**: Market Overview, Forecast, Risk.
    *   **Tools**: Quality Grading (CV), Logistics (Graph), Advanced Planning (Simplex/EOQ).
    *   **Business**: B2B Marketplace, Fintech Services, Developer API.
    *   **Accessibility**: WhatsApp Bot (Chat), Language Toggle (En/Hi/Or).
*   **Migration**: Explicitly calls `db_manager.init_db()` at startup to ensure schema consistency.

#### `app/utils.py`
Helper utilities.
*   `load_css()`: Custom styling.
*   `get_live_data()`: Cached data fetcher.

---

### 2. Agent Layer (`agents/`)
The "Brains" of the application.

#### Core Intelligence
*   **`ForecastingAgent`**: Hybrid ML (Trend + XGBoost Residuals) to predict prices 30 days out.
*   **`MarketRiskEngine`**: Quantifies volatility and shock severity into a 0-100 Risk Score.
*   **`IntelligenceAgent`**: The "Consultant". Runs What-If scenarios (e.g., "Effect of Rain") and suggests "Hold Duration".
*   **`AnomalyDetectionEngine`**: Flags abnormal price spikes (>15%).

#### Optimization (Phase 3)
*   **`OptimizationEngine`**:
    *   **Crop Rotation**: Uses **Linear Programming (Simplex)** to maximize profit given Land/Budget constraints.
    *   **Inventory**: Calculates **Economic Order Quantity (EOQ)** for warehouse efficiency.

#### Business & Accessibility (Phase 2 & 4)
*   **`BusinessEngine`**:
    *   **B2B**: Matchmaking algorithm to connect Farmers with nearby Buyers (based on location/crop).
    *   **Fintech**: Scoring algorithm to assess creditworthiness based on yield stability.
*   **`LanguageManager`**: Dictionary-based translation for UI elements (English, Hindi, Odia).
*   **`ChatbotEngine`**: Regex/NLP-based intent parser for natural language queries (Text/Voice).

---

### 3. Specialized Modules

#### `cv/grading_model.py`
*   **Purpose**: Quality Grading.
*   **Tech**: Structural CNN (Convolutional Neural Network) using PyTorch/TensorFlow (simulated logic for demo).
*   **Input**: Product Image -> **Output**: Grade A/B/C.

#### `utils/graph_algo.py`
*   **Purpose**: Logistics Optimization.
*   **Tech**: **NetworkX** (Dijkstra's Algorithm).
*   **Logic**: Finds the "Best Profit Route" considering Price at Destination - Transport Cost (Distance * Rate).

---

### 4. Data & ETL Layer

#### `database/db_manager.py`
Handles SQLite interactions.
*   **Schema Migration**: Auto-detects missing columns (e.g., `wind_speed`) and updates table structure on startup.
*   **Tables**: `market_prices`, `weather_logs` (w/ wind/humidity), `news_alerts`, `signal_logs`.

#### `etl/data_loader.py`
The simulation engine.
*   **`fetch_real_weather()`**: Integration with **OpenWeatherMap API**.
*   **`run_daily_update()`**: Orchestrates the daily data refresh pipeline.

---

## 🛠️ Configuration & Setup

1.  **Prerequisites**: Python 3.9+
2.  **Dependencies**: `requirements.txt` (Streamlit, Pandas, Plotly, XGBoost, Scipy, Pillow, Requests).
3.  **First Run**:
    ```bash
    pip install -r requirements.txt
    streamlit run app/main.py
    ```
