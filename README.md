# 🌾 AgriIntel - Agricultural Market Intelligence System

A live AI-powered dashboard for tracking agricultural commodities (Potato, Onion, Tomato) in Indian Mandis. This project uses simulated real-time data and advanced Machine Learning (XGBoost + Trend Decomposition) to provide accurate 30-day price forecasts and risk assessments.

📘 **[Read the Full Architecture Documentation](ARCHITECTURE.md)** to understand every module from tip to toe.

## 🚀 Features & Roadmap

### 🤖 1. AI Market Consultant (Live)
- **Conversational**: Ask "Should I sell onions in Agra?" and get a Buy/Hold/Sell signal.
- **Context-Aware**: Considers Price trends, Risk scores, and News sentiment.
- **Persona**: Acts as a Senior Analyst, not a chatbot.

### 📲 2. Smart Alerts (Beta)
- **Shock Detection**: Automatic banners for sudden price crashes (>5%).
- **Arbitrage**: Scans nearby mandis for price gaps > Transport Cost.

### 📊 3. Self-Evaluation & Trust (New)
- **Accuracy Boost**: Displays how much better the AI is vs a Naive Baseline.
- **Backtesting**: Validates model performance on hidden test sets (Last 30 days).

### 👤 4. User Personalization & Simulation
- **Sidebar Config**: Set your preferred Commodity and Mandi.
- **Scenario Simulator**: Run "What-If" analysis (e.g., "Heavy Rain", "Export Ban") to see price impact.

### 🧠 5. Learning Strategy Engine
- **Auto-Tuning**: XGBoost model optimizes its own hyperparameters (Learning Rate, Depth) before every run.
- **Weather Fusion**: Ingests Rainfall/Temp data to refine forecasts.

### 🌍 6. Roadmap (Upcoming)
- **Real-Time API**: Connect to live Agmarknet XML feeds.
- **Mobile Mode**: Low-bandwidth UI for rural access.
- **Personalized Accounts**: Save transport costs and risk preferences.

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
