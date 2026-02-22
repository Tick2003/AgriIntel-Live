# 🌾 AgriIntel 2.0 - The Full Stack Agricultural Intelligence Suite

**AgriIntel 2.0** is a comprehensive **Multi-Tenant SaaS Ecosystem** designed to empower Indian farmers, traders, and enterprises with actionable insights. From **Forecasting Prices** to **Connecting Buyers**, it covers the entire agricultural lifecycle.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agriintel-live.streamlit.app/)

> 📘 **[Architecture Documentation](ARCHITECTURE.md)** | 🛠️ **[Installation Guide](#-how-to-run-locally)**

---

## 🚀 Key Modules (The 4 Pillars)

### 📊 1. Market Intelligence (The "Brain")
*   **Price Forecasting**: Hybrid ML models (XGBoost + Trend Decomposition) predict prices 30 days ahead with dynamic confidence intervals.
*   **Risk & Shocks**: Decomposes risk into **Volatility**, **Shock**, **Sentiment**, and **Weather** components.
*   **Arbitrage Engine**: Real-time identification of profitable trade routes with realistic cost modeling (**Fuel**, **Tolls**, **Spoilage**).
*   **Model Drift Detection**: Automated monitoring of AI model health with alerts for accuracy degradation.
*   **Smart Consultant**: Interactive AI agent that runs "What-If" scenarios (e.g., *"Effect of Heavy Rain on Onion prices"*).

### 🏢 2. Enterprise SaaS (The "Backbone")
*   **Multi-Tenancy**: Secure **Organization-based** access control (RBAC) with Admin, Analyst, and Viewer roles.
*   **API Infrastructure**: RESTful API (`/v1/price`, `/v1/risk`) for external integration, powered by **FastAPI**.
*   **Institutional Dashboard**: National-level heatmap and state-wise volatility analysis for government/corporate users.
*   **SaaS API**: Developer portal for enterprises to access AgriIntel's data streams via API keys.

### 📸 3. Quality & Logistics (The "Eyes & Legs")
*   **Computer Vision Grading**: Visual simulation of crop grading (A/B/C) using structural analysis.
*   **Smart Logistics**: Uses **Dijkstra’s Algorithm** (Graph Theory) to find the "Best Profit Route" balancing Market Price vs. Transport Costs.

### 🌏 4. Accessibility & Business (The "Voice & Wallet")
*   **Vernacular UI**: Fully translated interface in **Hindi** and **Odia** for rural adoption.
*   **WhatsApp Bot Simulation**: A low-bandwidth "Chat Mode" that mimics SMS/WhatsApp queries with **Voice-to-Text** support.
*   **B2B Marketplace**: "Tinder for Crops" — Matches Farmers with Millers and Exporters based on location and commodity.
*   **Fintech Hub**: Generates an **Agri-Credit Score** (300-900) based on historical yield stability, enabling instant loan eligibility checks.

---

## 🛠️ Tech Stack
*   **Core**: Python 3.9+
*   **Frontend**: Streamlit
*   **Backend API**: FastAPI, Uvicorn
*   **ML & Math**: XGBoost, Scikit-Learn, Scipy (Linear Programming), NetworkX (Graph Algo), PyTorch/TensorFlow (CV Structure).
*   **Data**: SQLite (Optimized with VACUUM), OpenWeatherMap API, Simulated Agmarknet Feed, Pandas.
*   **DevOps**: GitHub Actions (CI/CD), Streamlit Cloud.

---

## 🔄 Automated Data Pipeline
The system features a **Self-Healing Data Pipeline** powered by **GitHub Actions**.
*   **Schedule**: Runs automatically every day at 00:00 UTC.
*   **Trigger**: Also runs on every `git push` to `main` for immediate feedback.
*   **Process**:
    1.  Fetches latest Simulated Market Prices.
    2.  Scrapes News via Google RSS.
    3.  Fetches Real Weather from OpenWeatherMap.
    4.  **Commits & Pushes** data back to the repo (`data/market_prices.csv`) for persistence.

---

## 📦 How to Run Locally

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Tick2003/AgriIntel-Live.git
    cd AgriIntel-Live
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Seed the Database** (Important for first run):
    ```bash
    python etl/data_loader.py seed
    ```

4.  **Run the App (Dashboard)**:
    ```bash
    streamlit run app/main.py
    ```

5.  **Run the API Server (Optional)**:
    ```bash
    uvicorn api_server:app --reload
    ```
    *API Docs available at `http://localhost:8000/docs`*

---

## ☁️ Live Demo
AgriIntel is deployed on **Streamlit Cloud**. To update the live version, simply push to the `main` branch.

---
*Built with ❤️ for Indian Agriculture*
