#!/usr/bin/env python3
import os
import json
import time
import redis
import logging
import requests
import hashlib
import hmac
import argparse
from datetime import datetime

from config.config_loader import PATHS
from fork.utils.fork_entry_logger import log_fork_entry
from dca.utils.entry_utils import get_entry_price, compute_score_hash

# === CONFIG ===
FORK_TRADES_PATH = PATHS["final_fork_rrr_trades"]
FORK_TV_TRADES_PATH = PATHS["fork_tv_adjusted"]
CRED_PATH = PATHS["paper_cred"]
REDIS_HOST = "localhost"
REDIS_PORT = 6379
SENT_KEY = "FORK_SENT_TRADES"
THREECOMMAS_URL = "https://app.3commas.io/trade_signal/trading_view"
THREECOMMAS_BASE_URL = "https://api.3commas.io"

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Load Credentials ===
try:
    with open(CRED_PATH, "r") as f:
        creds = json.load(f)
    BOT_ID = creds["3commas_bot_id"]
    BOT_ID2 = creds.get("3commas_bot_id2")
    EMAIL_TOKEN = creds["3commas_email_token"]
    API_KEY = creds["3commas_api_key"]
    API_SECRET = creds["3commas_api_secret"]
except Exception as e:
    logging.error(f"❌ Failed to load paper_cred.json: {e}")
    exit(1)

# Initialize Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# === Helpers ===

def format_3c_pair(symbol):
    return f"USDT_{symbol.replace('USDT', '').replace('USDT_', '')}"

def sign_payload(payload: dict, token: str) -> dict:
    query = "&".join(f"{k}={v}" for k, v in sorted(payload.items()))
    signature = hmac.new(token.encode(), query.encode(), hashlib.sha256).hexdigest()
    payload["sign"] = signature
    return payload

def send_to_3c(symbol, bot_id):
    payload = {
        "message_type": "bot",
        "bot_id": bot_id,
        "email_token": EMAIL_TOKEN,
        "delay_seconds": 0,
        "pair": format_3c_pair(symbol)
    }
    signed_payload = sign_payload(payload.copy(), EMAIL_TOKEN)

    try:
        res = requests.post(THREECOMMAS_URL, json=signed_payload, timeout=10)
        res.raise_for_status()
        r.hset(SENT_KEY, f"{symbol}_{bot_id}", json.dumps({"sent": True, "timestamp": time.time()}))
        logging.info(f"✅ Sent {symbol} to 3Commas bot {bot_id}.")
        return True
    except Exception as e:
        logging.error(f"❌ Error sending {symbol} to bot {bot_id}: {e}")
        return False

def get_active_3c_trades():
    try:
        full_path = "/public/api/ver1/deals?scope=active"
        full_url = THREECOMMAS_BASE_URL + full_path
        signature = hmac.new(API_SECRET.encode("utf-8"), full_path.encode("utf-8"), hashlib.sha256).hexdigest()
        headers = {
            "Apikey": API_KEY,
            "Signature": signature
        }
        res = requests.get(full_url, headers=headers, timeout=10)
        res.raise_for_status()
        deals = res.json()
        active = set()
        for deal in deals:
            if deal.get("status") != "bought":
                continue
            pair = deal.get("pair", "")
            if pair.startswith("USDT_"):
                active.add(pair.split("_")[1] + "USDT")
        return active
    except Exception as e:
        logging.error(f"❌ Failed to fetch active trades: {e}")
        return set()

def load_fork_trades(tv_mode: bool):
    path = FORK_TV_TRADES_PATH if tv_mode else FORK_TRADES_PATH
    if not os.path.exists(path):
        logging.error(f"❌ Missing: {path}")
        return []

    with open(path, "r") as f:
        if path.suffix == ".jsonl":
            return [json.loads(line.strip()) for line in f if line.strip()]
        else:
            return json.load(f)

# === Main Runner ===

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tv-mode", action="store_true", help="Use TV-kicker trades")
    args = parser.parse_args()

    logging.info("🚀 Fork Trade Runner starting...")

    fork_trades = load_fork_trades(args.tv_mode)
    if not fork_trades:
        logging.info("⚠️ No fork trades found.")
        return

    trade_buffer = []
    for trade in fork_trades:
        symbol = trade.get("symbol")
        if not symbol:
            logging.warning(f"⚠️ Missing symbol in trade: {trade}")
            continue

        indicator_data = trade.get("indicators", trade.get("meta", {})) or {}
        if not trade.get("score_hash"):
            trade["score_hash"] = compute_score_hash(indicator_data)

        success_main = send_to_3c(symbol, BOT_ID)
        success_alt = send_to_3c(symbol, BOT_ID2) if BOT_ID2 else False

        if success_main or success_alt:
            trade_buffer.append({
                "symbol": symbol,
                "entry_ts": int(time.time()),
                "indicators": indicator_data,
                "score_hash": trade["score_hash"],
                "source": "tv_kicker" if args.tv_mode else "fork_runner"
            })

        time.sleep(1)

    logging.info("⏱️ Waiting 5 seconds for 3Commas to create trades...")
    time.sleep(5)

    active_symbols = get_active_3c_trades()
    logging.info(f"📦 Active trades pulled from 3Commas: {len(active_symbols)}")

    confirmed = 0
    for t in trade_buffer:
        base_symbol = t["symbol"].replace("USDT", "")
        if base_symbol + "USDT" in active_symbols:
            entry_price = get_entry_price(t["symbol"], t["entry_ts"])
            entry_ts_iso = datetime.utcfromtimestamp(t["entry_ts"]).isoformat()
            log_fork_entry({
                "symbol": t["symbol"],
                "entry_price": entry_price,
                "entry_time": t["entry_ts"],
                "entry_ts_iso": entry_ts_iso,
                "score_hash": t["score_hash"],
                "source": t.get("source", "fork_runner"),
                "indicators": t.get("indicators", {})
            })
            confirmed += 1
        else:
            logging.warning(f"⚠️ Not found in active deals: {t['symbol']}")

    logging.info(f"✅ Final logged entries: {confirmed} / {len(trade_buffer)}")

if __name__ == "__main__":
    main()
