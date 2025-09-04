# /market7/dashboard_backend/threecommas_metrics.py

import hashlib
import hmac
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

# === Config Loader ===
sys.path.append(str(Path(__file__).resolve().parent.parent))  # Up to /market7
from config.unified_config_manager import (
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
)
from utils.credential_manager import get_3commas_credentials

# === Load credentials ===
with open(get_path("paper_cred"), "r") as f:
    creds = json.load(f)

API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]
BOT_ID = creds.get("3commas_bot_id", 16017224)
ACCOUNT_ID = creds.get("3commas_account_id", 32994602)  # fallback paper trading ID


# === Helper: Sign a request ===
def sign_request(path: str, query: str = "") -> (str, dict):
    if query:
        message = f"{path}?{query}"
        url = f"https://api.3commas.io{path}?{query}"
    else:
        message = path
        url = f"https://api.3commas.io{path}"

    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    headers = {"APIKEY": API_KEY, "Signature": signature}
    return url, headers


# === Pull Active Deals ===
def get_active_deals(bot_id: int):
    path = "/public/api/ver1/deals"
    query = f"limit=1000&scope=active&bot_id={bot_id}"
    url, headers = sign_request(path, query)
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print("Error fetching active deals:", resp.text)
        return []


# === Pull Finished Deals ===
def get_finished_deals(bot_id: int):
    path = "/public/api/ver1/deals"
    query = f"limit=1000&scope=finished&bot_id={bot_id}"
    url, headers = sign_request(path, query)
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print("Error fetching finished deals:", resp.text)
        return []


# === Open PnL Calculator ===
def calculate_open_pnl(active_deals):
    total_open_pnl = 0.0
    deals_info = []
    for deal in active_deals:
        try:
            spent_amount = float(deal.get("bought_volume", 0))
            coins_bought = float(deal.get("bought_amount", 0))
            current_price = float(deal.get("current_price", 0))
            pair = deal.get("pair", "UNKNOWN")

            current_value = coins_bought * current_price
            open_pnl = current_value - spent_amount
            pnl_pct = (open_pnl / spent_amount) * 100 if spent_amount else 0

            entry_price = spent_amount / coins_bought if coins_bought else 0
            drawdown_pct = (
                ((entry_price - current_price) / entry_price) * 100
                if current_price < entry_price
                else 0.0
            )
            drawdown_usd = (
                (entry_price - current_price) * coins_bought
                if current_price < entry_price
                else 0.0
            )

            total_open_pnl += open_pnl
            deals_info.append(
                {
                    "pair": pair,
                    "spent_amount": round(spent_amount, 2),
                    "current_price": round(current_price, 6),
                    "entry_price": round(entry_price, 2),
                    "open_pnl": round(open_pnl, 2),
                    "open_pnl_pct": round(pnl_pct, 2),
                    "drawdown_pct": round(drawdown_pct, 2),
                    "drawdown_usd": round(drawdown_usd, 2),
                }
            )
        except Exception:
            continue
    return total_open_pnl, deals_info


# === Closed Deals Calculator ===
def calculate_closed_deals_stats(finished_deals):
    now = datetime.utcnow()
    last_24h = now - timedelta(days=1)
    total_realized_pnl = 0.0
    daily_realized_pnl = 0.0
    total_deals = 0
    wins = 0

    for deal in finished_deals:
        try:
            profit = float(deal.get("final_profit", 0))
            closed_at_str = deal.get("closed_at", "").replace("Z", "+00:00")
            closed_at = datetime.fromisoformat(closed_at_str)

            total_realized_pnl += profit
            total_deals += 1
            if profit > 0:
                wins += 1

            if closed_at >= last_24h:
                daily_realized_pnl += profit
        except Exception:
            continue

    win_rate = round((wins / total_deals) * 100, 1) if total_deals else 0
    return total_realized_pnl, daily_realized_pnl, total_deals, win_rate


# === Get Multi Pair Stats ===
def get_multi_pair_stats(bot_id: int, account_id: int):
    path = "/public/api/ver1/bots/stats"
    query = f"bot_id={bot_id}&account_id={account_id}"
    url, headers = sign_request(path, query)
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print("Error fetching multi-pair stats:", resp.text)
        return {}


# === Main Exported Function ===
def get_3commas_metrics():
    active_deals = get_active_deals(BOT_ID)
    finished_deals = get_finished_deals(BOT_ID)

    total_open_pnl, open_deals_info = calculate_open_pnl(active_deals)
    (
        realized_pnl_alltime,
        daily_realized_pnl,
        total_deals,
        win_rate,
    ) = calculate_closed_deals_stats(finished_deals)
    multi_pair_stats = get_multi_pair_stats(BOT_ID, ACCOUNT_ID)

    return {
        "bot_id": BOT_ID,
        "metrics": {
            "open_pnl": round(total_open_pnl, 2),
            "daily_realized_pnl": round(daily_realized_pnl, 2),
            "realized_pnl_alltime": round(realized_pnl_alltime, 2),
            "total_deals": total_deals,
            "win_rate": win_rate,
            "active_deals": open_deals_info,
        },
        "multi_pair_stats": multi_pair_stats,
    }


if __name__ == "__main__":
    print(json.dumps(get_3commas_metrics(), indent=2))
