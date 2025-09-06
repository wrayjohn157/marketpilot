"""
BTC Context API Routes - Market7 Style
Modular route for BTC market context and indicators
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Import Redis client
from enhanced_dashboard_api import get_redis_client

@router.get("/btc/context")
def get_btc_context():
    """
    BTC market context endpoint (Market7 compatible)
    """
    def parse_float(val):
        try:
            if val is None:
                return 0.0
            return float(str(val).replace("np.float64(", "").replace(")", ""))
        except:
            return 0.0

    try:
        redis_client = get_redis_client()
        
        if redis_client:
            # Try to get real data from Redis (Market7 style keys)
            btc_condition = redis_client.get("cache:btc_condition") or redis_client.get("btc_condition")
            rsi = redis_client.get("indicators:BTC:15m:RSI14") or redis_client.get("BTC_15m_RSI14")
            adx = redis_client.get("indicators:BTC:1h:ADX14") or redis_client.get("BTC_1h_ADX14")
            ema = redis_client.get("indicators:BTC:1h:EMA50") or redis_client.get("BTC_1h_EMA50")
            close = redis_client.get("indicators:BTC:1h:latest_close") or redis_client.get("BTC_1h_latest_close")
            
            return {
                "status": btc_condition or "BULLISH",
                "rsi": parse_float(rsi) or 45.2,
                "adx": parse_float(adx) or 28.5,
                "ema": parse_float(ema) or 110500.0,
                "close": parse_float(close) or 110850.0,
                "sentiment": "positive" if (parse_float(rsi) or 45) < 70 else "negative",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Fallback to mock data when Redis unavailable
            return {
                "status": "BULLISH",
                "rsi": 45.2,
                "adx": 28.5,
                "ema": 110500.0,
                "close": 110850.0,
                "sentiment": "positive",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get BTC context: {e}")
        # Return mock data on error
        return {
            "status": "UNKNOWN",
            "rsi": 50.0,
            "adx": 25.0,
            "ema": 110000.0,
            "close": 110000.0,
            "sentiment": "neutral",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/api/btc/context")
def get_btc_context_enhanced():
    """
    Enhanced API endpoint (alias for consistency)
    """
    return get_btc_context()

@router.get("/btc/indicators")
def get_btc_indicators():
    """
    Extended BTC indicators endpoint
    """
    try:
        redis_client = get_redis_client()
        
        indicators = {}
        
        if redis_client:
            # Comprehensive indicator set
            indicator_keys = [
                "BTC_1m_RSI14", "BTC_5m_RSI14", "BTC_15m_RSI14", "BTC_1h_RSI14", "BTC_4h_RSI14",
                "BTC_1h_ADX14", "BTC_4h_ADX14",
                "BTC_1h_EMA20", "BTC_1h_EMA50", "BTC_1h_EMA200",
                "BTC_1h_latest_close", "BTC_1h_latest_volume",
                "BTC_4h_latest_close", "BTC_4h_latest_volume"
            ]
            
            for key in indicator_keys:
                value = redis_client.get(key) or redis_client.get(f"indicators:BTC:{key}")
                if value:
                    try:
                        indicators[key] = float(str(value).replace("np.float64(", "").replace(")", ""))
                    except:
                        indicators[key] = str(value)
        
        # Add calculated indicators
        if "BTC_1h_latest_close" in indicators and "BTC_1h_EMA50" in indicators:
            price = indicators["BTC_1h_latest_close"]
            ema50 = indicators["BTC_1h_EMA50"]
            indicators["price_vs_ema50_pct"] = round(((price - ema50) / ema50) * 100, 2)
        
        return {
            "indicators": indicators,
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(indicators)
        }
        
    except Exception as e:
        logger.error(f"Failed to get BTC indicators: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BTC indicators: {e}")

