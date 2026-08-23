"""
AgriIntel.in API Server (v2.0 — Hardened)
==========================================
Production-ready FastAPI with CORS, rate limiting, deep health checks,
and timing-safe auth.
"""

import hmac
import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uvicorn

# Add root to path
sys.path.append(os.getcwd())

from config import settings
import database.db_manager as db_manager
from agents.arbitrage_engine import ArbitrageAgent
from agents.risk_scoring import MarketRiskEngine

logger = logging.getLogger(__name__)

# --- Rate Limiting ---
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    limiter = None
    RATE_LIMITING_AVAILABLE = False
    logger.warning("slowapi not installed — rate limiting disabled. Install with: pip install slowapi")


# --- Security ---
API_KEY = settings.security.api_key

# --- Lifespan (startup/shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate critical config and initialize DB on startup."""
    if settings.app.is_production and not API_KEY:
        logger.critical("REFUSING to start in production without AGRIINTEL_API_KEY!")
        raise RuntimeError("API key not configured for production deployment")

    try:
        db_manager.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    yield  # App runs here


app = FastAPI(
    title="AgriIntel.in API",
    description="Advanced AI Market Intelligence for Indian Agriculture",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.app.is_production else None,
    redoc_url="/redoc" if not settings.app.is_production else None,
)

# --- CORS Middleware (Hardened) ---
# In production, restrict origins to the deployed Streamlit app.
# In development, allow localhost for convenience.
if settings.app.is_production:
    allowed_origins = os.environ.get(
        "CORS_ORIGINS",
        "https://agriintel-live.streamlit.app"
    ).split(",")
else:
    allowed_origins = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:8501,http://localhost:3000"
    ).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# --- Rate Limiting Middleware ---
if RATE_LIMITING_AVAILABLE and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key using timing-safe comparison."""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server API key not configured. Set AGRIINTEL_API_KEY env var.")
    if not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# --- Response Models ---
class HealthResponse(BaseModel):
    status: str
    db: str
    db_record_count: int = 0
    environment: str = "development"

class VoiceStartRequest(BaseModel):
    phone_number: str

class VoiceInteractionRequest(BaseModel):
    session_id: str
    text_input: str

# --- Endpoints ---

@app.get("/")
def home():
    return {"message": "Welcome to AgriIntel.in API", "version": "2.0.0", "docs": "/docs"}

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Deep health check — actually verifies DB connectivity."""
    db_status = "disconnected"
    record_count = 0
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM market_prices")
            record_count = cursor.fetchone()[0]
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    
    status = "ok" if db_status == "connected" else "degraded"
    return HealthResponse(
        status=status,
        db=db_status,
        db_record_count=record_count,
        environment=settings.app.environment
    )

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
    df = db_manager.get_price_history(commodity, mandi)
    if df.empty:
        raise HTTPException(status_code=404, detail="Data not found")
        
    df['price'] = df['price_modal']
    volatility = df['price'].pct_change().std()
    
    engine = MarketRiskEngine()
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
    df = db_manager.get_latest_prices(commodity)
    if df.empty:
        raise HTTPException(status_code=404, detail="Commodity data not found")
        
    agent = ArbitrageAgent()
    opps_df = agent.find_opportunities(commodity, mandi, df, {"is_shock": False})
    
    if opps_df.empty:
        return {"opportunities": []}
        
    return {"opportunities": opps_df.to_dict(orient='records')}

# --- Voice Endpoints ---
try:
    from agents.voice_intelligence import VoiceIntelligenceAgent
    voice_agent = VoiceIntelligenceAgent()
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    logger.warning("Voice intelligence agent not available (missing dependencies)")

@app.post("/v1/voice/start", dependencies=[Depends(verify_api_key)])
def voice_start(req: VoiceStartRequest):
    """Start a voice session."""
    if not VOICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice service unavailable")
    session_id, greeting, lang = voice_agent.handle_call_start(req.phone_number)
    return {"session_id": session_id, "greeting": greeting, "language": lang}

@app.post("/v1/voice/interact", dependencies=[Depends(verify_api_key)])
def voice_interact(req: VoiceInteractionRequest):
    """Process a voice interaction turn."""
    if not VOICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice service unavailable")
    response_text, lang = voice_agent.handle_interaction(req.session_id, text_input=req.text_input)
    return {"response_text": response_text, "language": lang}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
