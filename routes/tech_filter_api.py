"""
Tech Filter API Routes
Provides technical analysis and filtering endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Import Redis client
from enhanced_dashboard_api import get_redis_client

@router.get("/tech-filter/indicators/{symbol}")
def get_tech_filter_indicators(symbol: str) -> Dict[str, Any]:
    """
    Get technical indicators for a specific symbol
    """
    try:
        redis_client = get_redis_client()
        
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis not available")
        
        # Get complete indicator set
        key = f"tech_filter:{symbol}:1h:complete"
        data = redis_client.get(key)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No tech filter data for {symbol}")
        
        indicators = json.loads(data)
        
        return {
            "symbol": symbol,
            "timeframe": "1h",
            "indicators": indicators,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get tech filter indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch indicators: {e}")

@router.get("/tech-filter/score/{symbol}")
def get_tech_filter_score(symbol: str) -> Dict[str, Any]:
    """
    Get tech filter score for a specific symbol
    """
    try:
        redis_client = get_redis_client()
        
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis not available")
        
        # Get complete indicator set
        key = f"tech_filter:{symbol}:1h:complete"
        data = redis_client.get(key)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No tech filter data for {symbol}")
        
        indicators = json.loads(data)
        tech_score = indicators.get('tech_filter_score', 0.5)
        
        return {
            "symbol": symbol,
            "tech_filter_score": tech_score,
            "market_status": indicators.get('market_status', 'UNKNOWN'),
            "rsi": indicators['indicators']['rsi'],
            "macd": indicators['indicators']['macd'],
            "adx": indicators['indicators']['adx'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get tech filter score for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch score: {e}")

@router.get("/tech-filter/all")
def get_all_tech_filter_data() -> Dict[str, Any]:
    """
    Get tech filter data for all symbols
    """
    try:
        redis_client = get_redis_client()
        
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis not available")
        
        # Get all tech filter keys
        pattern = "tech_filter:*:1h:complete"
        keys = redis_client.keys(pattern)
        
        all_data = []
        for key in keys:
            try:
                data = redis_client.get(key)
                if data:
                    indicators = json.loads(data)
                    all_data.append(indicators)
            except Exception as e:
                logger.warning(f"Failed to parse data for key {key}: {e}")
                continue
        
        return {
            "symbols": all_data,
            "count": len(all_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get all tech filter data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {e}")

@router.get("/tech-filter/signals")
def get_tech_filter_signals() -> Dict[str, Any]:
    """
    Get trading signals based on tech filter analysis
    """
    try:
        redis_client = get_redis_client()
        
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis not available")
        
        # Get all tech filter data
        pattern = "tech_filter:*:1h:complete"
        keys = redis_client.keys(pattern)
        
        signals = []
        for key in keys:
            try:
                data = redis_client.get(key)
                if data:
                    indicators = json.loads(data)
                    symbol = indicators['symbol']
                    tech_score = indicators.get('tech_filter_score', 0.5)
                    market_status = indicators.get('market_status', 'UNKNOWN')
                    
                    # Generate signal based on score and status
                    if tech_score > 0.7 and market_status in ['BULLISH', 'TRENDING']:
                        signal = "BUY"
                        strength = "STRONG" if tech_score > 0.8 else "MEDIUM"
                    elif tech_score < 0.3 and market_status in ['BEARISH', 'TRENDING']:
                        signal = "SELL"
                        strength = "STRONG" if tech_score < 0.2 else "MEDIUM"
                    else:
                        signal = "HOLD"
                        strength = "WEAK"
                    
                    signals.append({
                        "symbol": symbol,
                        "signal": signal,
                        "strength": strength,
                        "score": tech_score,
                        "status": market_status,
                        "rsi": indicators['indicators']['rsi'],
                        "macd": indicators['indicators']['macd'],
                        "adx": indicators['indicators']['adx']
                    })
            except Exception as e:
                logger.warning(f"Failed to process signal for key {key}: {e}")
                continue
        
        return {
            "signals": signals,
            "count": len(signals),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get tech filter signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch signals: {e}")

