# AgriIntel.in: Technical Architecture & System Documentation

## 🏛️ System Overview
**AgriIntel.in** is a **National Unified Agricultural Intelligence Stack** powered by a **Modular Multi-Agent System (MMAS)**. It is designed to modernize agricultural market intelligence through real-time data ingestion, strategic machine learning forecasting, and conversational access layers.

---

## 🏗️ The Three-Layer Stack Architecture

AgriIntel.in operates as an integrated intelligence swarm, categorized into three strategic operational stacks:

```mermaid
graph TD
    %% Entry Points
    Farmer((Farmer)) -->|Voice Call| TelGate(Telephony Gateway)
    Admin((Agri-Admin)) -->|Web Interface| Streamlit(Streamlit App)
    Dev((Dev/Org)) -->|SaaS API| FastAPI(FastAPI Server)

    %% Core Orchestration
    TelGate -->|Webhook| VoiceAPI["Voice API (api_server.py)"]
    Streamlit -->|Logic Controller| MainApp(app/main.py)
    FastAPI -->|Endpoints| MainApp

    subgraph "1. Conversational Access Stack"
        VIntel(VoiceIntelligenceAgent)
        SM(VoiceSessionManager)
        Chat(ChatbotEngine)
        VoiceAPI --> VIntel
        VIntel --> SM
        VIntel --> Chat
    end

    subgraph "2. Strategic Intelligence Stack"
        Ag1(ForecastingAgent)
        Ag2(MarketRiskEngine)
        Ag6(DataHealthAgent)
        Ag7(PerformanceMonitor)
        Ag8(IntelligenceCore)
    end

    subgraph "3. Supply Chain Efficiency Stack"
        Ag3(ArbitrageAgent)
        Ag4(OptimizationEngine)
        Ag5(BusinessEngine)
        CV(GradingModel)
        Graph(LogisticsGraph)
    end

    MainApp --> Ag1 & Ag2 & Ag3 & Ag4 & Ag5 & Ag6 & Ag7 & Ag8
    MainApp --> CV & Graph
    VIntel --> MainApp

    subgraph "Unified Persistence Layer"
        DB[(National Data Warehouse)]
        Redis[(Session Context Cache)]
        MainApp --> DB
        SM --> Redis
    end
```

---

## 🔌 Stack Module Breakdown

### 🎙️ 1. Conversational Access Stack
*   **VoiceIntelligenceAgent**: Manages real-time call lifecycles and dialogue orchestration.
*   **TelecomMapper**: Determines regional language preferences and geographic context via carrier circle mapping.
*   **VoiceSessionManager**: Maintains cross-turn conversational state in a **Sandbox Environment**.
*   **ASR/TTS Engine**: Pluggable interface for high-fidelity speech synthesis and recognition.

### 📊 2. Strategic Intelligence Stack
*   **ForecastingAgent**: Hybrid model performing 30-day market predictions with residual error correction.
*   **MarketRiskEngine**: Decomposes systemic risks into Volatility, Shock, Sentiment, and Weather factors.
*   **IntelligenceCore**: Natural language "AI Analyst" providing deep-dive strategic explanations.
*   **PerformanceMonitor**: Real-time tracking of MAPE/RMSE to ensure model reliability.

### 🚛 3. Supply Chain Efficiency Stack
*   **ArbitrageAgent**: Spatial econometric analysis to identify regional price discrepancies.
*   **LogisticsGraph**: Optimized routing using **Dijkstra's Algorithm** with integrated fuel and toll logic.
*   **OptimizationEngine**: Resources allocation (Simplex) and inventory management (EOQ) for agricultural planning.
*   **GradingModel**: Structural analysis for quality assessment (**Phase II Enhancement**).

---

## 📈 Data Pipeline & Governance
1.  **Ingestion**: `data_loader.py` fetches Market, Weather, and News data in a cascading fallback chain (real API → scraper → simulation).
2.  **Validation**: `DataReliabilityAgent` acts as the quality gate — every batch is checked for completeness, plausibility (±50%/±300% price-change thresholds), and intra-batch duplicates before reaching the database.
3.  **Processing**: The Intelligence Swarm generates unified market signals (Forecast + Risk + Decision).
4.  **Governance**: `DataHealthAgent` monitors ongoing data integrity across the national stack.
5.  **Automation**: The full pipeline runs daily at 00:00 UTC via `.github/workflows/daily_update.yml`.

---

## 🛠️ Operational Setup
```bash
# Install all dependencies
pip install -r requirements.txt

# Run the daily data pipeline (lightweight — no ML training)
python etl/data_loader.py --skip-swarm

# Run the full intelligence swarm (data + forecast + risk + decision)
python etl/data_loader.py

# Launch the Streamlit dashboard
streamlit run app/main.py
```
