"""
Enhanced MarketPilot Dashboard API
Inspired by Market7 architecture with comprehensive 3Commas integration
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with CORS
app = FastAPI(title="MarketPilot Dashboard API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Configuration ===


def get_3commas_credentials():
    """Load 3Commas credentials"""
    try:
        with open(
            "/home/signal/marketpilot/config/credentials/3commas_default.json", "r"
        ) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load 3Commas credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to load credentials")


def get_redis_client():
    """Get Redis client for caching"""
    try:
        return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        return None


# === 3Commas API Client ===


def make_3commas_request(path: str, params: Dict = None) -> requests.Response:
    """
    Make authenticated request to 3Commas API
    Following market7 architecture with proper error handling
    """
    try:
        creds = get_3commas_credentials()
        api_key = creds["3commas_api_key"]
        api_secret = creds["3commas_api_secret"]

        # Build query string if params provided
        query_string = ""
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        # Create signature - 3Commas uses just the path for signature
        message = f"{path}?{query_string}" if query_string else path
        signature = hmac.new(
            api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        headers = {
            "APIKEY": api_key,
            "Signature": signature,
            "Content-Type": "application/json",
        }

        # Build full URL
        url = f"https://api.3commas.io{path}"
        if query_string:
            url += f"?{query_string}"

        logger.debug(f"3Commas API call: {url}")
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            logger.warning(
                f"3Commas API returned {response.status_code}: {response.text[:200]}"
            )

        return response

    except Exception as e:
        logger.error(f"3Commas API request failed: {e}")
        raise


# === Core Data Functions (Market7 Style) ===


def get_active_deals(bot_id: str, use_cache: bool = True) -> List[Dict]:
    """
    Get active deals for specific bot with caching
    Market7 pattern: Cached retrieval with fallback
    """
    cache_key = f"active_deals_{bot_id}"
    redis_client = get_redis_client()

    # Try cache first
    if use_cache and redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached active deals for bot {bot_id}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

    # Fetch from 3Commas
    try:
        response = make_3commas_request(
            "/public/api/ver1/deals", {"scope": "active", "bot_id": bot_id}
        )

        if response.status_code == 200:
            deals = response.json()
            logger.info(f"Fetched {len(deals)} active deals for bot {bot_id}")

            # Cache for 1 minute
            if redis_client:
                try:
                    redis_client.setex(cache_key, 60, json.dumps(deals))
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")

            return deals
        else:
            logger.error(f"Failed to fetch active deals: {response.status_code}")
            return []

    except Exception as e:
        logger.error(f"Error fetching active deals: {e}")
        return []


def get_finished_deals(
    bot_id: str, limit: int = 100, use_cache: bool = True
) -> List[Dict]:
    """
    Get finished deals for performance analysis
    Market7 pattern: Historical performance tracking
    """
    cache_key = f"finished_deals_{bot_id}_{limit}"
    redis_client = get_redis_client()

    # Try cache first (5 minute TTL for historical data)
    if use_cache and redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached finished deals for bot {bot_id}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

    # Fetch from 3Commas
    try:
        response = make_3commas_request(
            "/public/api/ver1/deals",
            {"scope": "finished", "bot_id": bot_id, "limit": str(limit)},
        )

        if response.status_code == 200:
            deals = response.json()
            logger.info(f"Fetched {len(deals)} finished deals for bot {bot_id}")

            # Cache for 5 minutes
            if redis_client:
                try:
                    redis_client.setex(cache_key, 300, json.dumps(deals))
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")

            return deals
        else:
            logger.error(f"Failed to fetch finished deals: {response.status_code}")
            return []

    except Exception as e:
        logger.error(f"Error fetching finished deals: {e}")
        return []


def calculate_performance_metrics(finished_deals: List[Dict]) -> Dict:
    """
    Calculate comprehensive performance metrics
    Market7 pattern: Multi-dimensional performance analysis
    """
    if not finished_deals:
        return {
            "total_realized_pnl": 0,
            "daily_realized_pnl": 0,
            "win_rate": 0,
            "total_deals": 0,
            "profitable_deals": 0,
            "average_profit": 0,
            "average_loss": 0,
            "largest_win": 0,
            "largest_loss": 0,
        }

    total_realized_pnl = 0
    daily_realized_pnl = 0
    profitable_deals = 0
    profits = []
    losses = []
    today = datetime.now(datetime.UTC).date()

    for deal in finished_deals:
        profit = float(deal.get("usd_final_profit", 0))
        total_realized_pnl += profit

        if profit > 0:
            profitable_deals += 1
            profits.append(profit)
        elif profit < 0:
            losses.append(profit)

        # Check if deal was closed today
        if deal.get("closed_at"):
            try:
                closed_date = datetime.fromisoformat(
                    deal["closed_at"].replace("Z", "+00:00")
                ).date()
                if closed_date == today:
                    daily_realized_pnl += profit
            except:
                pass

    win_rate = (profitable_deals / len(finished_deals) * 100) if finished_deals else 0

    return {
        "total_realized_pnl": round(total_realized_pnl, 2),
        "daily_realized_pnl": round(daily_realized_pnl, 2),
        "win_rate": round(win_rate, 1),
        "total_deals": len(finished_deals),
        "profitable_deals": profitable_deals,
        "average_profit": round(sum(profits) / len(profits), 2) if profits else 0,
        "average_loss": round(sum(losses) / len(losses), 2) if losses else 0,
        "largest_win": round(max(profits), 2) if profits else 0,
        "largest_loss": round(min(losses), 2) if losses else 0,
    }


def enrich_active_deals(active_deals: List[Dict]) -> List[Dict]:
    """
    Enrich active deals with additional metrics
    Market7 pattern: Trade health and confidence scoring
    """
    enriched = []

    for deal in active_deals:
        # Calculate basic metrics
        current_price = float(deal.get("current_price", 0))
        entry_price = float(deal.get("bought_average_price", 0))
        bought_volume = float(
            deal.get("bought_volume", 0)
        )  # This is already in USDT (spent amount)
        bought_amount = float(
            deal.get("bought_amount", 0)
        )  # This is the crypto quantity
        spent_amount = bought_volume  # bought_volume is already the USDT spent

        # Calculate price change percentage
        price_change_pct = (
            ((current_price - entry_price) / entry_price * 100)
            if entry_price > 0
            else 0
        )

        # Calculate trade age
        created_at = deal.get("created_at", "")
        trade_age_hours = 0
        if created_at:
            try:
                created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                trade_age_hours = (
                    datetime.now(datetime.UTC).replace(tzinfo=created_time.tzinfo)
                    - created_time
                ).total_seconds() / 3600
            except:
                pass

        # Enrich the deal
        enriched_deal = {
            "deal_id": str(deal.get("id")),
            "symbol": deal.get("pair", "").replace("USDT_", ""),
            "pair": deal.get("pair"),
            "status": deal.get("status"),
            "spent_amount": round(
                spent_amount, 2
            ),  # Now correctly using bought_volume (USDT spent)
            "current_price": current_price,
            "entry_price": entry_price,
            "bought_volume": round(bought_volume, 2),  # USDT spent
            "bought_amount": round(bought_amount, 8),  # Crypto quantity
            "open_pnl": float(
                deal.get("actual_usd_profit", deal.get("usd_final_profit", 0))
            ),
            "open_pnl_pct": float(deal.get("final_profit_percentage", 0)),
            "price_change_pct": round(price_change_pct, 2),
            "trade_age_hours": round(trade_age_hours, 1),
            "created_at": created_at,
            "updated_at": deal.get("updated_at", ""),
            "bot_id": str(deal.get("bot_id")),
            "max_safety_orders": deal.get("max_safety_orders", 0),
            "active_safety_orders_count": deal.get("active_safety_orders_count", 0),
            # Market7-style health indicators
            "health_score": calculate_trade_health(deal),
            "confidence_score": calculate_confidence_score(deal),
        }

        enriched.append(enriched_deal)

    return enriched


def calculate_trade_health(deal: Dict) -> float:
    """Calculate trade health score (0-100)"""
    # Simple health calculation based on PnL and age
    pnl_pct = float(deal.get("final_profit_percentage", 0))

    # Health starts at 50 (neutral)
    health = 50.0

    # Adjust based on PnL (-50 to +50)
    health += min(max(pnl_pct * 2, -50), 50)

    # Ensure 0-100 range
    return max(0, min(100, health))


def calculate_confidence_score(deal: Dict) -> float:
    """Calculate ML confidence score (0-100)"""
    # Placeholder - in market7 this used ML models
    # For now, base on trade performance and volume
    pnl_pct = float(deal.get("final_profit_percentage", 0))

    # Base confidence on current performance
    if pnl_pct > 5:
        return 85.0
    elif pnl_pct > 0:
        return 70.0
    elif pnl_pct > -5:
        return 60.0
    elif pnl_pct > -10:
        return 40.0
    else:
        return 25.0


# === API Endpoints (Market7 Compatible) ===


@app.get("/", response_class=HTMLResponse)
def root():
    """Landing page with API information"""
    return """
    <html><head><title>MarketPilot Dashboard API v2.0</title></head>
    <body style="font-family: Arial; margin: 40px;">
        <h1>🚀 MarketPilot Dashboard API v2.0</h1>
        <p><strong>Enhanced with Market7 Architecture</strong></p>

        <h2>📊 Available Endpoints:</h2>
        <ul>
            <li><a href="/health">🏥 Health Check</a></li>
            <li><a href="/api/trades/active">📈 Active Trades</a></li>
            <li><a href="/api/3commas/metrics">📊 3Commas Metrics</a></li>
            <li><a href="/api/account/summary">💰 Account Summary</a></li>
            <li><a href="/api/btc/context">₿ BTC Context</a></li>
            <li><a href="/api/performance/stats">📈 Performance Stats</a></li>
        </ul>

        <h2>🔗 External Links:</h2>
        <ul>
            <li><a href="http://155.138.202.35:3001" target="_blank">📱 Frontend Dashboard</a></li>
            <li><a href="/docs" target="_blank">📚 API Documentation</a></li>
        </ul>

        <p><em>Powered by MarketPilot • Inspired by Market7</em></p>
    </body></html>
    """


@app.get("/health")
def health_check():
    """Comprehensive health check"""
    try:
        # Test Redis
        redis_client = get_redis_client()
        redis_status = (
            "healthy" if redis_client and redis_client.ping() else "unhealthy"
        )

        # Test 3Commas API
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]

        # Quick API test
        try:
            response = make_3commas_request(
                "/public/api/ver1/deals",
                {"scope": "active", "bot_id": bot_id, "limit": "1"},
            )
            api_status = (
                "healthy"
                if response.status_code == 200
                else f"unhealthy_{response.status_code}"
            )
        except:
            api_status = "unhealthy_connection"

        return {
            "status": (
                "healthy"
                if redis_status == "healthy" and "healthy" in api_status
                else "degraded"
            ),
            "timestamp": datetime.now(datetime.UTC).isoformat(),
            "services": {
                "redis": redis_status,
                "3commas_api": api_status,
                "bot_id": bot_id,
            },
            "version": "2.0.0",
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/api/trades/active")
def get_active_trades_api():
    """
    Get active trades with enrichment
    Market7 compatible endpoint
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]

        # Get active deals
        active_deals = get_active_deals(bot_id)

        # Enrich with additional metrics
        enriched_deals = enrich_active_deals(active_deals)

        # Calculate summary metrics
        total_open_pnl = sum(deal["open_pnl"] for deal in enriched_deals)
        total_spent = sum(deal["spent_amount"] for deal in enriched_deals)
        avg_health = (
            sum(deal["health_score"] for deal in enriched_deals) / len(enriched_deals)
            if enriched_deals
            else 0
        )

        return {
            "trades": enriched_deals,
            "count": len(enriched_deals),
            "summary": {
                "total_open_pnl": round(total_open_pnl, 2),
                "total_spent": round(total_spent, 2),
                "average_health": round(avg_health, 1),
            },
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get active trades: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch active trades: {e}"
        )


@app.get("/api/3commas/metrics")
def get_comprehensive_metrics():
    """
    Comprehensive 3Commas metrics
    Market7 style with performance analysis
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]

        # Get active and finished deals
        active_deals = get_active_deals(bot_id)
        finished_deals = get_finished_deals(bot_id, limit=200)

        # Calculate performance metrics
        perf_metrics = calculate_performance_metrics(finished_deals)

        # Calculate open PnL using actual_usd_profit (what 3Commas dashboard shows)
        open_pnl = sum(
            float(deal.get("actual_usd_profit", deal.get("usd_final_profit", 0)))
            for deal in active_deals
        )

        # Enrich active deals
        enriched_active = enrich_active_deals(active_deals)

        return {
            "bot_id": bot_id,
            "metrics": {
                "open_pnl": round(open_pnl, 2),
                "daily_realized_pnl": perf_metrics["daily_realized_pnl"],
                "realized_pnl_alltime": perf_metrics["total_realized_pnl"],
                "total_deals": perf_metrics["total_deals"],
                "win_rate": perf_metrics["win_rate"],
                "active_deals_count": len(active_deals),
                "active_deals": enriched_active[:10],  # Limit for performance
                "performance": {
                    "profitable_deals": perf_metrics["profitable_deals"],
                    "average_profit": perf_metrics["average_profit"],
                    "average_loss": perf_metrics["average_loss"],
                    "largest_win": perf_metrics["largest_win"],
                    "largest_loss": perf_metrics["largest_loss"],
                },
            },
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get 3Commas metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {e}")


@app.get("/api/performance/stats")
def get_performance_stats():
    """
    Detailed performance statistics
    Market7 style analytics endpoint
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]

        # Get comprehensive deal history
        finished_deals = get_finished_deals(bot_id, limit=500)
        active_deals = get_active_deals(bot_id)

        # Calculate extended metrics
        perf_metrics = calculate_performance_metrics(finished_deals)

        # Calculate weekly/monthly performance
        now = datetime.now(datetime.UTC)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        weekly_pnl = 0
        monthly_pnl = 0

        for deal in finished_deals:
            if deal.get("closed_at"):
                try:
                    closed_time = datetime.fromisoformat(
                        deal["closed_at"].replace("Z", "+00:00")
                    )
                    profit = float(deal.get("usd_final_profit", 0))

                    if closed_time >= week_ago:
                        weekly_pnl += profit
                    if closed_time >= month_ago:
                        monthly_pnl += profit
                except:
                    pass

        return {
            "bot_id": bot_id,
            "performance": {
                **perf_metrics,
                "weekly_realized_pnl": round(weekly_pnl, 2),
                "monthly_realized_pnl": round(monthly_pnl, 2),
                "current_active_trades": len(active_deals),
                "total_open_pnl": round(
                    sum(
                        float(deal.get("usd_final_profit", 0)) for deal in active_deals
                    ),
                    2,
                ),
            },
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch performance stats: {e}"
        )


# Keep existing endpoints for compatibility
@app.get("/api/account/summary")
def get_account_summary():
    """Account summary endpoint"""
    try:
        trades_response = get_active_trades_api()
        trades = trades_response.get("trades", [])
        summary = trades_response.get("summary", {})

        return {
            "summary": {
                "balance": 10000.0,  # Mock - would need account API
                "today_pnl": summary.get("total_open_pnl", 0),
                "total_pnl": summary.get("total_open_pnl", 0),
                "active_trades": len(trades),
                "allocated": summary.get("total_spent", 0),
                "upnl": summary.get("total_open_pnl", 0),
            },
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get account summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch account summary: {e}"
        )


@app.get("/api/btc/context")
def get_btc_context():
    """BTC market context"""
    return {
        "status": "BULLISH",
        "rsi": 45.2,
        "adx": 28.5,
        "ema": 110500.0,
        "close": 110850.0,
        "sentiment": "positive",
        "timestamp": datetime.now(datetime.UTC).isoformat(),
    }


@app.get("/api/fork/metrics")
def get_fork_metrics():
    """Fork metrics (redirect to active trades)"""
    return get_active_trades_api()


@app.get("/api/ml/confidence")
def get_ml_confidence():
    """ML confidence data"""
    return {
        "confidence": 0.85,
        "model_version": "v2.1",
        "last_updated": datetime.now(datetime.UTC).isoformat(),
    }


@app.get("/api/trade-health/{symbol}")
def get_trade_health(symbol: str):
    """Trade health for specific symbol"""
    return {
        "symbol": symbol,
        "score": 0.75,
        "health": "good",
        "recommendations": ["hold", "monitor"],
        "timestamp": datetime.now(datetime.UTC).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
