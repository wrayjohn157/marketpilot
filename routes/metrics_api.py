"""
Metrics API Routes - Market7 Style
Modular route for 3Commas metrics and performance data
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Import our enhanced functions
from enhanced_dashboard_api import (
    get_3commas_credentials,
    get_active_deals,
    get_finished_deals,
    calculate_performance_metrics,
    enrich_active_deals,
    get_redis_client
)

@router.get("/3commas/metrics")
def get_3commas_metrics():
    """
    Market7 compatible 3Commas metrics endpoint
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Get active and finished deals
        active_deals = get_active_deals(bot_id)
        finished_deals = get_finished_deals(bot_id, limit=200)
        
        # Calculate performance metrics
        perf_metrics = calculate_performance_metrics(finished_deals)
        
        # Calculate open PnL
        open_pnl = sum(float(deal.get('usd_final_profit', 0)) for deal in active_deals)
        
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
                    "largest_loss": perf_metrics["largest_loss"]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get 3Commas metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {e}")

@router.get("/api/3commas/metrics")
def get_enhanced_3commas_metrics():
    """
    Enhanced API endpoint (alias for consistency)
    """
    return get_3commas_metrics()

@router.get("/fork/metrics")
def get_fork_metrics():
    """
    Fork metrics endpoint (Market7 compatibility)
    Returns enhanced active trades data formatted for fork analysis
    """
    try:
        # Use the enhanced trades endpoint data
        from routes.trades_api import get_active_trades_enhanced
        trades_data = get_active_trades_enhanced()
        
        # Transform to fork metrics format
        fork_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_trades": trades_data["count"],
            "total_pnl": trades_data["summary"]["total_open_pnl"],
            "average_health": trades_data["summary"]["average_health"],
            "trades": []
        }
        
        # Add trade details for fork analysis
        for trade in trades_data["trades"]:
            fork_metrics["trades"].append({
                "symbol": trade["symbol"],
                "pnl": trade["open_pnl"],
                "pnl_pct": trade["open_pnl_pct"],
                "health_score": trade["health_score"],
                "confidence_score": trade["confidence_score"],
                "trade_age_hours": trade["trade_age_hours"]
            })
        
        return fork_metrics
        
    except Exception as e:
        logger.error(f"Failed to get fork metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch fork metrics: {e}")

@router.get("/api/performance/stats")
def get_performance_stats():
    """
    Detailed performance statistics
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
        from datetime import timedelta
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        weekly_pnl = 0
        monthly_pnl = 0
        
        for deal in finished_deals:
            if deal.get('closed_at'):
                try:
                    closed_time = datetime.fromisoformat(deal['closed_at'].replace('Z', '+00:00'))
                    profit = float(deal.get('usd_final_profit', 0))
                    
                    if closed_time >= week_ago:
                        weekly_pnl += profit
                    if closed_time >= month_ago:
                        monthly_pnl += profit
                    except Exception:
                        pass
        
        return {
            "bot_id": bot_id,
            "performance": {
                **perf_metrics,
                "weekly_realized_pnl": round(weekly_pnl, 2),
                "monthly_realized_pnl": round(monthly_pnl, 2),
                "current_active_trades": len(active_deals),
                "total_open_pnl": round(sum(float(deal.get('usd_final_profit', 0)) for deal in active_deals), 2)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance stats: {e}")

