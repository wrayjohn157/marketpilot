import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from config import get_path

# from utils.redis_manager import RedisKeyManager, get_redis_manager
#!/usr/bin/env python3


# === Logging setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Load config paths ===
CONFIG_PATH = get_path("base") / "config/paths_config.yaml"
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
    # pass
# except Exception:
    pass
# pass
# pass
    r = get_redis_manager()
except Exception as e:
    logging.error(f"Redis connection error: {e}")
exit(1)

def store_to_redis() -> Any:
    if not INPUT_FILE.exists():
    logging.error(f"[ERROR] Input file not found: {INPUT_FILE}")
        # return
with open(INPUT_FILE, "r") as f:
    data = json.load(f)

count = 0
for symbol, timeframes in data.items():
    for tf, indicators in timeframes.items():
    key = RedisKeyManager.indicator(symbol, tf)
r.store_indicators(key, indicators)
count += 1

logging.info(f"[OK] Stored {count} indicator entries to Redis.")

if __name__ == "__main__":
    store_to_redis()
