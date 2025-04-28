#!/usr/bin/env python3
import json
import redis
import logging
from pathlib import Path
import yaml

# === Logging setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Load config paths ===
CONFIG_PATH = "/home/signal/market7/config/paths_config.yaml"
with open(CONFIG_PATH) as f:
    paths = yaml.safe_load(f)

# Input file path
INPUT_FILE = Path(paths["dashboard_cache"]) / "market_scan.json"

# Redis config
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Redis connection
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
except Exception as e:
    logging.error(f"Redis connection error: {e}")
    exit(1)

def store_to_redis():
    if not INPUT_FILE.exists():
        logging.error(f"❌ Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    count = 0
    for symbol, timeframes in data.items():
        for tf, indicators in timeframes.items():
            key = f"{symbol.upper()}_{tf}"
            r.set(key, json.dumps(indicators))
            count += 1

    logging.info(f"✅ Stored {count} indicator entries to Redis.")

if __name__ == "__main__":
    store_to_redis()
