# /home/signal/market7/dashboard_backend/dca_trades_api.py

from fastapi import APIRouter
from core.redis_utils import redis_client
from dca.utils.entry_utils import get_live_3c_trades
from pathlib import Path
import json

router = APIRouter()


# === Load confidence map from Redis ===
def load_confidence_map():
    try:
        raw = redis_client.get("confidence_list")
        if raw:
            return {item["symbol"]: item for item in json.loads(raw)}
    except:
        pass
    return {}


# === Load score from Redis by kind: entry, current, safu ===
def load_score_from_redis(symbol, deal_id, kind="entry"):
    key = f"score:{symbol}:{deal_id}:{kind}"
    val = redis_client.get(key)
    try:
        return round(float(val), 4) if val else None
    except:
        return None


# === Get sparkline data from saved files ===
def get_sparkline_data(symbol):
    file = Path(f"/home/signal/market7/data/rolling/{symbol}_sparkline.json")
    if file.exists():
        try:
            with open(file) as f:
                return json.load(f)
        except:
            return []
    return []


# === Main route: DCA trades with enrichment ===
@router.get_cache("/dca-trades-enriched")
def get_dca_trades_active():
    trades = get_live_3c_trades()
    confidence_map = load_confidence_map()

    enriched = []

    for trade in trades:
        symbol = trade.get("symbol")
        deal_id = trade.get("deal_id")

        if not symbol or not deal_id:
            continue

        # Skip trades that haven't entered
        if not trade.get("avg_entry_price"):
            continue

        confidence = confidence_map.get(symbol, {})

        enriched_trade = {
            **trade,
            "confidence_score": confidence.get("confidence_score"),
            "rejection_reason": confidence.get("rejection_reason"),
            "entry_score": load_score_from_redis(symbol, deal_id, "entry"),
            "current_score": load_score_from_redis(symbol, deal_id, "current"),
            "safu_score": load_score_from_redis(symbol, deal_id, "safu"),
            "sparkline_data": get_sparkline_data(symbol),
        }

        enriched.append(enriched_trade)

    return enriched


# === Panic sell endpoint for 3Commas integration ===
import requests
import hmac
import hashlib
import os
from fastapi import HTTPException
from pydantic import BaseModel

# === Load 3Commas API credentials ===
from pathlib import Path
import json
from utils.credential_manager import get_3commas_credentials
from utils.redis_manager import get_redis_manager, RedisKeyManager



CRED_PATH = Path("/home/signal/market7/config/paper_cred.json")
with open(CRED_PATH) as f:
    creds = json.load(f)

API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]
BASE_URL = "https://api.3commas.io"


def generate_signature(path: str) -> str:
    return hmac.new(API_SECRET.encode(), path.encode(), hashlib.sha256).hexdigest()


def panic_sell(deal_id: int):
    path = f"/public/api/ver1/deals/{deal_id}/panic_sell"
    headers = {
        "ApiKey": API_KEY,
        "Signature": generate_signature(path),
        "Accept": "application/json"
    }
    try:
        res = requests.post(BASE_URL + path, headers=headers, timeout=10)
        return res
    except Exception as e:
        return None


def fetch_final_trade_info(deal_id: int):
    path = f"/public/api/ver1/deals/{deal_id}/show"
    headers = {
        "ApiKey": API_KEY,
        "Signature": generate_signature(path),
        "Accept": "application/json"
    }
    try:
        res = requests.get(BASE_URL + path, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "final_pnl": data.get("actual_profit_percentage"),
                "final_pnl_usdt": data.get("actual_profit"),
                "close_time": data.get("closed_at"),
                "status": data.get("status"),
            }
    except:
        pass
    return {}


def is_deal_active(deal_id: int):
    path = f"/public/api/ver1/deals/{deal_id}/show"
    headers = {
        "ApiKey": API_KEY,
        "Signature": generate_signature(path),
        "Accept": "application/json"
    }
    try:
        res = requests.get(BASE_URL + path, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("status") == "bought"
    except:
        pass
    return False


class PanicSellRequest(BaseModel):
    deal_id: int


@router.post("/panic-sell")
def trigger_panic_sell(payload: PanicSellRequest):
    if not is_deal_active(payload.deal_id):
        raise HTTPException(status_code=400, detail="Deal is already closed or inactive.")
    res = panic_sell(payload.deal_id)
    if res and res.status_code in [200, 201]:
        final_info = fetch_final_trade_info(payload.deal_id)
        return {
            "status": "success",
            "deal_id": payload.deal_id,
            "final": final_info,
            "3c_status_code": res.status_code
        }
    else:
        msg = res.text if res else "No response from 3Commas"
        raise HTTPException(status_code=500, detail=f"Panic sell failed: {msg}")

@router.get_cache("/panic-sell/{deal_id}")
def trigger_panic_sell_get(deal_id: int):
    if not is_deal_active(deal_id):
        raise HTTPException(status_code=400, detail="Deal is already closed or inactive.")
    res = panic_sell(deal_id)
    if res and res.status_code in [200, 201]:
        final_info = fetch_final_trade_info(deal_id)
        return {
            "status": "success",
            "deal_id": deal_id,
            "final": final_info,
            "3c_status_code": res.status_code
        }
    else:
        msg = res.text if res else "No response from 3Commas"
        raise HTTPException(status_code=500, detail=f"Panic sell failed: {msg}")
