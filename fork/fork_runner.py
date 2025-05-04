#!/usr/bin/env python3
import os, sys, json, time, redis, logging, requests, hmac, hashlib, argparse
from pathlib import Path
from datetime import datetime
import yaml

# === Project path patch ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.config_loader import PATHS
from fork.utils.fork_entry_logger import log_fork_entry
from fork.utils.entry_utils import get_entry_price, compute_score_hash

# === Paths from config ===
FORK_RRR_PATH = PATHS["final_fork_rrr_trades"]
FORK_TV_PATH = PATHS["fork_tv_adjusted"]
FORK_BACKTEST_PATH = PATHS["fork_backtest_candidates"]
TV_CONFIG_PATH = PATHS["tv_screener_config"]
CRED_PATH = PATHS["paper_cred"]

# === Redis / 3Commas ===
REDIS_HOST = "localhost"
REDIS_PORT = 6379
SENT_KEY = "FORK_SENT_TRADES"
THREECOMMAS_URL = "https://app.3commas.io/trade_signal/trading_view"
THREECOMMAS_BASE_URL = "https://api.3commas.io"

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# === Credentials ===
with open(CRED_PATH, "r") as f:
    creds = json.load(f)
BOT_ID = creds["3commas_bot_id"]
BOT_ID2 = creds.get("3commas_bot_id2")
EMAIL_TOKEN = creds["3commas_email_token"]
API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]

# === TV Screener status ===
def is_tv_enabled():
    try:
        config = yaml.safe_load(TV_CONFIG_PATH.read_text())
        tv_enabled = config.get("tv_screener", {}).get("enabled", False)
        return tv_enabled
    except Exception as e:
        logging.error(f"❌ Failed to read TV Screener config: {e}")
        return False

# === Load fork trades ===
def load_trades(tv_enabled: bool):
    path = FORK_TV_PATH if tv_enabled else FORK_RRR_PATH
    if not path.exists():
        logging.warning(f"⚠️ Trade path missing: {path}")
        return []
    if path.suffix == ".jsonl":
        return [json.loads(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    return list(json.load(path).keys())  # legacy RRR list

# === Clear stale files ===
def clear_if_disabled():
    logging.info("🚫 TV Screener disabled. Clearing adjusted/backtest outputs...")
    FORK_TV_PATH.write_text("")
    FORK_BACKTEST_PATH.write_text("")

# === 3Commas helpers ===
def format_pair(symbol): return f"USDT_{symbol.replace('USDT', '').replace('USDT_', '')}"

def sign_payload(payload, token):
    q = "&".join(f"{k}={v}" for k, v in sorted(payload.items()))
    payload["sign"] = hmac.new(token.encode(), q.encode(), hashlib.sha256).hexdigest()
    return payload

def send_to_3c(symbol, bot_id):
    payload = {
        "message_type": "bot",
        "bot_id": bot_id,
        "email_token": EMAIL_TOKEN,
        "delay_seconds": 0,
        "pair": format_pair(symbol)
    }
    try:
        res = requests.post(THREECOMMAS_URL, json=sign_payload(payload, EMAIL_TOKEN), timeout=10)
        res.raise_for_status()
        r.hset(SENT_KEY, f"{symbol}_{bot_id}", json.dumps({"sent": True, "timestamp": time.time()}))
        logging.info(f"✅ Sent {symbol} to 3Commas bot {bot_id}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send {symbol} to bot {bot_id}: {e}")
        return False

def get_active_trades():
    try:
        path = "/public/api/ver1/deals?scope=active"
        sig = hmac.new(API_SECRET.encode(), path.encode(), hashlib.sha256).hexdigest()
        headers = {"Apikey": API_KEY, "Signature": sig}
        res = requests.get(THREECOMMAS_BASE_URL + path, headers=headers)
        res.raise_for_status()
        return {deal["pair"].split("_")[1] + "USDT" for deal in res.json() if deal.get("status") == "bought"}
    except Exception as e:
        logging.error(f"❌ Could not fetch active trades: {e}")
        return set()

# === Main runner ===
def main():
    logging.info("🚀 Fork Trade Runner starting...")
    tv_mode = is_tv_enabled()

    if not tv_mode:
        clear_if_disabled()

    trades = load_trades(tv_mode)
    if not trades:
        logging.info("⚠️ No trades to process.")
        return

    trade_buffer = []
    for t in trades:
        symbol = t["symbol"] if isinstance(t, dict) else t
        if not symbol:
            logging.warning(f"⚠️ Skipping malformed trade: {t}")
            continue

        success_main = send_to_3c(symbol, BOT_ID)
        success_alt = send_to_3c(symbol, BOT_ID2) if BOT_ID2 else False

        if success_main or success_alt:
            trade_buffer.append({
                "symbol": symbol,
                "entry_ts": int(time.time()),
                "indicators": t.get("indicators", {}),
                "score_hash": t.get("score_hash", compute_score_hash(t.get("indicators", {}))),
                "source": "tv_kicker" if tv_mode else "fork_runner"
            })

        time.sleep(1)

    logging.info("⏱️ Waiting 5 seconds for 3Commas...")
    time.sleep(5)

    active = get_active_trades()
    confirmed = 0
    for t in trade_buffer:
        if t["symbol"] in active:
            log_fork_entry({
                "symbol": t["symbol"],
                "entry_price": get_entry_price(t["symbol"], t["entry_ts"]),
                "entry_time": t["entry_ts"],
                "entry_ts_iso": datetime.utcfromtimestamp(t["entry_ts"]).isoformat(),
                "score_hash": t["score_hash"],
                "source": t["source"],
                "indicators": t["indicators"]
            })
            confirmed += 1
        else:
            logging.warning(f"⚠️ Not found in active deals: {t['symbol']}")

    logging.info(f"✅ Final logged entries: {confirmed} / {len(trade_buffer)}")

if __name__ == "__main__":
    main()
