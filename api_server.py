
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import pandas as pd
import sqlite3
import uvicorn
import os
import sys

# Add root to path
sys.path.append(os.getcwd())
import database.db_manager as db_manager
from agents.arbitrage_engine import ArbitrageAgent
from agents.risk_scoring import MarketRiskEngine

app = FastAPI(
    title="AgriIntel API",
    description="Advanced AI Market Intelligence for Indian Agriculture",
    version="1.0.0"
)

# --- Security ---
API_KEY = "agriintel-secret-key-123" # Mock Key

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# --- Endpoints ---

@app.get("/")
def home():
    return {"message": "Welcome to AgriIntel API", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok", "db": "connected"}

@app.get("/v1/price/{commodity}/{mandi}", dependencies=[Depends(verify_api_key)])
def get_price(commodity: str, mandi: str):
    """Get latest market price."""
    df = db_manager.get_latest_prices(commodity)
    if df.empty:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    row = df[df['mandi'] == mandi].sort_values('date').tail(1)
    if row.empty:
        raise HTTPException(status_code=404, detail="Mandi data not found")
        
    return row.to_dict(orient='records')[0]

@app.get("/v1/risk/{commodity}/{mandi}", dependencies=[Depends(verify_api_key)])
def get_risk(commodity: str, mandi: str):
    """Calculate Real-Time Risk Score."""
    # Fetch Data
    df = db_manager.get_price_history(commodity, mandi)
    if df.empty:
        raise HTTPException(status_code=404, detail="Data not found")
        
    # Mock Volatility Calc
    df['price'] = df['price_modal'] # Normalize
    volatility = df['price'].pct_change().std()
    
    # Run Agent
    engine = MarketRiskEngine()
    # Mock inputs for API simplicity (In real app, we'd fetch these too)
    risk_data = engine.calculate_risk_score(
        shock_info={"is_shock": False}, 
        forecast_std=100, 
        market_volatility=volatility if not pd.isna(volatility) else 0.01,
        sentiment_score=0,
        arrival_anomaly=0,
        weather_risk=0
    )
    return risk_data

@app.get("/v1/arbitrage/{commodity}/{mandi}", dependencies=[Depends(verify_api_key)])
def get_arbitrage(commodity: str, mandi: str):
    """Find Arbitrage Opportunities."""
    # Fetch all data for commodity
    df = db_manager.get_latest_prices(commodity)
    if df.empty:
        raise HTTPException(status_code=404, detail="Commodity data not found")
        
    agent = ArbitrageAgent()
    # Find ops
    opps_df = agent.find_opportunities(commodity, mandi, df, {"is_shock": False})
    
    if opps_df.empty:
        return {"opportunities": []}
        
    return {"opportunities": opps_df.to_dict(orient='records')}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
