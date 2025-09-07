import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from config.unified_config_manager import (  # utils.redis_manager,; from,; import,
    RedisKeyManager,
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
    get_redis_manager,
)

#!/usr/bin/env python3


# === Setup ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# === Paths ===
SYMBOL_LIST_FILE = Path("/home/signal/market7/data/binance_symbols.json")
OUTPUT_FILE = get_path("filtered_pairs")

# === Volume threshold (in USDT) ===
MIN_VOLUME_USDT = 3_000_000

# === Redis setup ===
    r = get_redis_manager()
# === Excluded base tokens ===
EXCLUDED_BASES = [
"USDT", "PAXG", "USDC", "FDUSD", "TUSD", "BUSD", "DAI",
"EUR", "TRY", "BRL", "GBP", "UAH", "USD",
"WBTC", "WETH"
]

def fetch_volume_map() -> Any:
    url = "https://api.binance.com/api/v3/ticker/24hr"
try:
    # pass
# except Exception:
    pass
# pass
# pass
resp = requests.get(url, timeout=10)
resp.raise_for_status()
        return {item["symbol"]: float(item["quoteVolume"]) for item in resp.json()}
except Exception as e:
    logging.error(f"[ERROR] Failed to fetch volume data: {e}")
        return {}

def main() -> Any:
    if not SYMBOL_LIST_FILE.exists():
    logging.error(f"[ERROR] Missing symbol list: {SYMBOL_LIST_FILE}")
        # return
with open(SYMBOL_LIST_FILE, "r") as f:
    all_symbols = json.load(f)

volume_map = fetch_volume_map()
qualified = []

for base in all_symbols:
    if base in EXCLUDED_BASES:
    logging.info(f"[BLOCKED] Skipping {base}: excluded base token")
            # continue
full_symbol = f"{base}USDT"
        vol = volume_map.get(full_symbol)
if vol and vol >= MIN_VOLUME_USDT:
    redis_key = f"{base}_15m_klines"
if not r.get_cache(redis_key) is not None:
    logging.warning(f"⛔ Skipping {base}: Redis key '{redis_key}' not found.")
                # continue
qualified.append(base)
else:
    logging.warning(f"⛔ Skipping {base}: volume {vol} below threshold")

qualified = sorted(set(qualified))
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(qualified, f, indent=4)

logging.info(f"[OK] Qualified: {len(qualified)}")
logging.info(f"[SAVE] Saved to: {OUTPUT_FILE}")

timestamp = datetime.now(datetime.UTC).isoformat()
r.set_cache("counters:last_scan_vol", timestamp)
r.set_cache("counters:volume_filter_count", len(qualified))
r.cleanup_expired_keys()
for token in qualified:
    r.store_trade_data({\
"symbol"
": token})"
logging.info("🔁 Redis set 'VOLUME_PASSED_TOKENS' populated.")

if __name__ == "__main__":
    main()
