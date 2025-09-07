#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

"""
Simple MarketPilot Backend
A minimal FastAPI backend to get the system running
"""

# === FastAPI ===
app = FastAPI(title="MarketPilot API", version="1.0.0")

# === Allow CORS from anywhere (or restrict to your domain) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <html>
        <head><title>MarketPilot Dashboard API</title></head>
        <body>
            <h2>🚀 MarketPilot Dashboard Backend</h2>
            <p>Available Endpoints:</p>
            <ul>
                <li><a href="/active-trades">/active-trades</a></li>
                <li><a href="/btc/context">/btc/context</a></li>
                <li><a href="/health">/health</a></li>
                <li><a href="/docs">/docs</a> - API Documentation</li>
            </ul>
            <p><small>Server time: <code>{datetime.now(datetime.UTC).isoformat()}</code></small></p>
        </body>
    </html>
    """


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "service": "MarketPilot Backend",
    }


@app.get("/btc/context")
def get_btc_context():
    """Mock BTC context data"""
    return {
        "status": "UNKNOWN",
        "rsi": 50.0,
        "adx": 25.0,
        "ema": 45000.0,
        "close": 45000.0,
    }


@app.get("/active-trades")
def active_trades():
    """Mock active trades data"""
    return [
        {"symbol": "BTCUSDT", "score": 85},
        {"symbol": "ETHUSDT", "score": 72},
        {"symbol": "ADAUSDT", "score": 68},
    ]


@app.get("/trade-health/{symbol}")
def trade_health(symbol: str):
    """Mock trade health data"""
    return {"symbol": symbol.upper(), "score": 75, "status": "healthy"}


@app.get("/3commas/metrics")
def threecommas_metrics():
    """Mock 3Commas metrics"""
    return {
        "total_trades": 150,
        "active_trades": 12,
        "profit_loss": 1250.50,
        "success_rate": 0.78,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
