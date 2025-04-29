# /market7/dashboard_backend/unified_fork_metrics.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from config.config_loader import PATHS

# === Load credentials properly ===
with open(PATHS["paper_cred"], "r") as f:
    creds = json.load(f)

API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]
BOT_ID = creds.get("3commas_bot_id", 16017224)
ACCOUNT_ID = creds.get("3commas_account_id", 32994602)  # fallback

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
        digestmod=hashlib.sha256
    ).hexdigest()
    headers = {
        "APIKEY": API_KEY,
        "Signature": signature
    }
    return url, headers

# === Get Active Deals ===
def get_active_deals(bot_id: int):
    path = "/public/api/ver1/deals"
    query = f"limit=1000&scope=active&bot_id={bot_id}"
    url, headers = sign_request(path, query)
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print("[ERROR] Fetching active deals:", resp.text)
        return []

# === Get Finished Deals ===
def get_finished_deals(bot_id: int):
    path = "/public/api/ver1/deals"
    query = f"limit=1000&scope=finished&bot_id={bot_id}"
    url, headers = sign_request(path, query)
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print("[ERROR] Fetching finished deals:", resp.text)
        return []

# === Calculate Open PnL & Drawdown ===
def calculate_open_pnl(active_deals):
    total_open_pnl = 0.0
    deals_info = []
    for deal in active_deals:
        try:
            spent = float(deal.get("bought_volume", 0))
            coins = float(deal.get("bought_amount", 0))
            current_price = float(deal.get("current_price", 0))
            pair = deal.get("pair", "")

            if spent == 0 or coins == 0 or current_price == 0:
                continue

            current_value = coins * current_price
            open_pnl = current_value - spent
            pnl_pct = (open_pnl / spent) * 100 if spent else 0

            entry_price = spent / coins if coins else 0
            drawdown_pct = max(0, ((entry_price - current_price) / entry_price) * 100) if entry_price else 0
            drawdown_usd = max(0, (entry_price - current_price) * coins)

            total_open_pnl += open_pnl
            deals_info.append({
                "pair": pair,
                "spent_amount": round(spent, 2),
                "current_price": round(current_price, 6),
                "entry_price": round(entry_price, 2),
                "open_pnl": round(open_pnl, 2),
                "open_pnl_pct": round(pnl_pct, 2),
                "drawdown_pct": round(drawdown_pct, 2),
                "drawdown_usd": round(drawdown_usd, 2)
            })
        except Exception:
            continue
    return total_open_pnl, deals_info

# === Calculate Closed Deals ===
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
            closed_at = datetime.fromisoformat(deal.get("closed_at", "").replace("Z", "+00:00"))
            total_realized_pnl += profit
            total_deals += 1
            if profit > 0:
                wins += 1
            if closed_at >= last_24h:
                daily_realized_pnl += profit
        except Exception:
            continue
    win_rate = round((wins / total_deals) * 100, 1) if total_deals > 0 else 0
    return total_realized_pnl, daily_realized_pnl, total_deals, win_rate

# === Get Multi-Pair Stats ===
def get_multi_pair_stats(bot_id: int, account_id: int):
    path = "/public/api/ver1/bots/stats"
    query = f"bot_id={bot_id}&account_id={account_id}"
    url, headers = sign_request(path, query)
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print("[ERROR] Fetching multi-pair stats:", resp.text)
        return {}

# === Get Fork Metrics ===
def get_fork_trade_metrics():
    active_deals = get_active_deals(BOT_ID)
    finished_deals = get_finished_deals(BOT_ID)

    total_open_pnl, open_deals_info = calculate_open_pnl(active_deals)
    realized_pnl_alltime, daily_realized_pnl, total_deals, win_rate = calculate_closed_deals_stats(finished_deals)
    multi_pair_stats = get_multi_pair_stats(BOT_ID, ACCOUNT_ID)

    total_allocated = sum(d.get("spent_amount", 0) for d in open_deals_info)
    upnl = round(total_open_pnl, 2)
    active_count = len(open_deals_info)
    total_pnl = multi_pair_stats.get("profits_in_usd", {}).get("overall_usd_profit", realized_pnl_alltime)
    today_pnl = multi_pair_stats.get("profits_in_usd", {}).get("today_usd_profit", daily_realized_pnl)
    balance = 25000 + float(total_pnl or 0)

    return {
        "bot_id": BOT_ID,
        "metrics": {
            "open_pnl": upnl,
            "daily_realized_pnl": round(daily_realized_pnl, 2),
            "realized_pnl_alltime": round(realized_pnl_alltime, 2),
            "total_deals": total_deals,
            "win_rate": win_rate,
            "active_deals": open_deals_info
        },
        "multi_pair_stats": multi_pair_stats,
        "summary": {
            "active_trades": active_count,
            "allocated": round(total_allocated, 2),
            "today_pnl": round(today_pnl, 2),
            "upnl": upnl,
            "total_pnl": round(total_pnl, 2),
            "balance": round(balance, 2)
        }
    }

if __name__ == "__main__":
    result = get_fork_trade_metrics()
    print(json.dumps(result, indent=2))
