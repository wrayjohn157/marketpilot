from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
import os
import sys

import requests

import hashlib
import hmac
import time
from utils.credential_manager import get_3commas_credentials
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs



#!/usr/bin/env python3
from
 pathlib import Path

# === Logging setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Load credentials manually ===
BASE_DIR = get_path("base")
CRED_PATH = BASE_DIR / "config" / "paper_cred.json"

with open(CRED_PATH) as f:
    creds = json.load(f)

BOT_ID = creds["3commas_bot_id"]
EMAIL_TOKEN = creds["3commas_email_token"]

# === Redis setup ===
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
FINAL_TRADES_KEY = "queues:final_trades"
FINAL_FILTER_KEY = "FINAL_RRR_FILTERED_TRADES"
SENT_TRADES_KEY = "sessions:sent_trades"
from utils.redis_manager import get_redis_manager
r = get_redis_manager()

# === Constants ===
DELAY_SECONDS = 0
PRICE_MOVEMENT_THRESHOLD = 0.02  # 2%

THREECOMMAS_URL = "https://app.3commas.io/trade_signal/trading_view"

# === Functions ===
def should_send_trade(symbol: Any, current_price: Any) -> Any:
    last_data = r.get_trade_data()
    if last_data is None:
        return True
    try:
        last_price = json.loads(last_data)["entry_price"]
        return abs(current_price - last_price) / last_price >= PRICE_MOVEMENT_THRESHOLD
    except Exception:
        return True

def format_3commas_pair(symbol: str) -> str:
    if symbol.endswith("USDT"):
        base = symbol.replace("USDT", "")
        return f"USDT_{base}"
    return f"USDT_{symbol}"

def send_trade_to_3commas(symbol: Any, current_price: Any) -> Any:
    pair = format_3commas_pair(symbol)
    payload = {
        "message_type": "bot",
        "bot_id": BOT_ID,
        "email_token": EMAIL_TOKEN,
        "delay_seconds": DELAY_SECONDS,
        "pair": pair
    }
    try:
        response = requests.post(THREECOMMAS_URL, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"✅ Sent {pair} to 3Commas.")
        r.store_trade_data({\"symbol\": symbol, \"data\": {"entry_price": current_price}})
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send {pair} to 3Commas: {e}")
        return False

def main() -> Any:
    logging.info("🚀 Sending final trades to 3Commas bot...")

    try:
        data = r.get_cache(FINAL_TRADES_KEY)
        if not data:
            logging.info("No final trades in Redis.")
            return
        final_trades = json.loads(data)
    except Exception as e:
        logging.error(f"Error loading final trades: {e}")
        return

    # If final_trades is a list, try to load detailed trade info
    if isinstance(final_trades, list):
        logging.info("Final trades is a list; loading detailed data from FINAL_RRR_FILTERED_TRADES.")
        detailed_data = r.get_cache(FINAL_FILTER_KEY)
        if not detailed_data:
            logging.info("No detailed trades found.")
            return
        final_trades = json.loads(detailed_data)
        if not isinstance(final_trades, dict):
            logging.info("Detailed data is not a dict. Skipping dispatch.")
            return

    for symbol, trade_data in final_trades.items():
        price = trade_data.get("market_price")
        if not price:
            continue
        if should_send_trade(symbol, price):
            send_trade_to_3commas(symbol, price)
            time.sleep(1)
        else:
            logging.info(f"Skipping {symbol}: price change < {PRICE_MOVEMENT_THRESHOLD*100:.1f}%")

    logging.info("✅ Trade sending process complete.")

if __name__ == "__main__":
    main()
