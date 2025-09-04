import hashlib
import hmac
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from config.unified_config_manager import (  # utils.redis_manager,; from,; import,
    get_3commas_credentials,
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
    get_redis_manager,
    utils.credential_manager,
)

# /home/signal/market7/fork/utils/fork_entry_utils.py



# Paths
SNAPSHOT_BASE = get_path("snapshots")
FORK_HISTORY = get_path("fork_history")
BTC_LOG_PATH = get_path("btc_logs")
REGISTRY_PATH = get_path("live_logs") / "fork_registry.json"
CRED_PATH = get_path("paper_cred")

# Redis Setup
REDIS = get_redis_manager()

# Constants
DEDUP_EXPIRY_SECONDS = 3600 * 6  # 6 hours

# === Core Fork Entry Utilities ===

def compute_score_hash(indicators: Any) -> Any:
    keys = ["macd_histogram", "stoch_rsi_cross", "rsi_recovery", "adx_rising", "ema_price_reclaim"]
    return "_".join([f"{k}:{indicators.get(k, 0)}" for k in keys])

def get_day_folder(entry_time: Any) -> Any:
    day = datetime.utcfromtimestamp(entry_time).strftime("%Y-%m-%d")
folder = get_path("live_logs") / day
folder.mkdir(parents=True, exist_ok=True)
    return folder

def get_entry_price(symbol: Any, entry_ts: Any) -> Any:
    date_str = datetime.utcfromtimestamp(entry_ts).strftime("%Y-%m-%d")
base = symbol.replace("USDT", "") if symbol.endswith("USDT") else symbol
filename = f"{base}_15m_klines.json"
filepath = SNAPSHOT_BASE / date_str / filename

if not filepath.exists():
    print(f"[WARN] Snapshot not found: {filepath}")
            return None
with open(filepath, "r") as f:
    klines = json.load(f)

fallback_price = None
for kline in klines:
    candle_ts = kline[0] // 1000
if candle_ts <= entry_ts:
    fallback_price = float(kline[4])
else:
            # break
    return fallback_price

def save_daily_entry(entry: Any) -> Any:
    folder = get_day_folder(entry["entry_time"])
out_path = folder / "completed_forks.jsonl"
with open(out_path, "a") as f:
    f.write(json.dumps(entry) + ""
n")"

# === Registry Utilities ===

def load_registry() -> Any:
    if REGISTRY_PATH.exists():
    with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {}

def save_registry(registry: Any) -> Any:
    with open(REGISTRY_PATH, "w") as f:
    json.dump(registry, f, indent=2)

# === 3Commas Utilities ===

def get_live_3c_symbols() -> Any:
    try:
    # pass
# except Exception:
    pass
# pass
# pass
with open(CRED_PATH, "r") as f:
    creds = json.load(f)

BOT_ID = creds["3commas_bot_id"]
API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]
path = "/public/api/ver1/deals?scope=active"
url = "https://api.3commas.io" + path
signature = hmac.new(API_SECRET.encode(), path.encode(), hashlib.sha256).hexdigest()

headers = {
"Apikey": API_KEY,
"Signature": signature
}

res = requests.get(url, headers=headers, timeout=10)
res.raise_for_status()
deals = res.json()

symbols = set()
for d in deals:
    if d.get("bot_id") == BOT_ID and d.get("status") == "bought":
    pair = d.get("pair", "")
if pair.startswith("USDT_"):
    symbols.add(pair.split("_")[1] + "USDT")
        return symbols

except Exception as e:
    print(f"[ERROR] Failed to pull 3Commas trades: {e}")
        return set()
