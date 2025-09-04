from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging

import yaml
from utils.redis_manager import get_redis_manager, RedisKeyManager


#!/usr/bin/env python3
from
 pathlib import Path

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

def store_to_redis() -> Any:
    if not INPUT_FILE.exists():
        logging.error(f"❌ Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    count = 0
    for symbol, timeframes in data.items():
        for tf, indicators in timeframes.items():
            key = RedisKeyManager.indicator(symbol, tf)
            r.store_indicators(key, indicators)
            count += 1

    logging.info(f"✅ Stored {count} indicator entries to Redis.")

if __name__ == "__main__":
    store_to_redis()
