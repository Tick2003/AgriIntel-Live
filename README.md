# 🌾 AgriIntel 2.0 - The Full Stack Agricultural Intelligence Suite

**AgriIntel 2.0** is a comprehensive ecosystem designed to empower Indian farmers, traders, and enterprises with actionable insights. From **Forecasting Prices** to **Connecting Buyers**, it covers the entire agricultural lifecycle.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agriintel-live.streamlit.app/)

> 📘 **[Architecture Documentation](ARCHITECTURE.md)** | 🛠️ **[Installation Guide](#-how-to-run-locally)**

---

## 🚀 Key Modules (The 4 Pillars)

### 📊 1. Market Intelligence (The "Brain")
*   **Price Forecasting**: Hybrid ML models (XGBoost + Trend Decomposition) predict prices 30 days ahead with dynamic confidence intervals.
*   **Risk & Shocks**: Automatic detection of market anomalies (>15% price drops) and volatility regimes.
*   **Smart Consultant**: Interactive AI agent that runs "What-If" scenarios (e.g., *"Effect of Heavy Rain on Onion prices"*) and suggests specific **Hold Durations**.

### 📸 2. Quality & Logistics (The "Eyes & Legs")
*   **Computer Vision Grading**: Upload crop images to get an instant **Grade A/B/C** assessment using a structural CNN.
*   **Smart Logistics**: Uses **Dijkstra’s Algorithm** (Graph Theory) to find the "Best Profit Route" by balancing Market Price vs. Transport Costs across varying distances.

### 🌏 3. Accessibility (The "Voice")
*   **Vernacular UI**: Fully translated interface in **Hindi** and **Odia** for rural adoption.
*   **WhatsApp Bot Simulation**: A low-bandwidth "Chat Mode" that mimics SMS/WhatsApp queries (e.g., *"Onion rate Cuttack?"*) with **Voice-to-Text** support.

### 💼 4. Business & Monetization (The "Wallet")
*   **B2B Marketplace**: "Tinder for Crops" — Matches Farmers with Millers, Exporters, and Retail Chains based on location and commodity.
*   **Fintech Hub**: Generates an **Agri-Credit Score** (300-900) based on historical yield stability, enabling instant loan eligibility checks.
*   **SaaS API**: Developer portal for enterprises to access AgriIntel's data streams via API keys.

---

## 🛠️ Tech Stack
*   **Core**: Python 3.9+
*   **Frontend**: Streamlit
*   **ML & Math**: XGBoost, Scikit-Learn, Scipy (Linear Programming), NetworkX (Graph Algo), PyTorch/TensorFlow (CV Structure).
*   **Data**: SQLite, OpenWeatherMap API, Simulated Agmarknet Feed.

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

4.  **Run the App**:
    ```bash
    streamlit run app/main.py
    ```

## ☁️ Live Demo
AgriIntel is deployed on **Streamlit Cloud**. To update the live version, simply push to the `main` branch.

---
*Built with ❤️ for Indian Agriculture*
