# 🌾 AgriIntel - Agricultural Market Intelligence System

A live dashboard for tracking agricultural commodities (Potato, Onion, Tomato) in Indian Mandis. This project uses simulated real-time data to demonstrate advanced market intelligence features.

## 🚀 Features
- **Live Market Data**: Simulated real-time prices and arrivals for major Mandis.
- **Compare Markets**: Side-by-side comparison of commodities and regions.
- **Weather Intelligence**: Live weather impact alerts (Temperature, Rainfall).
- **Global News Hub**: Real-time agriculture news feed with sentiment analysis.
- **Price Forecasting**: 30-day AI-driven price predictions.
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
