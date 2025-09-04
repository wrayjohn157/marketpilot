from typing import Dict, List, Optional, Any, Union, Tuple
import json

import redis
import requests

import time

from
 pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SYMBOLS_PATH = BASE_DIR / "lev" / "data" / "perps" / "lev_symbols.json"

# Redis connection
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Binance API template
FUNDING_RATE_URL = "https://fapi.binance.com/fapi/v1/fundingRate?symbol={}&limit=1"

def load_symbols() -> Any:
    with open(SYMBOLS_PATH, "r") as f:
        return json.load(f)

def fetch_funding(symbol: Any) -> Any:
    try:
        url = FUNDING_RATE_URL.format(symbol)
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return {
                "timestamp": int(data[0]["fundingTime"]) // 1000,
                "fundingRate": float(data[0]["fundingRate"])
            }
    except Exception as e:
        print(f"⚠️ Error fetching {symbol}: {e}")
    return None

def save_to_redis(symbol: Any, entry: Any, max_len: Any = 48) -> Any:
    key = f"funding:{symbol}"

    # Force delete if wrong type
    if r.type(key) != "list":
        r.delete(key)

    # Append new entry
    r.rpush(key, json.dumps(entry))
    # Trim to max length
    r.ltrim(key, -max_len, -1)

    # Get length for logging
    length = r.llen(key)
    print(f"💾 {symbol} | Funding: {entry['fundingRate']:.6f} | Stored entries: {length}")

if __name__ == "__main__":
    symbols = load_symbols()
    for sym in symbols:
        entry = fetch_funding(sym)
        if entry:
            save_to_redis(sym, entry)
        time.sleep(0.2)  # Avoid hammering API
