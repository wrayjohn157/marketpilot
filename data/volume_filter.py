#!/usr/bin/env python3
import sys
import os
import requests
import json
import logging
import redis
from datetime import datetime
from pathlib import Path

# === Add project root to path ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# === Import centralized paths ===
from config.config_loader import PATHS

# === Setup logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# === Paths ===
OUTPUT_FILE = PATHS["filtered_pairs"]

# === Volume threshold (in USDT) ===
MIN_VOLUME_USDT = 3_000_000

# === Redis setup ===
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# === Excluded base tokens ===
EXCLUDED_BASES = [
    "USDT", "USDC", "FDUSD", "TUSD", "BUSD", "DAI",
    "EUR", "TRY", "BRL", "GBP", "UAH", "USD",
    "WBTC", "WETH"
]

def fetch_binance_volume_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"❌ Failed to fetch data: {e}")
        return []

    data = resp.json()
    qualified = []

    for item in data:
        symbol = item["symbol"]

        if not symbol.endswith("USDT") or any(x in symbol for x in ["UP", "DOWN", "BULL", "BEAR"]):
            continue

        base = symbol.replace("USDT", "")
        if base in EXCLUDED_BASES:
            continue

        try:
            quote_volume = float(item["quoteVolume"])
            if quote_volume >= MIN_VOLUME_USDT:
                redis_key = f"{base}_15m_klines"
                if not r.exists(redis_key):
                    logging.warning(f"⛔ Skipping {base}: Redis key '{redis_key}' not found.")
                    continue
                qualified.append(base)
        except Exception as e:
            logging.warning(f"⚠️ Skipping {symbol}: {e}")

    return sorted(qualified)

def main():
    qualified_symbols = fetch_binance_volume_data()
    count = len(qualified_symbols)
    logging.info(f"✅ Qualified symbols: {count} passed all volume and Redis checks.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(qualified_symbols, f, indent=4)
    logging.info(f"💾 Filtered pairs saved to: {OUTPUT_FILE}")

    timestamp = datetime.utcnow().isoformat()
    r.set("last_scan_vol", timestamp)
    r.set("volume_filter_count", count)
    logging.info(f"📦 Redis updated: last_scan_vol={timestamp}, volume_filter_count={count}")

    VOLUME_PASSED_SET = "VOLUME_PASSED_TOKENS"
    r.delete(VOLUME_PASSED_SET)
    for token in qualified_symbols:
        r.sadd(VOLUME_PASSED_SET, token)
    logging.info(f"🔁 Redis set '{VOLUME_PASSED_SET}' populated.")

if __name__ == "__main__":
    main()
