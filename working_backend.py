#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from dashboard_backend.threecommas_metrics import get_3commas_metrics
from dashboard_backend.unified_fork_metrics import get_fork_trade_metrics
from utils.redis_manager import get_redis_manager

"""
Working MarketPilot Backend
A simplified version that bypasses config issues and gets the system running
"""

# === FastAPI ===
app = FastAPI(title="MarketPilot API", version="1.0.0")

# === Allow CORS from anywhere ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Redis ===
r = get_redis_manager()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "service": "MarketPilot Backend",
    }


@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <html>
        <head><title>MarketPilot Dashboard API</title></head>
        <body>
            <h2>🚀 MarketPilot Dashboard Backend</h2>
            <p>Available Endpoints:</p>
            <ul>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/active-trades">Active Trades</a></li>
                <li><a href="/btc/context">BTC Context</a></li>
                <li><a href="/3commas/metrics">3Commas Metrics</a></li>
                <li><a href="/fork/metrics">Fork Metrics</a></li>
            </ul>
            <p><strong>Status:</strong> ✅ Running with modular structure</p>
        </body>
    </html>
    """


@app.get("/active-trades")
def active_trades():
    try:
        raw = r.get_cache("active_trades")
        if not raw:
            return []

        entries = json.loads(raw)
        trades = []
        for entry in entries:
            parts = entry.split("_")
            if len(parts) == 2:
                symbol = parts[1] + parts[0]
            else:
                symbol = entry

            score_raw = r.get_cache(f"trade_health:{symbol}")
            try:
                score = int(score_raw) if score_raw else None
            except:
                score = None

            trades.append({"symbol": symbol, "score": score})

        return trades
    except:
        return []


@app.get("/btc/context")
def get_btc_context():
    def parse_float(val):
        try:
            if val is None:
                return 0.0
            return float(str(val).replace("np.float64(", "").replace(")", ""))
        except:
            return 0.0

    try:
        return {
            "status": r.get_cache("cache:btc_condition") or "UNKNOWN",
            "rsi": parse_float(r.get_cache("indicators:BTC:15m:RSI14")),
            "adx": parse_float(r.get_cache("indicators:BTC:1h:ADX14")),
            "ema": parse_float(r.get_cache("indicators:BTC:1h:EMA50")),
            "close": parse_float(r.get_cache("indicators:BTC:1h:latest_close")),
        }
    except:
        return {
            "status": "UNKNOWN",
            "rsi": 50.0,
            "adx": 25.0,
            "ema": 45000.0,
            "close": 45000.0,
        }


@app.get("/3commas/metrics")
def threecommas_metrics():
    """3Commas trading metrics"""
    try:
        # Try to get real 3commas data
        return get_3commas_metrics()
    except:
        # Fallback to mock data
        return {
            "total_trades": 150,
            "active_trades": 12,
            "profit_loss": 1250.50,
            "success_rate": 0.78,
            "status": "mock_data",
        }


@app.get("/fork/metrics")
def serve_cached_metrics():
    try:
        # Try to get real fork metrics
        return get_fork_trade_metrics()
    except:
        return {"error": "Fork metrics not available"}


@app.get("/trade-health/{symbol}")
def trade_health(symbol: str):
    redis_key = f"trade_health:{symbol.upper()}"
    raw = r.get_cache(redis_key)

    if not raw:
        return {"error": "No data"}

    try:
        return {"symbol": symbol.upper(), "score": int(raw)}
    except:
        return {"error": "Invalid format"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
