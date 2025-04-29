# /home/signal/market7/data/rolling_klines.py

#!/usr/bin/env python3
import time
import json
import redis
import logging
import requests
from datetime import datetime
from pathlib import Path
import sys

# === Patch sys.path to reach /market7 ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# === Import central paths ===
from config.config_loader import PATHS

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Redis config ===
r = redis.Redis(host="localhost", port=6379, db=0)

# === Timeframes + settings ===
TIMEFRAMES = ["15m", "1h", "4h"]
KLINE_LIMIT = 210
REFRESH_INTERVAL = 60

# === Paths ===
FILTERED_FILE = PATHS["filtered_pairs"]
BINANCE_SYMBOLS_FILE = PATHS["binance_symbols"]
SNAPSHOTS_BASE = PATHS["snapshots"]
FORK_METRICS_FILE = Path("/home/signal/market7/dashboard_backend/cache/fork_metrics.json")

def get_snapshot_dir():
    path = SNAPSHOTS_BASE / datetime.utcnow().strftime("%Y-%m-%d")
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_active_fork_symbols():
    active_symbols = set()
    try:
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
        logging.warning(f"⚠️ Failed to load active fork symbols: {e}")
    return active_symbols

def load_symbols():
    filtered = set()
    active = set()

    if FILTERED_FILE.exists():
        with open(FILTERED_FILE, "r") as f:
            filtered = set(json.load(f))

    active = load_active_fork_symbols()

    symbols = sorted(filtered.union(active))

    if not symbols:
        logging.warning("⚠️ No symbols found from filtered_pairs.json or active fork trades.")

    return symbols

def fetch_klines(symbol, interval, limit=150):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.warning(f"⚠️ Failed to fetch klines for {symbol} {interval}: {e}")
        return None

def save_klines_to_disk(symbol, tf, data):
    snapshot_dir = get_snapshot_dir()
    filename = snapshot_dir / f"{symbol.upper()}_{tf}_klines.json"
    try:
        with open(filename, "w") as f:
            json.dump(data, f)
        logging.info(f"📁 Saved {symbol.upper()}_{tf}_klines.json to disk")
    except Exception as e:
        logging.error(f"❌ Failed to write klines to disk for {symbol.upper()}_{tf}: {e}")

def main():
    logging.info("📈 Starting raw kline Redis updater...")
    while True:
        symbols = load_symbols()
        if not symbols:
            time.sleep(REFRESH_INTERVAL)
            continue

        for symbol in symbols:
            full_symbol = symbol.upper()
            for tf in TIMEFRAMES:
                data = fetch_klines(full_symbol, tf, limit=KLINE_LIMIT)
                if data is None or len(data) < 100:
                    continue
                redis_key = f"{full_symbol}_{tf}_klines"
                try:
                    r.delete(redis_key)
                    r.rpush(redis_key, *[json.dumps(entry) for entry in data])
                    r.ltrim(redis_key, -KLINE_LIMIT, -1)
                    logging.info(f"📦 Updated {redis_key} with {len(data)} candles")
                    save_klines_to_disk(symbol, tf, data)
                except Exception as e:
                    logging.error(f"❌ Redis error for {redis_key}: {e}")

        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
