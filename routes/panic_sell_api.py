"""
Panic Sell API - Market7 Style
Implements the exact panic sell endpoint that Market7 frontend expects
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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

class PanicSellRequest(BaseModel):
    deal_id: int

def generate_signature(path: str) -> str:
    """Generate HMAC signature for 3Commas API"""
    try:
        creds = get_3commas_credentials()
        api_secret = creds["3commas_api_secret"]
        return hmac.new(api_secret.encode(), path.encode(), hashlib.sha256).hexdigest()
    except Exception as e:
        logger.error(f"Failed to generate signature: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API signature")

def is_deal_active(deal_id: int) -> bool:
    """Check if a deal is still active"""
    try:
        creds = get_3commas_credentials()
        api_key = creds["3commas_api_key"]
        bot_id = creds["3commas_bot_id"]
        
        # Get active deals for the bot
        path = f"/public/api/ver1/deals?account_id={creds['3commas_account_id']}&bot_id={bot_id}&scope=active"
        signature = generate_signature(path)
        headers = {"ApiKey": api_key, "Signature": signature, "Accept": "application/json"}
        
        response = requests.get(f"https://api.3commas.io{path}", headers=headers, timeout=10)
        response.raise_for_status()
        
        deals = response.json()
        active_deal_ids = [deal["id"] for deal in deals]
        return deal_id in active_deal_ids
        
    except Exception as e:
        logger.error(f"Failed to check if deal {deal_id} is active: {e}")
        return False

def panic_sell(deal_id: int):
    """Execute panic sell on 3Commas"""
    try:
        creds = get_3commas_credentials()
        api_key = creds["3commas_api_key"]
        
        path = f"/public/api/ver1/deals/{deal_id}/panic_sell"
        signature = generate_signature(path)
        headers = {
            "ApiKey": api_key, 
            "Signature": signature, 
            "Accept": "application/json"
        }
        
        response = requests.post(f"https://api.3commas.io{path}", headers=headers, timeout=10)
        return response
        
    except Exception as e:
        logger.error(f"Failed to execute panic sell for deal {deal_id}: {e}")
        return None

def fetch_final_trade_info(deal_id: int):
    """Fetch final trade info after panic sell"""
    try:
        creds = get_3commas_credentials()
        api_key = creds["3commas_api_key"]
        
        path = f"/public/api/ver1/deals/{deal_id}/show"
        signature = generate_signature(path)
        headers = {"ApiKey": api_key, "Signature": signature, "Accept": "application/json"}
        
        response = requests.get(f"https://api.3commas.io{path}", headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to fetch final trade info for deal {deal_id}: {e}")
        return None

@router.post("/panic-sell")
def trigger_panic_sell(payload: PanicSellRequest):
    """
    Market7 compatible panic sell endpoint
    Executes panic sell on 3Commas and returns final trade info
    """
    try:
        deal_id = payload.deal_id
        
        # Check if deal is still active
        if not is_deal_active(deal_id):
            raise HTTPException(status_code=400, detail="Deal is already closed or inactive")
        
        # Execute panic sell
        res = panic_sell(deal_id)
        if not res or res.status_code not in [200, 201]:
            error_msg = res.text if res else "no response"
            raise HTTPException(status_code=500, detail=f"Panic sell failed: {error_msg}")
        
        # Fetch final trade info
        final_info = fetch_final_trade_info(deal_id)
        
        # Update Redis cache
        redis_client = get_redis_client()
        if redis_client:
            cache_key = f"deal:{deal_id}:panic_sell"
            cache_data = {
                "deal_id": deal_id,
                "status": "panic_sold",
                "final_info": final_info,
                "timestamp": datetime.utcnow().isoformat()
            }
            redis_client.set_cache(cache_key, json.dumps(cache_data), ttl=3600)  # 1 hour
        
        return {
            "status": "success", 
            "deal_id": deal_id, 
            "final": final_info,
            "message": "Panic sell executed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute panic sell for deal {payload.deal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Panic sell failed: {e}")

@router.get("/panic-sell/{deal_id}/status")
def get_panic_sell_status(deal_id: int):
    """
    Get the status of a panic sell operation
    """
    try:
        redis_client = get_redis_client()
        if not redis_client:
            raise HTTPException(status_code=500, detail="Redis not available")
        
        cache_key = f"deal:{deal_id}:panic_sell"
        cached_data = redis_client.get(cache_key)
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="No panic sell data found")
        
        return json.loads(cached_data)
        
    except Exception as e:
        logger.error(f"Failed to get panic sell status for deal {deal_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get panic sell status: {e}")

