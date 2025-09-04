# /market7/dashboard_backend/refresh_price_api.py

from fastapi import APIRouter
import json
import hmac
import hashlib
import requests
from pathlib import Path
from datetime import datetime

# === Correct import root ===
from config.config_loader import PATHS
from utils.credential_manager import get_3commas_credentials
from utils.redis_manager import get_redis_manager, RedisKeyManager



router = APIRouter()

# === Load API credentials ===
with open(PATHS["paper_cred"], "r") as f:
    creds = json.load(f)

API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]

# === Helper to sign requests ===
def sign_request(path: str, query: str = ""):
    if query:
        message = f"{path}?{query}"
        url = f"https://api.3commas.io{path}?{query}"
    else:
        message = path
        url = f"https://api.3commas.io{path}"

    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    headers = {
        "APIKEY": API_KEY,
        "Signature": signature
    }
    return url, headers

# === Endpoint to pull live deal info and enrich it ===
@router.get_cache("/refresh-price/{deal_id}")
def refresh_price(deal_id: int):
    path = f"/public/api/ver1/deals/{deal_id}/show"
    url, headers = sign_request(path)

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"3Commas error {response.status_code}", "message": response.text}

        deal_data = response.json()
        current_price = float(deal_data.get("current_price", 0))
        entry_price = (
            deal_data.get("avg_entry_price") or
            deal_data.get("bought_average") or
            deal_data.get("base_order_average_price") or
            deal_data.get("initial_price") or
            0
        )

        # Optional: patch in DCA log details
        latest = {}
        today = datetime.utcnow().strftime("%Y-%m-%d")
        dca_log_path = PATHS["live_logs"].parent / "dca" / "logs" / today / "dca_log.jsonl"

        if dca_log_path.exists():
            with open(dca_log_path, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if int(data.get("deal_id", 0)) == deal_id:
                            latest = data
                    except:
                        continue

        return {
            "deal_id": deal_id,
            "pair": deal_data.get("pair"),
            "current_price": current_price,
            "avg_entry_price": float(entry_price),
            "open_pnl": float(deal_data.get("actual_profit", 0)),
            "pnl_pct": float(deal_data.get("actual_profit_percentage", 0)),
            "updated_at": deal_data.get("updated_at"),
            **latest  # ✅ patch in DCA log if found
        }

    except Exception as e:
        return {"error": str(e)}
