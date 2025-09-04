from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
import os
import sys

import yaml

from indicators.rrr_filter.run_rrr_filter import run_rrr_filter
from utils.redis_manager import get_redis_manager, RedisKeyManager


#!/usr/bin/env python3
from
 datetime import datetime

# Add root to sys.path
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# === Load config paths ===
CONFIG_PATH = PROJECT_ROOT / "config" / "paths_config.yaml"
with open(CONFIG_PATH) as f:
paths = yaml.safe_load(f)

APPROVED_FILE = Path(paths["final_fork_rrr_trades"])
RRR_PASS_FILE = Path(paths["fork_trade_candidates_path"])

# Redis keys
FINAL_FILTER_KEY = "FINAL_RRR_FILTERED_TRADES"
FINAL_TRADES_KEY = "queues:final_trades"

r = get_redis_manager()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

EMA_WINDOW = 5

def get_indicator(symbol: Any, tf: Any) -> Any:
key = f"{symbol}_{tf}"
data = r.get_cache(key)
    return json.loads(data) if data else None

def get_klines(symbol: Any, tf: Any) -> Any:
key = f"{symbol}_{tf}_klines"
candles = r.lrange(key, 0, -1)
    return [json.loads(c) for c in candles] if candles else []

def make_json_serializable(obj: Any) -> Any:
if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
elif isinstance(obj, list):
        return [make_json_serializable(i) for i in obj]
elif hasattr(obj, "item"):
        return obj.item()
elif isinstance(obj, (bool, int, float, str, type(None))):
        return obj
    return str(obj)

def main() -> Any:
logging.info("[LAUNCH] Running RRR filter engine...")
r.cleanup_expired_keys()
r.cleanup_expired_keys()

if not APPROVED_FILE.exists():
logging.error(f"[ERROR] Missing approved trades file: {APPROVED_FILE}")
        return

with open(APPROVED_FILE) as f:
symbols = json.load(f)

filtered = {}
rejections = skips = failures = 0

for symbol in symbols:
if isinstance(symbol, dict):
s = symbol.get("symbol", "").upper()
else:
s = symbol.upper()
if not s:
logging.warning("[WARNING] Skipping entry with missing symbol")
            continue

ind_1h = get_indicator(s, "1h")
        ind_15m = get_indicator(s, "15m")
        klines = get_klines(s, "15m")

if not ind_1h:
logging.warning(f"[WARNING] Skipping {s}: missing 1h indicators")
skips += 1
            continue
if not ind_15m:
logging.warning(f"[WARNING] Skipping {s}: missing 15m indicators")
skips += 1
            continue
if len(klines) < EMA_WINDOW + 6:
logging.warning(f"[WARNING] Skipping {s}: not enough klines ({len(klines)} candles)")
skips += 1
            continue

try:
result = run_rrr_filter(
s,
klines,
ind_1h.get("ATR"),
ind_1h.get("ADX14"),
{
"ema50": ind_15m.get("EMA50"),
"ema200": ind_15m.get("EMA200")
}
)
except Exception as e:
logging.error(f"[ERROR] Error scoring {s}: {e}")
failures += 1
            continue

if not result:
logging.error(f"[ERROR] No result returned for {s}")
failures += 1
            continue

score = result.get("score", 0)
if result.get("passed"):
result.update({
"pair": f"USDT_{s}",
"exchange": "binance",
"type": "long",
"market_price": ind_1h.get("latest_close")
})
filtered[s] = make_json_serializable(result)
logging.info(f"[OK] Passed: {s} | Score: {score:.2f}")
else:
logging.info(f"[ERROR] Rejected: {s} | Score: {score:.2f}")
for reason in result.get("reasons", []):
logging.info(f"    🪫 {reason}")
rejections += 1

with open(RRR_PASS_FILE, "w") as f:
json.dump(filtered, f, indent=2)

r.store_indicators(FINAL_FILTER_KEY, filtered)
r.store_indicators(FINAL_TRADES_KEY, list(filtered.keys()))
r.set_cache("last_scan_rrr", datetime.utcnow().isoformat())
r.set_cache("rrr_filter_count_in", len(symbols))
r.set_cache("rrr_filter_count_out", len(filtered))
r.set_cache("final_trades_count", len(filtered))

logging.info(""
n[STATS] RRR Filter Summary:")"
logging.info(f" - [OK] Passed:   {len(filtered)}")
logging.info(f" - [ERROR] Rejected: {rejections}")
logging.info(f" - [WARNING] Skipped:  {skips}")
logging.info(f" - 💥 Errors:   {failures}")
logging.info(f" - 📄 Saved fork trade candidates to: {RRR_PASS_FILE}")

if __name__ == "__main__":
main()
