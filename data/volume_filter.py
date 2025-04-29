#!/usr/bin/env python3
import sys
import os
import requests
import json
import logging
from datetime import datetime
from pathlib import Path
import redis

# === Setup ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.config_loader import PATHS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# === Paths ===
SYMBOL_LIST_FILE = Path("/home/signal/market7/data/binance_symbols.json")
OUTPUT_FILE = PATHS["filtered_pairs"]

# === Volume threshold (in USDT) ===
MIN_VOLUME_USDT = 3_000_000

# === Redis setup ===
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def fetch_volume_map():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return {item["symbol"]: float(item["quoteVolume"]) for item in resp.json()}
    except Exception as e:
        logging.error(f"❌ Failed to fetch volume data: {e}")
        return {}

def main():
    if not SYMBOL_LIST_FILE.exists():
        logging.error(f"❌ Missing symbol list: {SYMBOL_LIST_FILE}")
        return

    with open(SYMBOL_LIST_FILE, "r") as f:
        all_symbols = json.load(f)

    volume_map = fetch_volume_map()
    qualified = []

    for base in all_symbols:
        full_symbol = f"{base}USDT"
        vol = volume_map.get(full_symbol)
        if vol and vol >= MIN_VOLUME_USDT:
            qualified.append(base)
        else:
            logging.warning(f"⛔ Skipping {base}: volume {vol} below threshold")

    qualified = sorted(set(qualified))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(qualified, f, indent=4)

    logging.info(f"✅ Qualified: {len(qualified)}")
    logging.info(f"💾 Saved to: {OUTPUT_FILE}")

    timestamp = datetime.utcnow().isoformat()
    r.set("last_scan_vol", timestamp)
    r.set("volume_filter_count", len(qualified))
    r.delete("VOLUME_PASSED_TOKENS")
    for token in qualified:
        r.sadd("VOLUME_PASSED_TOKENS", token)

if __name__ == "__main__":
    main()
