# 🌾 AgriIntel.in: National AI Agricultural Voice Infrastructure & Intelligence Suite

**AgriIntel.in** is an end-to-end **Conversational Voice AI & Multi-Agent Market Intelligence Platform** designed to revolutionize the agricultural ecosystem in India. It transforms complex market analytics into actionable, regional-language insights accessible via web, API, and telephony.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agriintel-live.streamlit.app/)

---

## 🚀 Core Pillars & Exhaustive Feature List

### 🎙️ 1. Conversational Voice AI & Accessibility
*   **Telephony-Ready Infrastructure**: Real-time voice interaction layer for standard phone calls (simulated gateway).
*   **Multi-Turn Dialogue Management**: Maintain conversational context (crop, location) across a single session.
*   **Regional Language Support**: Fully supported voice and text interactions in **Hindi**, **Marathi**, **Odia**, and **English**.
*   **Telecom Mapping**: Automatic detection of caller region and initial language preference using Indian telecom circle logic.
*   **WhatsApp Bot Simulation**: Low-bandwidth "Chat Mode" for SMS/WhatsApp-style queries.
*   **Vernacular UI**: Multilingual dashboard interface for seamless adoption by rural users.

### 📊 2. Market Intelligence & Forecasting
*   **Hybrid Price Forecasting**: Combines additive trend decomposition with **XGBoost** residuals for high-accuracy 30-day predictions.
*   **Dynamic Confidence Intervals**: Visual upper and lower bounds for price forecasts based on statistical uncertainty.
*   **Risk & Shock Decomposition**: Quantifies risk into four distinct drivers: **Volatility**, **Abnormal Shocks**, **News Sentiment**, and **Weather Impact**.
*   **Arbitrage Engine**: Real-time identification of profitable regional trade opportunities.
*   **Logistics Cost Modeling**: Realistic profit calculation considering **Fuel Rates**, **Tolls**, **Labor**, and **Spoilage percentages**.
*   **AI Smart Consultant**: Interactive agent for running "What-If" scenarios (e.g., *"How will a 20% rainfall spike affect Potato prices?"*).
*   **Decision Signal Banner**: Real-time "Buy/Hold/Sell" recommendations with calculated Reliability Badges and accuracy scores.

### 🏢 3. Enterprise SaaS & Institutional Tools
*   **Multi-Tenant Architecture**: Secure, isolated environments for different organizations.
*   **Role-Based Access Control (RBAC)**: Specialized permissions for **Admin**, **Analyst**, and **Viewer** roles.
*   **Institutional Dashboard**: National-level heatmap and state-wise market aggregation for government/corporate governance.
*   **Comprehensive REST API**: Developer-friendly endpoints for price, risk, arbitrage, and voice interaction integration.
*   **Data Reliability Dashboard**: Monitoring of ETL success rates, execution times, and pipeline health.
*   **Quality Alerts**: Automated identification of data anomalies or collection failures.

### 📸 4. Quality, Logistics & Optimization
*   **Computer Vision Grading**: Visual quality assessment simulation (Grade A/B/C) using image-based structural analysis.
*   **Smart Logistics (Graph Theory)**: Uses **Dijkstra’s Algorithm** to find the most profitable route across a network of mandis.
*   **Crop Rotation Planning**: Uses **Linear Programming (Simplex)** to maximize farm profit under land and budget constraints.
*   **Inventory Optimization**: Calculates **Economic Order Quantity (EOQ)** for warehouse and supply chain efficiency.

### 💰 5. Fintech & B2B Services
*   **Agri-Credit Scoring**: AI-driven creditworthiness assessment based on historical yield stability and price consistency.
*   **B2B Marketplace**: Intelligent matchmaking service connecting Farmers directly with Millers, Exporters, and bulk Buyers.

---

## 🛠️ Tech Stack & Science
*   **ML Engine**: XGBoost, Scikit-Learn, Prophet.
*   **Math Backend**: Scipy (Optimization), NetworkX (Graph Analytics).
*   **Core Logic**: Python 3.9+, FastAPI, Redis (Session Cache), SQLite (Warehouse).
*   **Interface**: Streamlit, Plotly, Mermaid.js.

---

## 🔄 Self-Healing Automation
**AgriIntel.in** features a fully autonomous data pipeline powered by **GitHub Actions**:
*   **Daily Sync**: Automatically fetches simulated Agmarknet prices, news feeds, and real-time weather.
*   **Model Accuracy Tracking**: Continuously calculates **MAPE** and **RMSE** for every recommendation.
*   **Drift Monitoring**: Alerts when model performance degrades below the 20% accuracy threshold.

---

## 📦 Getting Started
1.  **Repo**: `git clone https://github.com/Tick2003/AgriIntel-Live.git`
2.  **Setup**: `pip install -r requirements.txt`
3.  **Core App**: `streamlit run app/main.py`
4.  **API**: `uvicorn api_server:app --reload`

*Empowering Indian Agriculture through Voice & Intelligence*
