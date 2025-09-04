from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import os, sys, json, time, redis, logging, requests, hmac, hashlib

import yaml

from fork.utils.entry_utils import get_entry_price, compute_score_hash
from fork.utils.fork_entry_logger import log_fork_entry
import subprocess
from utils.credential_manager import get_3commas_credentials


#!/usr/bin/env python3
from pathlib import Path
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs
from utils.redis_manager import get_redis_manager
from config.unified_config_manager import get_config


# === Setup ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# === Config Paths ===
FORK_SCORE_SCRIPT = PROJECT_ROOT / "indicators" / "fork_score_filter.py"
TV_KICKER_SCRIPT = PROJECT_ROOT / "indicators" / "tv_kicker.py"

FORK_RRR_PATH = get_path("final_fork_rrr_trades")
FORK_TV_PATH = get_path("fork_tv_adjusted")
FORK_BACKTEST_PATH = get_path("fork_backtest_candidates")
TV_CONFIG_PATH = get_path("tv_screener_config")
CRED_PATH = get_path("paper_cred")
BTC_LOGS_DIR = get_path("btc_logs")

# === Redis / 3Commas ===
REDIS_HOST = "localhost"
REDIS_PORT = 6379
SENT_KEY = "FORK_SENT_TRADES"
THREECOMMAS_URL = "https://app.3commas.io/trade_signal/trading_view"
THREECOMMAS_BASE_URL = "https://api.3commas.io"

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
r = get_redis_manager()

# === Load Credentials ===
with open(CRED_PATH, "r") as f:
    creds = json.load(f)
BOT_ID = creds["3commas_bot_id"]
BOT_ID2 = creds.get("3commas_bot_id2")
EMAIL_TOKEN = creds["3commas_email_token"]
API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]

# === Helpers ===
def format_pair(symbol: Any) -> Any:
    return f"USDT_{symbol.replace('USDT', '').replace('USDT_', '')}"

def sign_payload(payload: Any, token: Any) -> Any:
    q = "&".join(f"{k}={v}" for k, v in sorted(payload.items()))
    payload["sign"] = hmac.new(token.encode(), q.encode(), hashlib.sha256).hexdigest()
    return payload

def send_to_3c(symbol: Any, bot_id: Any) -> Any:
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

def get_active_trades() -> Any:
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

# === BTC Status from file ===
def get_latest_btc_status() -> Any:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    btc_log_path = BTC_LOGS_DIR / today / "btc_snapshots.jsonl"
    if not btc_log_path.exists():
        return "neutral"
    try:
        lines = btc_log_path.read_text().strip().splitlines()
        if not lines:
            return "neutral"
        last = json.loads(lines[-1])
        return last.get("market_condition", "neutral").lower()
    except Exception as e:
        logging.warning(f"⚠️ Failed to read BTC status from log: {e}")
        return "neutral"

# === TV Status ===
def check_tv_status() -> Any:
    try:
        cfg = yaml.safe_load(TV_CONFIG_PATH.read_text()).get("tv_screener", {})
        enabled = cfg.get("enabled", False)
        guard = cfg.get("disable_if_btc_unhealthy", False)
        btc_status = get_latest_btc_status()
        healthy = (btc_status == "bullish")
        return enabled, guard, btc_status, (not guard or healthy)
    except Exception as e:
        logging.error(f"❌ Failed to parse TV Screener config: {e}")
        return False, False, "unknown", False

# === Main ===
def main() -> Any:
    logging.info("🚀 Fork Trade Runner starting...")

    # Step 1: Run fork_score_filter.py
    subprocess.run(["python3", str(FORK_SCORE_SCRIPT)], check=True)

    # Step 2: Send regular forks
    if FORK_RRR_PATH.exists():
        trades = json.load(FORK_RRR_PATH.open())
        if isinstance(trades, dict):
            trade_list = [{"symbol": s} for s in trades.keys()]
        elif isinstance(trades, list):
            trade_list = trades
        else:
            logging.error("❌ Unknown format in final_fork_rrr_trades.json")
            trade_list = []

        for trade in trade_list:
            symbol = trade["symbol"]
            send_to_3c(symbol, BOT_ID)
            if BOT_ID2:
                send_to_3c(symbol, BOT_ID2)
            time.sleep(1)

    # Step 3: TV kicker logic
    tv_enabled, btc_guard, btc_status, allow_tv = check_tv_status()
    logging.info(f"📊 TV Enabled: {'✅' if tv_enabled else '❌'} | BTC Guard: {'✅' if btc_guard else '❌'} | BTC Status: {btc_status.upper()}")
    logging.info(f"📈 TV kicker allowed: {'✅' if allow_tv else '❌'}")

    if tv_enabled and allow_tv:
        subprocess.run(["python3", str(TV_KICKER_SCRIPT)], check=True)
        if FORK_TV_PATH.exists():
            lines = FORK_TV_PATH.read_text().strip().splitlines()
            for line in lines:
                trade = json.loads(line)
                symbol = trade["symbol"]
                send_to_3c(symbol, BOT_ID)
                if BOT_ID2:
                    send_to_3c(symbol, BOT_ID2)
                time.sleep(1)
    else:
        logging.info("📉 BTC is unhealthy or TV disabled. Skipping TV kicker.")
        logging.info("🧹 Clearing stale TV outputs...")
        FORK_TV_PATH.write_text("")
        FORK_BACKTEST_PATH.write_text("")

if __name__ == "__main__":
    main()
