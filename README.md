# 🌾 AgriIntel - Agricultural Market Intelligence System

A live AI-powered dashboard for tracking agricultural commodities (Potato, Onion, Tomato) in Indian Mandis. This project uses simulated real-time data and advanced Machine Learning (XGBoost + Trend Decomposition) to provide accurate 30-day price forecasts and risk assessments.

📘 **[Read the Full Architecture Documentation](ARCHITECTURE.md)** to understand every module from tip to toe.

## 🚀 Features
- **Live Market Data**: Simulated real-time prices and arrivals for major Mandis.
- **AI Consultant 🤖**: Chat with the system ("Should I sell?") or run "What-If" scenarios (Rain/Export Ban).
- **Signal Accuracy Tracker**: Automated backtesting of past signals with a real-time "Win Rate" badge.
- **Actionable Signals**: "Sell Now", "Hold", "Accumulate" recommendations with Confidence Scores.
- **Regional Arbitrage**: Identify profitable trade routes between Mandis.
- **Global News Hub**: Real-time agriculture news feed (De-duplicated) with sentiment analysis.
- **Price Forecasting**: 30-day AI-driven price predictions using XGBoost.
- **Risk Scoring**: Automated market risk assessment.

## 🛠️ Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python (Pandas, Plotly)
- **Database**: SQLite
- **Data Sources**: Agmarknet (Simulated), Google News RSS, Weather (Simulated)

## 📦 How to Run Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/Tick2003/AgriIntel-Live.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Seed the database with historical data:
   ```bash
   python etl/data_loader.py seed
   ```
4. Run the dashboard:
   ```bash
   streamlit run app/main.py
   ```

## ☁️ Deployment
This app is ready for [Streamlit Cloud](https://streamlit.io/cloud). Just connect your repository and deploy!

---
*Built with ❤️ for Indian Agriculture*
