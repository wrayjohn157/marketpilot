from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json

import requests

import argparse
import hashlib
import hmac

#!/usr/bin/env python3
from
 datetime import datetime, timedelta, timezone

# === Updated Dynamic Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/market7
CRED_PATH = PROJECT_ROOT / "config/paper_cred.json"
SAVE_BASE = PROJECT_ROOT / "ml/datasets/raw_paper"
BASE_URL = "https://api.3commas.io"
LIMIT = 1000

def load_credentials() -> Any:
    with open(CRED_PATH, "r") as f:
        creds = json.load(f)
    return creds["3commas_api_key"], creds["3commas_api_secret"], creds["3commas_bot_id"]

def generate_signature(path: Any, secret: Any) -> Any:
    return hmac.new(secret.encode("utf-8"), path.encode("utf-8"), hashlib.sha256).hexdigest()

def fetch_closed_trades(api_key: Any, api_secret: Any, bot_id: Any) -> Any:
    all_trades = []
    page = 1
    while True:
        url_path = f"/public/api/ver1/deals?bot_id={bot_id}&limit={LIMIT}&offset={(page-1)*LIMIT}"
        full_url = BASE_URL + url_path
        headers = {
            "Apikey": api_key,
            "Signature": generate_signature(url_path, api_secret)
        }

        try:
            response = requests.get(full_url, headers=headers, timeout=20)
            if response.status_code != 200:
                print(f"[ERROR] {response.status_code}: {response.text}")
                break
            page_trades = response.json()
            if not page_trades:
                break
            all_trades.extend(page_trades)
            if len(page_trades) < LIMIT:
                break
            page += 1
        except Exception as e:
            print(f"[ERROR] Failed to fetch page {page}: {e}")
            break

    return [t for t in all_trades if t.get("status") in {
        "completed", "stop_loss_finished", "panic_sold", "manual", "cancelled"
    }]

def filter_trades_by_date(trades: Any, target_date: Any) -> Any:
    results = []
    for t in trades:
        try:
            closed_dt = datetime.fromisoformat(t["closed_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
            if closed_dt.strftime("%Y-%m-%d") == target_date:
                results.append(t)
        except Exception as e:
            print(f"[WARN] Could not parse closed_at for trade {t.get('id')}: {e}")
    return results

def reduce_trade(t: Any) -> Any:
    return {
        "id": t.get("id"),
        "pair": t.get("pair"),
        "created_at": t.get("created_at"),
        "closed_at": t.get("closed_at"),
        "status": t.get("status"),
        "final_profit_percentage": t.get("final_profit_percentage"),
        "usd_final_profit": t.get("usd_final_profit"),
        "actual_profit": t.get("actual_profit"),
        "strategy": t.get("strategy"),
        "bot_name": t.get("bot_name"),
        "completed_safety_orders_count": t.get("completed_safety_orders_count"),
        "max_safety_orders": t.get("max_safety_orders"),
        "trailing_enabled": t.get("trailing_enabled"),
        "tsl_enabled": t.get("tsl_enabled"),
        "stop_loss_percentage": t.get("stop_loss_percentage"),
        "base_order_average_price": t.get("base_order_average_price"),
        "bought_average_price": t.get("bought_average_price"),
        "sold_average_price": t.get("sold_average_price"),
        "tsl_max_price": t.get("tsl_max_price")
    }

def save_trades(trades: Any, target_day: Any) -> Any:
    folder = SAVE_BASE / target_day
    folder.mkdir(parents=True, exist_ok=True)
    file_path = folder / "paper_trades.jsonl"
    with open(file_path, "w") as f:
        for trade in trades:
            f.write(json.dumps(reduce_trade(trade)) + "\n")
    print(f"✅ {len(trades)} trades saved to {file_path}")

def main() -> Any:
    parser = argparse.ArgumentParser(description="Pull and save closed 3Commas trades by day.")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD (defaults to yesterday UTC)")
    args = parser.parse_args()

    target_day = args.date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"[{datetime.utcnow()}] Pulling closed trades for target date: {target_day}...")

    api_key, api_secret, bot_id = load_credentials()
    trades = fetch_closed_trades(api_key, api_secret, bot_id)

    if not trades:
        print("[INFO] No trades fetched from 3Commas.")
        return

    filtered_trades = filter_trades_by_date(trades, target_day)
    if filtered_trades:
        save_trades(filtered_trades, target_day)
    else:
        print(f"[INFO] No trades matched the target date {target_day}.")

if __name__ == "__main__":
    main()
