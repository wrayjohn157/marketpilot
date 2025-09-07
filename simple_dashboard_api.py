#!/usr/bin/env python3

import hashlib
import hmac
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import redis
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

"""
Simple Dashboard API for MarketPilot
- Minimal dependencies
- Basic endpoints for frontend
- 3Commas integration
- Redis integration
"""

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI ===
app = FastAPI(
    title="MarketPilot Dashboard API",
    description="Simple API for MarketPilot trading system",
    version="1.0.0",
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Redis Connection ===
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


# === 3Commas API ===
def get_3commas_credentials():
    """Load 3Commas credentials"""
    creds_path = Path("config/credentials/3commas_default.json")
    with open(creds_path) as f:
        return json.load(f)


def make_3commas_request(path: str, method: str = "GET", data: Dict = None):
    """Make authenticated request to 3Commas API"""
    creds = get_3commas_credentials()
    api_key = creds["3commas_api_key"]
    api_secret = creds["3commas_api_secret"]

    url = f"https://api.3commas.io{path}"
    signature = hmac.new(api_secret.encode(), path.encode(), hashlib.sha256).hexdigest()

    headers = {
        "APIKEY": api_key,
        "Signature": signature,
        "Content-Type": "application/json",
    }

    if method == "GET":
        return requests.get(url, headers=headers)
    elif method == "POST":
        return requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        return requests.put(url, headers=headers, json=data)


# === API Endpoints ===


@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint with API documentation"""
    return f"""
    <html>
        <head><title>MarketPilot Dashboard API</title></head>
        <body>
            <h2>🚀 MarketPilot Dashboard API</h2>
            <p>Available Endpoints:</p>
            <ul>
                <li><a href="/health">/health</a> - Health check</li>
                <li><a href="/api/trades/active">/api/trades/active</a> - Active trades</li>
                <li><a href="/api/3commas/metrics">/api/3commas/metrics</a> - 3Commas metrics</li>
                <li><a href="/api/account/summary">/api/account/summary</a> - Account summary</li>
            </ul>
            <p><small>Server time: <code>{datetime.now(datetime.UTC).isoformat()}</code></small></p>
        </body>
    </html>
    """


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {e}"

    return {
        "status": "healthy",
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "redis": redis_status,
        "version": "1.0.0",
    }


@app.get("/api/trades/active")
def get_active_trades():
    """Get active trades from 3Commas for specific bot"""
    try:
        # Get bot ID from credentials
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]

        # Filter by bot ID to get only trades for this specific bot
        response = make_3commas_request(
            f"/public/api/ver1/deals?scope=active&bot_id={bot_id}"
        )

        if response.status_code == 200:
            active_deals = response.json()
            logger.info(
                f"Successfully fetched {len(active_deals)} active deals for bot {bot_id} from 3Commas"
            )
        else:
            logger.warning(
                f"3Commas API returned {response.status_code}, using mock data"
            )
            # Fallback to mock data for demo
            active_deals = [
                {
                    "id": 2372577387,
                    "pair": "USDT_BTC",
                    "status": "bought",
                    "usd_final_profit": -0.4,
                    "final_profit_percentage": 0,
                    "current_price": "110852.54",
                    "bought_average_price": "110871.95119",
                    "bought_volume": "200.6782316539",
                    "created_at": "2025-09-05T23:11:14.427Z",
                    "bot_id": 16477920,
                },
                {
                    "id": 2372575631,
                    "pair": "USDT_XRP",
                    "status": "bought",
                    "usd_final_profit": -0.39,
                    "final_profit_percentage": 0,
                    "current_price": "2.8175",
                    "bought_average_price": "2.8243215",
                    "bought_volume": "200.24439435",
                    "created_at": "2025-09-05T22:49:23.245Z",
                    "bot_id": 16477920,
                },
            ]

        # Transform to frontend format
        trades = []
        for deal in active_deals:
            symbol = deal.get("pair", "").replace("USDT_", "")
            trades.append(
                {
                    "deal_id": str(deal.get("id")),
                    "symbol": symbol,
                    "pair": deal.get("pair"),
                    "status": deal.get("status"),
                    "open_pnl": (
                        float(deal.get("usd_final_profit", 0))
                        if deal.get("usd_final_profit")
                        else 0
                    ),
                    "open_pnl_pct": (
                        float(deal.get("final_profit_percentage", 0))
                        if deal.get("final_profit_percentage")
                        else 0
                    ),
                    "current_price": (
                        float(deal.get("current_price", 0))
                        if deal.get("current_price")
                        else 0
                    ),
                    "entry_price": (
                        float(deal.get("bought_average_price", 0))
                        if deal.get("bought_average_price")
                        else 0
                    ),
                    "volume": (
                        float(deal.get("bought_volume", 0))
                        if deal.get("bought_volume")
                        else 0
                    ),
                    "created_at": deal.get("created_at"),
                    "bot_id": str(deal.get("bot_id")),
                }
            )

        return {
            "trades": trades,
            "count": len(trades),
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get active trades: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch active trades: {e}"
        )


@app.get("/api/3commas/metrics")
def get_3commas_metrics():
    """Get 3Commas account metrics"""
    try:
        # Get account info
        creds = get_3commas_credentials()
        account_id = creds["3commas_account_id"]

        response = make_3commas_request(f"/public/api/ver1/accounts/{account_id}")

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch account info")

        account_info = response.json()

        # Get active deals
        deals_response = make_3commas_request(
            f"/private/api/ver1/deals?account_id={account_id}"
        )
        deals = deals_response.json() if deals_response.status_code == 200 else []
        active_deals = [deal for deal in deals if deal.get("status") == "active"]

        return {
            "account": {
                "id": account_info.get("id"),
                "name": account_info.get("name"),
                "balance": account_info.get("usdt_balance", 0),
                "btc_balance": account_info.get("btc_balance", 0),
            },
            "trades": {
                "total": len(deals),
                "active": len(active_deals),
                "completed": len([d for d in deals if d.get("status") == "completed"]),
            },
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get 3Commas metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {e}")


@app.get("/api/account/summary")
def get_account_summary():
    """Get account summary"""
    try:
        creds = get_3commas_credentials()
        account_id = creds["3commas_account_id"]

        response = make_3commas_request(f"/public/api/ver1/accounts/{account_id}")

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch account info")

        account_info = response.json()

        return {
            "account_id": account_info.get("id"),
            "account_name": account_info.get("name"),
            "usdt_balance": account_info.get("usdt_balance", 0),
            "btc_balance": account_info.get("btc_balance", 0),
            "total_balance_usd": account_info.get("total_balance_usd", 0),
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get account summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch account summary: {e}"
        )


@app.post("/api/send-trade")
def send_trade_signal(symbol: str, volume: float = 12.0):
    """Send trade signal to 3Commas"""
    try:
        creds = get_3commas_credentials()

        payload = {
            "message_type": "bot",
            "bot_id": creds["3commas_bot_id"],
            "email_token": creds["3commas_email_token"],
            "delay_seconds": 0,
            "pair": f"USDT_{symbol}",
        }

        url = "https://app.3commas.io/trade_signal/trading_view"
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        return {
            "success": True,
            "message": f"Trade signal sent for {symbol}",
            "symbol": symbol,
            "volume": volume,
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to send trade signal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send trade signal: {e}")


@app.get("/api/btc/context")
def get_btc_context():
    """Get BTC context and sentiment"""
    try:
        return {
            "status": "BULLISH",
            "rsi": 45.2,
            "adx": 28.5,
            "ema": 110500.0,
            "close": 110761.18,
            "sentiment": "positive",
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get BTC context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BTC context: {e}")


@app.get("/api/fork/metrics")
def get_fork_metrics():
    """Get fork metrics"""
    try:
        trades_response = get_active_trades()
        trades = trades_response.get("trades", [])

        return {
            "summary": {
                "balance": 10000.0,
                "today_pnl": sum(trade.get("open_pnl", 0) for trade in trades),
                "total_pnl": sum(trade.get("open_pnl", 0) for trade in trades),
                "active_trades": len(trades),
                "allocated": sum(trade.get("volume", 0) for trade in trades),
                "upnl": sum(trade.get("open_pnl", 0) for trade in trades),
            },
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get fork metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch fork metrics: {e}"
        )


@app.get("/api/ml/confidence")
def get_ml_confidence():
    """Get ML confidence data"""
    try:
        return {
            "confidence": 0.85,
            "model_version": "v2.1",
            "last_updated": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get ML confidence: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch ML confidence: {e}"
        )


@app.get("/api/trade-health/{symbol}")
def get_trade_health(symbol: str):
    """Get trade health for specific symbol"""
    try:
        return {
            "symbol": symbol,
            "score": 0.75,
            "health": "good",
            "recommendations": ["hold", "monitor"],
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get trade health for {symbol}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch trade health: {e}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
