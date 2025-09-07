import hashlib
import hmac
import json
from datetime import datetime, timedelta

import requests

from utils.credential_manager import get_3commas_credentials
from utils.redis_manager import get_redis_manager

# Load 3Commas API credentials from credentials.json
with open("credentials.json") as f:
    creds = json.load(f)

API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]

# Set the bot ID you want to pull stats for
BOT_ID = 16017224

# Connect to Redis (for open deal data)
r = get_redis_manager()


def get_open_deals(bot_id):
    keys = r.get_key_stats()
    open_deals = []
    for key in keys:
        data = r.hgetall(key)
        if not data:
            continue
        try:
            if int(data.get("bot_id", 0)) == bot_id:
                pnl = float(data.get("current_pnl", 0))
                pnl_pct = float(data.get("current_pnl_pct", 0))
                open_deals.append(
                    {"pair": data.get("pair", key), "pnl": pnl, "pnl_pct": pnl_pct}
                )
        except Exception:
            continue
    total_open_pnl = sum(deal["pnl"] for deal in open_deals)
    return total_open_pnl, open_deals


def get_closed_deals(bot_id):
    # Build the path and query string to sign
    path = "/public/api/ver1/deals"
    query = f"limit=1000&bot_id={bot_id}&scope=finished"
    message = f"{path}?{query}"
    # Compute the signature using HMAC SHA256
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    headers = {"APIKEY": API_KEY, "Signature": signature}
    url = f"https://api.3commas.io{path}?{query}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error fetching closed deals:", response.text)
        return []
    return response.json()


def get_closed_deals_stats(bot_id):
    closed_deals = get_closed_deals(bot_id)
    total_realized_pnl = 0.0
    wins = 0
    total_deals = 0
    for deal in closed_deals:
        try:
            profit = float(deal.get("final_profit", 0))
            total_realized_pnl += profit
            total_deals += 1
            if profit > 0:
                wins += 1
        except Exception:
            continue
    win_rate = round((wins / total_deals) * 100, 1) if total_deals > 0 else 0
    return total_realized_pnl, total_deals, win_rate


def main():
    total_open_pnl, current_deals = get_open_deals(BOT_ID)
    realized_pnl, total_deals, win_rate = get_closed_deals_stats(BOT_ID)

    result = {
        "bot_id": BOT_ID,
        "open_pnl": round(total_open_pnl, 2),
        "realized_pnl": round(realized_pnl, 2),
        "total_deals": total_deals,
        "win_rate": win_rate,
        "current_deals": current_deals,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
