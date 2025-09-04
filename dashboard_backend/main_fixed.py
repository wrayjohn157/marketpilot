#!/usr/bin/env python3
"""
Fixed Market7 Dashboard Backend
- Unified API endpoints
- Proper data structure alignment
- Fixed 3Commas integration
- Unified Redis usage
- Comprehensive error handling
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI ===
app = FastAPI(
    title="Market7 Trading Dashboard API",
    description="Unified API for Market7 trading system",
    version="2.0.0",
)

from .metrics_routes import router as metrics_router

# === Monitoring ===
from .middleware import LoggingMiddleware, MetricsMiddleware

# Add monitoring middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)

# Include metrics routes
app.include_router(metrics_router)

from config.unified_config_manager import get_config, get_path
from utils.credential_manager import get_3commas_credentials

# === Redis ===
from utils.redis_manager import get_redis_manager

# === Allow CORS from anywhere (or restrict to your domain) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Dependency Injection ===
def get_redis():
    return get_redis_manager()


def get_3commas_creds():
    return get_3commas_credentials()


from config_routes import safu_config_api
from config_routes.dca_config_api import router as dca_config_router
from config_routes.fork_score_config_api import router as fork_score_config_router
from config_routes.tv_screener_config_api import router as tv_screener_config_router
from dca_status import router as dca_router
from dca_trades_api import router as dca_trades_api_router
from eval_routes import dca_eval_api
from eval_routes.price_series_api import router as price_series_router
from ml_confidence_api import router as ml_confidence_router
from refresh_price_api import router as price_refresh_router
from sim_routes.dca_simulate_route import router as dca_simulate_router
from sim_routes.sim_dca_strategies import router as sim_dca_strategy_router

# === Route imports ===
from unified_fork_metrics import get_fork_trade_metrics

from dashboard_backend.sim_routes.sim_dca_config_api import router as sim_dca_router

# Include routers
app.include_router(dca_router)
app.include_router(ml_confidence_router)
app.include_router(price_refresh_router)
app.include_router(dca_trades_api_router)
app.include_router(fork_score_config_router, prefix="/config")
app.include_router(dca_config_router, prefix="/config")
app.include_router(tv_screener_config_router, prefix="/config")
app.include_router(dca_eval_api.router)
app.include_router(safu_config_api.router, prefix="/config")
app.include_router(price_series_router)
app.include_router(dca_simulate_router)
app.include_router(sim_dca_strategy_router)
app.include_router(sim_dca_router)


# === Health Check ===
@app.get("/health")
def health_check(redis: Any = Depends(get_redis)):
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis.ping()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {"redis": "connected", "api": "running"},
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# === Root Endpoint ===
@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <html>
        <head><title>Market7 Dashboard API v2.0</title></head>
        <body>
            <h2>🚀 Market7 Trading Dashboard API v2.0</h2>
            <p>Unified API for Market7 trading system</p>
            <h3>Available Endpoints:</h3>
            <ul>
                <li><a href="/health">/health</a> - Health check</li>
                <li><a href="/api/account/summary">/api/account/summary</a> - Account summary</li>
                <li><a href="/api/trades/active">/api/trades/active</a> - Active trades</li>
                <li><a href="/api/3commas/metrics">/api/3commas/metrics</a> - 3Commas metrics</li>
                <li><a href="/api/btc/context">/api/btc/context</a> - BTC context</li>
                <li><a href="/api/ml/confidence">/api/ml/confidence</a> - ML confidence</li>
                <li><a href="/api/fork/metrics">/api/fork/metrics</a> - Fork metrics</li>
            </ul>
            <p><small>Server time: <code>{datetime.utcnow().isoformat()}</code></small></p>
        </body>
    </html>
    """


# === Account Summary API ===
@app.get("/api/account/summary")
def get_account_summary(redis: Any = Depends(get_redis)):
    """Get account summary with proper data structure"""
    try:
        # Get fork metrics
        fork_metrics = get_fork_trade_metrics()

        # Get 3Commas metrics
        from threecommas_metrics import get_3commas_metrics

        threecommas_data = get_3commas_metrics()

        # Calculate summary
        balance = 25000  # Base balance
        total_pnl = threecommas_data.get("metrics", {}).get("realized_pnl_alltime", 0)
        today_pnl = threecommas_data.get("metrics", {}).get("daily_realized_pnl", 0)
        open_pnl = threecommas_data.get("metrics", {}).get("open_pnl", 0)
        active_trades = len(threecommas_data.get("metrics", {}).get("active_deals", []))

        # Calculate allocated amount
        allocated = sum(
            [
                deal.get("spent_amount", 0)
                for deal in threecommas_data.get("metrics", {}).get("active_deals", [])
            ]
        )

        return {
            "summary": {
                "balance": balance + total_pnl,
                "today_pnl": today_pnl,
                "total_pnl": total_pnl,
                "active_trades": active_trades,
                "allocated": allocated,
                "upnl": open_pnl,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get account summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch account summary")


# === Active Trades API ===
@app.get("/api/trades/active")
def get_active_trades(redis: Any = Depends(get_redis)):
    """Get active trades with proper data structure"""
    try:
        # Get 3Commas active deals
        from threecommas_metrics import get_3commas_metrics

        threecommas_data = get_3commas_metrics()

        active_deals = threecommas_data.get("metrics", {}).get("active_deals", [])

        # Transform to frontend expected format
        dca_trades = []
        for deal in active_deals:
            # Get confidence score from Redis
            symbol = deal.get("pair", "").replace("USDT", "")
            confidence_key = f"confidence_score:{symbol}"
            confidence_score = redis.get_cache(confidence_key)

            if confidence_score:
                try:
                    confidence_score = float(confidence_score)
                except:
                    confidence_score = 0.0
            else:
                confidence_score = 0.0

            dca_trades.append(
                {
                    "deal_id": deal.get("id", ""),
                    "symbol": symbol,
                    "pair": deal.get("pair", ""),
                    "open_pnl": deal.get("open_pnl", 0),
                    "open_pnl_pct": deal.get("open_pnl_pct", 0),
                    "drawdown_pct": deal.get("drawdown_pct", 0),
                    "drawdown_usd": deal.get("drawdown_usd", 0),
                    "step": deal.get("step", 0),
                    "confidence_score": confidence_score,
                    "spent_amount": deal.get("spent_amount", 0),
                    "current_price": deal.get("current_price", 0),
                    "entry_price": deal.get("entry_price", 0),
                }
            )

        return {
            "dca_trades": dca_trades,
            "count": len(dca_trades),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get active trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch active trades")


# === 3Commas Metrics API ===
@app.get("/api/3commas/metrics")
def get_3commas_metrics_api(redis: Any = Depends(get_redis)):
    """Get 3Commas metrics with proper error handling"""
    try:
        from threecommas_metrics import get_3commas_metrics

        return get_3commas_metrics()
    except Exception as e:
        logger.error(f"Failed to get 3Commas metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch 3Commas metrics")


# === BTC Context API ===
@app.get("/api/btc/context")
def get_btc_context(redis: Any = Depends(get_redis)):
    """Get BTC context with proper error handling"""
    try:

        def parse_float(val):
            try:
                if val is None:
                    return 0.0
                return float(str(val).replace("np.float64(", "").replace(")", ""))
            except:
                return 0.0

        return {
            "status": redis.get_cache("cache:btc_condition") or "UNKNOWN",
            "rsi": parse_float(redis.get_cache("indicators:BTC:15m:RSI14")),
            "adx": parse_float(redis.get_cache("indicators:BTC:1h:ADX14")),
            "ema": parse_float(redis.get_cache("indicators:BTC:1h:EMA50")),
            "close": parse_float(redis.get_cache("indicators:BTC:1h:latest_close")),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get BTC context: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch BTC context")


# === Fork Metrics API ===
@app.get("/api/fork/metrics")
def get_fork_metrics(redis: Any = Depends(get_redis)):
    """Get fork metrics with proper error handling"""
    try:
        path = get_path("dashboard_cache") / "fork_metrics.json"
        if path.exists():
            with open(path) as f:
                return json.load(f)
        else:
            return {"error": "Fork metrics file not found"}
    except Exception as e:
        logger.error(f"Failed to get fork metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch fork metrics")


# === ML Confidence API ===
@app.get("/api/ml/confidence")
def get_ml_confidence(redis: Any = Depends(get_redis)):
    """Get ML confidence data"""
    try:
        # Get confidence data from Redis
        confidence_data = redis.get_cache("ml_confidence_data")
        if confidence_data:
            return json.loads(confidence_data)
        else:
            return {"error": "No ML confidence data available"}
    except Exception as e:
        logger.error(f"Failed to get ML confidence: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch ML confidence data"
        )


# === Trade Health API ===
@app.get("/api/trade-health/{symbol}")
def get_trade_health(symbol: str, redis: Any = Depends(get_redis)):
    """Get trade health for specific symbol"""
    try:
        redis_key = f"trade_health:{symbol.upper()}"
        raw = redis.get_cache(redis_key)

        if not raw:
            raise HTTPException(status_code=404, detail="No data found for symbol")

        try:
            return {
                "symbol": symbol.upper(),
                "score": int(raw),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid data format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trade health for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trade health")


# === Legacy Endpoints (for backward compatibility) ===
@app.get("/btc/context")
def get_btc_context_legacy(redis: Any = Depends(get_redis)):
    """Legacy BTC context endpoint"""
    return get_btc_context(redis)


@app.get("/fork/metrics")
def get_fork_metrics_legacy(redis: Any = Depends(get_redis)):
    """Legacy fork metrics endpoint"""
    return get_fork_metrics(redis)


@app.get("/active-trades")
def get_active_trades_legacy(redis: Any = Depends(get_redis)):
    """Legacy active trades endpoint"""
    return get_active_trades(redis)


@app.get("/3commas/metrics")
def get_3commas_metrics_legacy(redis: Any = Depends(get_redis)):
    """Legacy 3Commas metrics endpoint"""
    return get_3commas_metrics_api(redis)


@app.get("/ml/confidence")
def get_ml_confidence_legacy(redis: Any = Depends(get_redis)):
    """Legacy ML confidence endpoint"""
    return get_ml_confidence(redis)


@app.get("/trade-health/{symbol}")
def get_trade_health_legacy(symbol: str, redis: Any = Depends(get_redis)):
    """Legacy trade health endpoint"""
    return get_trade_health(symbol, redis)


if __name__ == "__main__":
import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
