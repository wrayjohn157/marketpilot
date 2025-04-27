#!/usr/bin/env python3
import os
import time
import json
import redis
import logging
import requests
from datetime import datetime

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Redis config
r = redis.Redis(host="localhost", port=6379, db=0)

# Timeframes + settings
TIMEFRAMES = ["15m", "1h", "4h"]
KLINE_LIMIT = 210
REFRESH_INTERVAL = 60

# Filtered tokens file
BASE_PATH = os.path.dirname(__file__)
FILTERED_FILE = os.path.join(BASE_PATH, "filtered_pairs.json")

def get_snapshot_dir():
    path = os.path.join(BASE_PATH, "snapshots", datetime.utcnow().strftime("%Y-%m-%d"))
    os.makedirs(path, exist_ok=True)
    return path

def load_filtered_tokens():
    if not os.path.exists(FILTERED_FILE):
        logging.error("Missing filtered_pairs.json")
        return []
    with open(FILTERED_FILE, "r") as f:
        return json.load(f)

def fetch_klines(symbol, interval, limit=150):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        logging.warning(f"Failed to fetch klines for {symbol} {interval}: {e}")
        return None

def save_klines_to_disk(symbol, tf, data):
    snapshot_dir = get_snapshot_dir()
    filename = os.path.join(snapshot_dir, f"{symbol.upper()}_{tf}_klines.json")
    try:
        with open(filename, "w") as f:
            json.dump(data, f)
        logging.info(f"📁 Saved {symbol.upper()}_{tf}_klines.json to disk")
    except Exception as e:
        logging.error(f"❌ Failed to write klines to disk for {symbol.upper()}_{tf}: {e}")

def main():
    logging.info("📈 Starting raw kline Redis updater...")
    while True:
        symbols = load_filtered_tokens()
        for symbol in symbols:
            full_symbol = symbol.upper() + "USDT"
            for tf in TIMEFRAMES:
                data = fetch_klines(full_symbol, tf, limit=KLINE_LIMIT)
                if data is None or len(data) < 100:
                    continue
                redis_key = f"{symbol.upper()}_{tf}_klines"
                r.delete(redis_key)
                r.rpush(redis_key, *[json.dumps(entry) for entry in data])
                r.ltrim(redis_key, -KLINE_LIMIT, -1)
                logging.info(f"📦 Updated {redis_key} with {len(data)} candles")
                save_klines_to_disk(symbol, tf, data)
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
