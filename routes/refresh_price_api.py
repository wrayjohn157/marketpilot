"""
Refresh Price API - Market7 Style
Implements the exact refresh price endpoint that Market7 frontend expects
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import json
import logging
import hmac
import hashlib
import requests

logger = logging.getLogger(__name__)

router = APIRouter()

# Import our enhanced functions
from enhanced_dashboard_api import get_3commas_credentials, get_redis_client

def sign_request(path: str, query: str = ""):
    """Sign 3Commas API request using HMAC-SHA256"""
    try:
        creds = get_3commas_credentials()
        api_key = creds["3commas_api_key"]
        api_secret = creds["3commas_api_secret"]
        
        message = f"{path}?{query}" if query else path
        url = f"https://api.3commas.io{path}" + (f"?{query}" if query else "")
        signature = hmac.new(
            api_secret.encode("utf-8"), 
            msg=message.encode("utf-8"), 
            digestmod=hashlib.sha256
        ).hexdigest()
        
        headers = {"APIKEY": api_key, "Signature": signature}
        return url, headers
    except Exception as e:
        logger.error(f"Failed to sign request: {e}")
        raise HTTPException(status_code=500, detail="Failed to sign API request")

@router.get("/refresh-price/{deal_id}")
def refresh_price(deal_id: int):
    """
    Market7 compatible refresh price endpoint
    Calls 3Commas API to get latest deal data and returns current price info
    """
    try:
        path = f"/public/api/ver1/deals/{deal_id}/show"
        url, headers = sign_request(path)
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        deal_data = response.json()
        
        # Extract the data we need
        current_price = float(deal_data.get("current_price", 0))
        avg_entry_price = float(deal_data.get("avg_entry_price", 0))
        actual_profit = float(deal_data.get("actual_profit", 0))
        actual_profit_percentage = float(deal_data.get("actual_profit_percentage", 0))
        
        # Update Redis cache
        redis_client = get_redis_client()
        if redis_client:
            cache_key = f"deal:{deal_id}:refresh"
            cache_data = {
                "deal_id": deal_id,
                "current_price": current_price,
                "avg_entry_price": avg_entry_price,
                "actual_profit": actual_profit,
                "actual_profit_percentage": actual_profit_percentage,
                "timestamp": datetime.utcnow().isoformat()
            }
            redis_client.set_cache(cache_key, json.dumps(cache_data), ttl=300)  # 5 minutes
        
        return {
            "deal_id": deal_id,
            "current_price": current_price,
            "avg_entry_price": avg_entry_price,
            "open_pnl": actual_profit,
            "pnl_pct": actual_profit_percentage,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"3Commas API request failed for deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch deal data: {e}")
    except Exception as e:
        logger.error(f"Failed to refresh price for deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh price: {e}")

@router.get("/refresh-price/{deal_id}/cached")
def refresh_price_cached(deal_id: int):
    """
    Get cached refresh data for a deal
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis not available")
        
        cache_key = f"deal:{deal_id}:refresh"
        cached_data = redis_client.get(cache_key)
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="No cached data found")
        
        return json.loads(cached_data)
        
    except Exception as e:
        logger.error(f"Failed to get cached data for deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cached data: {e}")

