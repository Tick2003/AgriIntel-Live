# 🌾 AgriIntel.in: National Unified Agricultural Intelligence Stack

**AgriIntel.in** is an authoritative, end-to-end **Conversational Intelligence & Market Analytics ecosystem** designed to revolutionize the agricultural lifecycle in India. It serves as a single source of truth for farmers, policymakers, and institutional stakeholders through a speech-first regional language interface.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agriintel-live.streamlit.app/)

---

## 🏛️ The National Intelligence Stack

AgriIntel.in consolidates 20+ specialized AI agents into a unified, high-performance architecture:

### 🎙️ 1. Conversational Access Stack (Voice Gateway)
*   **Telephony-Ready Infrastructure**: Real-time voice interaction layer for standard phone calls (Hindi and English).
*   **Multi-Turn Dialogue Management**: Sustained conversational context across sessions.
*   **Telecom Mapping**: Automatic region-aware language detection via carrier circle mapping.

### 🧠 2. RACE Forecasting & Real-Time Trading Stack (NEW)
*   **RACE Forecaster (Regime-Adaptive Competitive Ensemble)**: Patent-grade engine combining HMM (Hidden Markov Model) regime classification (Stable/Volatile/Crisis) with dynamic inverse-MAPE weighted ensembles across **XGBoost**, **LightGBM**, and **CatBoost**.
*   **High-Frequency Intraday Simulation Engine**: Daemon-driven simulator generating live eNAM bid/ask and completed trades every 2-3s, biased by weather stress and news sentiment.
*   **Bloomberg-Style Trading Desk UI**: Streamlit page designed with non-blocking `@st.fragment` rendering live order books, scrolling trade tickers, and Plotly intraday charts.
*   **$3\sigma$ Shock Sentinel & Risk Augmentation**: Statistical sentinel flagging ticks exceeding $3\sigma$ deviation, instantly augmenting baseline risk score (+20 pts) in <5 seconds.

### 🚛 3. Supply Chain & Logistics Stack
*   **Spatial Arbitrage Corridor Engine**: Maps mandi networks using Dijkstra’s shortest-path algorithms to optimize route profits (factoring tolls, distance, and transport costs).
*   **Computer Vision Grading**: Visual produce scanning returning objective commercial grades (Grade A/B/C) with automatic pricing recommendations.
*   **Agri-Credit & B2B Matchmaking**: Farmers/exporters matchmaking and creditworthiness scoring.
*   **Smart Resource Planning**: Crop rotation (Simplex Algorithm) and inventory level optimization (EOQ).

---

## 📖 Essential Documentation
For a deeper look into the system, please refer to:
*   📜 **[Technical Architecture](ARCHITECTURE.md)**: Deep-dive into the Multi-Agent System (MMAA) and mathematical foundations.
*   📖 **[The AgriIntel.in Story](PRODUCT_STORY.md)**: A comprehensive, layman-friendly guide to every feature.

---

## 🔄 Autonomous Operations
**AgriIntel.in** features a fully autonomous, self-healing data pipeline:
*   **Daily Sync**: Automated ingestion of Market Data, News, and Weather patterns (Pilot Mode).
*   **Model Accuracy Tracking**: Continuous calculation of **MAPE** and **RMSE** for automated retraining.
*   **Infrastructure Health**: Real-time monitoring of ETL success and pipeline execution.

---

## 📦 Local Setup
1.  **Repository**: `git clone https://github.com/Tick2003/AgriIntel-Live.git`
2.  **Packages**: `pip install -r requirements.txt`
3.  **App**: `streamlit run app/main.py`
4.  **API**: `uvicorn api_server:app --reload`

*Intelligence for the Soil. Power for the Farmer.*
