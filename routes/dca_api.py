"""
DCA API Routes - Market7 Compatible
Provides the exact endpoints and data formats that Market7 frontend expects
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
    enrich_active_deals,
    make_3commas_request,
    get_redis_client
)

@router.get("/dca-trades-active")
def get_dca_trades_active():
    """
    Market7 compatible DCA trades endpoint
    Returns active trades in the exact format the frontend expects
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Get active deals
        active_deals = get_active_deals(bot_id)
        enriched_deals = enrich_active_deals(active_deals)
        
        # Transform to Market7 DCA trades format
        dca_trades = []
        for deal in enriched_deals:
            # Generate sparkline data (mock for now - could be enhanced with real price history)
            current_price = deal['current_price']
            entry_price = deal['entry_price']
            price_range = abs(current_price - entry_price) * 0.1
            sparkline_data = [
                current_price - price_range,
                current_price - price_range * 0.5,
                current_price - price_range * 0.2,
                current_price,
                current_price + price_range * 0.1
            ]
            
            dca_trade = {
                "deal_id": int(deal['deal_id']),
                "symbol": deal['pair'],  # Keep full USDT_BTC format for Market7 compatibility
                "step": deal.get('active_safety_orders_count', 0) + 1,  # DCA step (1 = base order)
                "current_price": deal['current_price'],
                "avg_entry_price": deal['entry_price'],
                "open_pnl": deal['open_pnl'],
                "sparkline_data": sparkline_data,
                "entry_score": deal['confidence_score'] / 100.0,  # Convert to 0-1 scale
                "current_score": deal['health_score'] / 100.0,    # Convert to 0-1 scale  
                "confidence_score": deal['confidence_score'] / 100.0,
                # Additional Market7 fields
                "pnl_pct": deal['open_pnl_pct'],
                "trade_age_hours": deal['trade_age_hours'],
                "spent_amount": deal['spent_amount'],
                "bought_amount": deal['bought_amount'],
                "status": deal['status'],
                "created_at": deal['created_at'],
                "bot_id": deal['bot_id']
            }
            dca_trades.append(dca_trade)
        
        return {
            "count": len(dca_trades),
            "dca_trades": dca_trades,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get DCA trades: {e}")
        # Return empty result for graceful degradation
        return {
            "count": 0,
            "dca_trades": [],
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/dca-evals")
def get_dca_evaluations():
    """
    DCA evaluation data for individual trade cards
    Market7 compatible endpoint
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Get active deals
        active_deals = get_active_deals(bot_id)
        enriched_deals = enrich_active_deals(active_deals)
        
        # Transform to evaluation format
        evaluations = []
        for deal in enriched_deals:
            evaluation = {
                "deal_id": int(deal['deal_id']),
                "symbol": deal['symbol'],
                "current_price": deal['current_price'],
                "entry_price": deal['entry_price'],
                "open_pnl": deal['open_pnl'],
                "pnl_pct": deal['open_pnl_pct'],
                "confidence_score": deal['confidence_score'] / 100.0,
                "health_score": deal['health_score'] / 100.0,
                "dca_step": deal.get('active_safety_orders_count', 0) + 1,
                "should_dca": deal['health_score'] < 40,  # Suggest DCA if health is poor
                "next_dca_price": deal['entry_price'] * 0.95,  # 5% below entry as example
                "max_dca_steps": deal.get('max_safety_orders', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            evaluations.append(evaluation)
        
        return {
            "evaluations": evaluations,
            "count": len(evaluations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get DCA evaluations: {e}")
        return {
            "evaluations": [],
            "count": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/refresh-price/{deal_id}")
def refresh_price(deal_id: str):
    """
    Refresh live price for a specific deal
    Market7 compatible endpoint for real-time updates
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Get active deals and find the specific one
        active_deals = get_active_deals(bot_id)
        
        for deal in active_deals:
            if str(deal.get('id')) == str(deal_id):
                # Calculate real-time PnL
                current_price = float(deal.get('current_price', 0))
                entry_price = float(deal.get('bought_average_price', 0))
                open_pnl = float(deal.get('actual_usd_profit', deal.get('usd_final_profit', 0)))
                
                # Calculate percentage
                pnl_pct = 0
                if entry_price > 0:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                return {
                    "deal_id": deal_id,
                    "current_price": current_price,
                    "open_pnl": open_pnl,
                    "pnl_pct": round(pnl_pct, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True
                }
        
        # Deal not found
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
        
    except Exception as e:
        logger.error(f"Failed to refresh price for deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh price: {e}")

@router.post("/panic-sell")
def panic_sell_trade(request: dict):
    """
    Emergency sell functionality
    Market7 compatible endpoint for force-closing trades
    """
    try:
        deal_id = request.get('deal_id')
        if not deal_id:
            raise HTTPException(status_code=400, detail="deal_id is required")
        
        # For demo/paper trading, we'll simulate the panic sell
        # In production, this would call 3Commas panic sell API
        
        logger.warning(f"PANIC SELL requested for deal {deal_id}")
        
        # Get current deal info for response
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        active_deals = get_active_deals(bot_id)
        
        for deal in active_deals:
            if str(deal.get('id')) == str(deal_id):
                current_pnl = float(deal.get('actual_usd_profit', deal.get('usd_final_profit', 0)))
                
                # Note: In production, you would call:
                # response = make_3commas_request(f"/public/api/ver1/deals/{deal_id}/panic_sell", method="POST")
                
                return {
                    "success": True,
                    "deal_id": deal_id,
                    "pair": deal.get('pair'),
                    "pnl_usdt": current_pnl,
                    "message": f"DEMO: Panic sell would close deal {deal_id}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
        
    except Exception as e:
        logger.error(f"Failed to panic sell deal: {e}")
        raise HTTPException(status_code=500, detail=f"Panic sell failed: {e}")

@router.get("/ml/confidence")
def get_ml_confidence():
    """
    ML confidence data
    Market7 compatible endpoint
    """
    try:
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Get active deals for overall confidence calculation
        active_deals = get_active_deals(bot_id)
        
        if active_deals:
            # Calculate average confidence based on current trades
            total_confidence = 0
            for deal in active_deals:
                pnl_pct = float(deal.get('final_profit_percentage', 0))
                # Simple confidence: positive PnL = higher confidence
                confidence = max(0.4, min(0.9, 0.7 + (pnl_pct / 100)))
                total_confidence += confidence
            
            avg_confidence = total_confidence / len(active_deals)
        else:
            avg_confidence = 0.75  # Default confidence when no trades
        
        return {
            "confidence": round(avg_confidence, 3),
            "confidence_percentage": round(avg_confidence * 100, 1),
            "model_version": "marketpilot_v2.1",
            "active_trades": len(active_deals),
            "last_updated": datetime.utcnow().isoformat(),
            "status": "healthy" if avg_confidence > 0.6 else "warning"
        }
        
    except Exception as e:
        logger.error(f"Failed to get ML confidence: {e}")
        return {
            "confidence": 0.5,
            "confidence_percentage": 50.0,
            "model_version": "marketpilot_v2.1",
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat(),
            "status": "error"
        }

