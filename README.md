# 🌾 AgriIntel.in: National Unified Agricultural Intelligence Stack

**AgriIntel.in** is an authoritative, end-to-end **Conversational Intelligence & Market Analytics ecosystem** designed to revolutionize the agricultural lifecycle in India. It serves as a single source of truth for farmers, policymakers, and institutional stakeholders through a speech-first regional language interface.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agriintel-live.streamlit.app/)

---

## 🏛️ The National Intelligence Stack

AgriIntel.in consolidates 20+ specialized AI agents into a unified, high-performance architecture:

### 🎙️ 1. Conversational Access Stack
*   **Telephony-Ready Infrastructure**: Real-time voice interaction layer for standard phone calls (In Sandbox Environment).
*   **Multi-Turn Dialogue Management**: Sustained conversational context across sessions.
*   **Regional Language Engine**: Native support for **Hindi**, **Marathi**, **Odia**, and **English**.
*   **Telecom Mapping**: Automatic region-aware language detection via carrier circle mapping.
*   **Digital Outreach**: SMS/Messenger-style interaction mode (Pilot Mode).

### 📊 2. Strategic Intelligence Stack
*   **Hybrid Price Forecasting**: Residual-corrected additive models for 30-day market predictions.
*   **Risk & Shock Decomposition**: Quantitative analysis of **Volatility**, **Abnormal Shocks**, **Sentiment**, and **Weather** risk drivers.
*   **Decision Signal Banner**: Dynamic "Buy/Hold/Sell" advisory with reliability metadata.
*   **AI Analyst Deep-Dive**: Interactive consultant for hypothetical scenario analysis.
*   **Institutional Dashboard**: State-level heatmaps and governance-focused market aggregation.

### 🚛 3. Supply Chain Efficiency Stack
*   **Spatial Arbitrage Engine**: Identification of regional trade opportunities with logistical cost modeling.
*   **Network Optimization**: Shortest-path routing using Dijkstra's logic (Integrating Tolls & Fuel).
*   **Computer Vision Grading**: Structural quality assessment (Phase II Enhancement).
*   **Agri-Credit & B2B Matchmaking**: Matchmaking Farmers with Exporters and calculating AI-driven creditworthiness scores.
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
