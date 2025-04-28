#!/usr/bin/env python3
import json
import redis
import logging
from datetime import datetime
from pathlib import Path
import yaml

from indicators.rrr_filter.run_rrr_filter import run_rrr_filter

# === Load config paths ===
CONFIG_PATH = "/home/signal/market7/config/paths_config.yaml"
with open(CONFIG_PATH) as f:
    paths = yaml.safe_load(f)

APPROVED_FILE = Path(paths["final_fork_rrr_trades"])
RRR_PASS_FILE = Path(paths["fork_backtest_candidates_path"])

# Redis keys
FINAL_FILTER_KEY = "FINAL_RRR_FILTERED_TRADES"
FINAL_TRADES_KEY = "FINAL_TRADES"

# Redis setup
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Constants
EMA_WINDOW = 5

# === Helper Functions ===
def get_indicator(symbol, tf):
    key = f"{symbol}_{tf}"
    data = r.get(key)
    return json.loads(data) if data else None

def get_klines(symbol, tf):
    key = f"{symbol}_{tf}_klines"
    candles = r.lrange(key, 0, -1)
    return [json.loads(c) for c in candles] if candles else []

def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(i) for i in obj]
    elif hasattr(obj, "item"):
        return obj.item()
    elif isinstance(obj, (bool, int, float, str, type(None))):
        return obj
    return str(obj)

# === Main Execution ===
def main():
    logging.info("🚀 Running RRR filter engine...")

    # Clear old Redis keys
    r.delete(FINAL_FILTER_KEY)
    r.delete(FINAL_TRADES_KEY)

    if not APPROVED_FILE.exists():
        logging.error(f"❌ Missing approved trades file: {APPROVED_FILE}")
        return

    with open(APPROVED_FILE) as f:
        symbols = json.load(f)

    filtered = {}
    rejections = skips = failures = 0

    for symbol in symbols:
        s = symbol.upper()
        ind_1h = get_indicator(s, "1h")
        ind_15m = get_indicator(s, "15m")
        klines = get_klines(s, "15m")

        if not ind_1h:
            logging.warning(f"⚠️ Skipping {s}: missing 1h indicators")
            skips += 1
            continue
        if not ind_15m:
            logging.warning(f"⚠️ Skipping {s}: missing 15m indicators")
            skips += 1
            continue
        if len(klines) < EMA_WINDOW + 6:
            logging.warning(f"⚠️ Skipping {s}: not enough klines ({len(klines)} candles)")
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
            logging.error(f"❌ Error scoring {s}: {e}")
            failures += 1
            continue

        if not result:
            logging.error(f"❌ No result returned for {s}")
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
            logging.info(f"✅ Passed: {s} | Score: {score:.2f}")
        else:
            logging.info(f"❌ Rejected: {s} | Score: {score:.2f}")
            reasons = result.get("reasons", [])
            for reason in reasons:
                logging.info(f"    🪫 {reason}")
            rejections += 1

    # Save outputs
    with open(RRR_PASS_FILE, "w") as f:
        json.dump(filtered, f, indent=2)

    r.set(FINAL_FILTER_KEY, json.dumps(filtered))
    r.set(FINAL_TRADES_KEY, json.dumps(list(filtered.keys())))
    r.set("last_scan_rrr", datetime.utcnow().isoformat())
    r.set("rrr_filter_count_in", len(symbols))
    r.set("rrr_filter_count_out", len(filtered))
    r.set("final_trades_count", len(filtered))

    # Summary
    logging.info("\n📊 RRR Filter Summary:")
    logging.info(f" - ✅ Passed:   {len(filtered)}")
    logging.info(f" - ❌ Rejected: {rejections}")
    logging.info(f" - ⚠️ Skipped:  {skips}")
    logging.info(f" - 💥 Errors:   {failures}")
    logging.info(f" - 📄 Saved final trades to: {RRR_PASS_FILE}")

if __name__ == "__main__":
    main()
