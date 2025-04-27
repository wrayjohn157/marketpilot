#!/usr/bin/env python3
import os
import json
import redis
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Redis config
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Input JSON file path
BASE_PATH = os.path.dirname(__file__)
INPUT_FILE = os.path.join(BASE_PATH, "market_scan.json")

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def store_to_redis():
    if not os.path.exists(INPUT_FILE):
        logging.error(f"Input file not found: {INPUT_FILE}")
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
