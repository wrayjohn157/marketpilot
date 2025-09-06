"""
Trades API Routes - Market7 Style
Modular route for active trades and trade management
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Import our enhanced functions
from enhanced_dashboard_api import (
    get_3commas_credentials, 
    get_active_deals, 
    enrich_active_deals,
    get_redis_client
)

@router.get("/active-trades")
def get_active_trades_legacy() -> Dict[str, Any]:
    """
    Legacy active trades endpoint for Market7 compatibility
    Returns simplified format for backward compatibility
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Get active deals
        active_deals = get_active_deals(bot_id)
        
        # Transform to legacy format
        trades = []
        for deal in active_deals:
            symbol = deal.get('pair', '').replace('USDT_', '')
            # Calculate simple health score (0-100 based on PnL)
            pnl_pct = float(deal.get('final_profit_percentage', 0))
            health_score = max(0, min(100, 50 + (pnl_pct * 2)))
            
            trades.append({
                "symbol": symbol,
                "score": int(health_score)
            })
        
        return trades
        
    except Exception as e:
        logger.error(f"Failed to get legacy active trades: {e}")
        return []

@router.get("/api/trades/active")
def get_active_trades_enhanced() -> Dict[str, Any]:
    """
    Enhanced active trades endpoint with full enrichment
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Get active deals
        active_deals = get_active_deals(bot_id)
        
        # Enrich with additional metrics
        enriched_deals = enrich_active_deals(active_deals)
        
        # Calculate summary metrics
        total_open_pnl = sum(deal['open_pnl'] for deal in enriched_deals)
        total_spent = sum(deal['spent_amount'] for deal in enriched_deals)
        avg_health = sum(deal['health_score'] for deal in enriched_deals) / len(enriched_deals) if enriched_deals else 0
        
        return {
            "trades": enriched_deals,
            "count": len(enriched_deals),
            "summary": {
                "total_open_pnl": round(total_open_pnl, 2),
                "total_spent": round(total_spent, 2),
                "average_health": round(avg_health, 1)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get enhanced active trades: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch active trades: {e}")

@router.get("/trade-health/{symbol}")
def get_trade_health(symbol: str) -> Dict[str, Any]:
    """
    Get health score for specific trade symbol
    """
    try:
        # Try Redis cache first
        redis_client = get_redis_client()
        if redis_client:
            cached_score = redis_client.get(f"trade_health:{symbol.upper()}")
            if cached_score:
                return {
                    "symbol": symbol.upper(),
                    "score": int(cached_score),
                    "source": "cache"
                }
        
        # Fallback to calculating from active trades
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        active_deals = get_active_deals(bot_id)
        
        # Find the specific trade
        for deal in active_deals:
            deal_symbol = deal.get('pair', '').replace('USDT_', '')
            if deal_symbol.upper() == symbol.upper():
                pnl_pct = float(deal.get('final_profit_percentage', 0))
                health_score = max(0, min(100, 50 + (pnl_pct * 2)))
                
                # Cache the result
                if redis_client:
                    redis_client.setex(f"trade_health:{symbol.upper()}", 300, int(health_score))
                
                return {
                    "symbol": symbol.upper(),
                    "score": int(health_score),
                    "source": "calculated"
                }
        
        return {"error": "Trade not found"}
        
    except Exception as e:
        logger.error(f"Failed to get trade health for {symbol}: {e}")
        return {"error": "Failed to calculate health"}

