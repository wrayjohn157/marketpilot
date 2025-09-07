import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

"""
Trades API Routes
Handles active trades and trade management
"""

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/trades/active")
def get_active_trades_enhanced() -> Dict[str, Any]:
    """
    Enhanced active trades endpoint with full enrichment
    """
    try:
        # Mock data for now - replace with real 3Commas API calls
        mock_trades = [
            {
                "deal_id": "2372577387",
                "symbol": "BTC",
                "pair": "USDT_BTC",
                "status": "bought",
                "spent_amount": 200.68,
                "current_price": 110799.5,
                "entry_price": 110871.95,
                "bought_volume": 200.68,
                "bought_amount": 0.00181,
                "open_pnl": -0.4,
                "open_pnl_pct": -0.07,
                "price_change_pct": -0.07,
                "trade_age_hours": 3.0,
                "created_at": "2025-09-05T23:11:14.427Z",
                "updated_at": "2025-09-05T23:11:14.941Z",
                "bot_id": "16477920",
                "max_safety_orders": 0,
                "active_safety_orders_count": 0,
                "health_score": 50.0,
                "confidence_score": 60.0,
            }
        ]

        # Calculate summary metrics
        total_open_pnl = sum(trade.get("open_pnl", 0) for trade in mock_trades)
        total_deals = len(mock_trades)

        summary = {
            "open_pnl": total_open_pnl,
            "daily_realized_pnl": 0.0,
            "realized_pnl_alltime": 0.0,
            "total_deals": total_deals,
            "win_rate": 0.0,
            "active_deals_count": total_deals,
        }

        return {
            "trades": mock_trades,
            "count": len(mock_trades),
            "summary": summary,
            "timestamp": datetime.now(datetime.UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get enhanced active trades: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch active trades: {e}"
        )


@router.get("/active-trades")
def get_active_trades_legacy() -> Dict[str, Any]:
    """Legacy active trades endpoint"""
    return get_active_trades_enhanced()


@router.get("/trade-health/{symbol}")
def get_trade_health(symbol: str) -> Dict[str, Any]:
    """Get health score for a specific trade symbol"""
    try:
        # Mock health data
        return {
            "symbol": symbol.upper(),
            "health_score": 75.0,
            "confidence_score": 80.0,
            "last_updated": datetime.now(datetime.UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get trade health for {symbol}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch trade health: {e}"
        )
