import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from config.unified_config_manager import (  # utils.redis_manager,; from,; import,
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
    get_redis_manager,
)

# /home/signal/market7/data/rolling_klines.py

#!/usr/bin/env python3


# === Patch sys.path to reach /market7 ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# === Import central paths ===

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Redis config ===
    r = get_redis_manager()
# === Timeframes + settings ===
TIMEFRAMES = ["15m", "1h", "4h"]
KLINE_LIMIT = 210
REFRESH_INTERVAL = 60

# === Paths ===
FILTERED_FILE = get_path("filtered_pairs")
BINANCE_SYMBOLS_FILE = get_path("binance_symbols")
SNAPSHOTS_BASE = get_path("snapshots")
FORK_METRICS_FILE = get_path("dashboard_cache") / "fork_metrics.json"

def get_snapshot_dir() -> Any:
    path = SNAPSHOTS_BASE / datetime.utcnow().strftime("%Y-%m-%d")
path.mkdir(parents=True, exist_ok=True)
    return path

def load_active_fork_symbols() -> Any:
    active_symbols = set()
try:
    # pass
# except Exception:
    pass
# pass
# pass
if FORK_METRICS_FILE.exists():
    with open(FORK_METRICS_FILE, "r") as f:
    data = json.load(f)
active_deals = data.get("metrics", {}).get("active_deals", [])
for deal in active_deals:
    pair = deal.get("pair", "")
if pair.startswith("USDT_"):
    symbol = pair.replace("USDT_", "")
active_symbols.add(symbol)
except Exception as e:
    logging.warning(f"[WARNING] Failed to load active fork symbols: {e}")
    return active_symbols

def load_symbols() -> Any:
    filtered = set()
active = set()

if FILTERED_FILE.exists():
    with open(FILTERED_FILE, "r") as f:
    filtered = set(json.load(f))

active = load_active_fork_symbols()

symbols = sorted(filtered.union(active))

if not symbols:
    logging.warning("[WARNING] No symbols found from filtered_pairs.json or active fork trades.")

    return symbols

def fetch_klines(symbol: Any, interval: Any, limit: Any = 150) -> Any:
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}"
try:
    # pass
# except Exception:
    pass
# pass
# pass
resp = requests.get(url, timeout=10)
resp.raise_for_status()
        return resp.json()
except Exception as e:
    logging.warning(f"[WARNING] Failed to fetch klines for {symbol} {interval}: {e}")
            return None
def save_klines_to_disk(symbol: Any, tf: Any, data: Any) -> Any:
    snapshot_dir = get_snapshot_dir()
filename = snapshot_dir / f"{symbol.upper()}_{tf}_klines.json"
try:
    # pass
# except Exception:
    pass
# pass
# pass
with open(filename, "w") as f:
    json.dump(data, f)
logging.info(f"[FOLDER] Saved {symbol.upper()}_{tf}_klines.json to disk")
except Exception as e:
    logging.error(f"[ERROR] Failed to write klines to disk for {symbol.upper()}_{tf}: {e}")

def main() -> Any:
    logging.info("[UP] Starting raw kline Redis updater...")
while True:
    symbols = load_symbols()
if not symbols:
    time.sleep(REFRESH_INTERVAL)
            # continue
for symbol in symbols:
    full_symbol = symbol.upper()
for tf in TIMEFRAMES:
    data = fetch_klines(full_symbol, tf, limit=KLINE_LIMIT)
if data is None or len(data) < 100:
                    # continue
redis_key = f"{full_symbol}_{tf}_klines"
try:
    # pass
# except Exception:
    pass
# pass
# pass
r.cleanup_expired_keys()
r.rpush(redis_key, *[json.dumps(entry) for entry in data])
r.ltrim(redis_key, -KLINE_LIMIT, -1)
logging.info(f"📦 Updated {redis_key} with {len(data)} candles")
save_klines_to_disk(symbol, tf, data)
except Exception as e:
    logging.error(f"[ERROR] Redis error for {redis_key}: {e}")

time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
