#!/usr/bin/env python3
import os
import sys
import json
import redis
import datetime

# ✅ Add project root to sys.path so absolute imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rrr_filter.run_rrr_filter import run_rrr_filter

# Redis setup
r = redis.Redis(decode_responses=True)

# Absolute file paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # /home/signal/taapi/market6
APPROVED_FILE = os.path.join(BASE_DIR, "output", "approved_trades.json")
RRR_PASS_FILE = os.path.join(BASE_DIR, "output", "rrr_passed.json")

# Redis keys
FINAL_FILTER_KEY = "FINAL_RRR_FILTERED_TRADES"
FINAL_TRADES_KEY = "FINAL_TRADES"
EMA_WINDOW = 5

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

def main():
    print("🚀 Running RRR filter engine...")

    # Clear old Redis keys
    r.delete(FINAL_FILTER_KEY)
    r.delete(FINAL_TRADES_KEY)

    if not os.path.exists(APPROVED_FILE):
        print(f"❌ Missing file: {APPROVED_FILE}")
        return

    with open(APPROVED_FILE, "r") as f:
        symbols = json.load(f)

    filtered = {}
    rejections = 0
    skips = 0
    failures = 0

    for symbol in symbols:
        s = symbol.upper()
        ind_1h = get_indicator(s, "1h")
        ind_15m = get_indicator(s, "15m")
        klines = get_klines(s, "15m")

        if not ind_1h:
            print(f"⚠️ Skipping {s}: missing 1h indicators")
            skips += 1
            continue
        if not ind_15m:
            print(f"⚠️ Skipping {s}: missing 15m indicators")
            skips += 1
            continue
        if len(klines) < EMA_WINDOW + 6:
            print(f"⚠️ Skipping {s}: not enough klines ({len(klines)} candles)")
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
            print(f"❌ Error scoring {s}: {e}")
            failures += 1
            continue

        if not result:
            print(f"❌ No result returned for {s}")
            failures += 1
            continue

        score = result.get("score", 0)
        if result.get("passed"):
            result["pair"] = f"USDT_{s}"
            result["exchange"] = "binance"
            result["type"] = "long"
            result["market_price"] = ind_1h.get("latest_close")
            filtered[s] = make_json_serializable(result)
            print(f"✅ Passed: {s} | Score: {score:.2f}")
        else:
            print(f"❌ Rejected: {s} | Score: {score:.2f}")
            reasons = result.get("reasons", [])
            if reasons:
                for reason in reasons:
                    print(f"    🪫 {reason}")
            else:
                print("    ⚠️ No rejection reasons provided.")
            rejections += 1

    # Save final trades to file
    with open(RRR_PASS_FILE, "w") as f:
        json.dump(filtered, f, indent=2)

    # Save to Redis
    r.set(FINAL_FILTER_KEY, json.dumps(filtered))
    r.set(FINAL_TRADES_KEY, json.dumps(list(filtered.keys())))
    r.set("last_scan_rrr", datetime.datetime.utcnow().isoformat())
    r.set("rrr_filter_count_in", len(symbols))
    r.set("rrr_filter_count_out", len(filtered))
    r.set("final_trades_count", len(filtered))

    # Summary
    print(f"\n📊 RRR Filter Summary:")
    print(f" - ✅ Passed:   {len(filtered)}")
    print(f" - ❌ Rejected: {rejections}")
    print(f" - ⚠️ Skipped:  {skips}")
    print(f" - 💥 Errors:   {failures}")
    print(f" - 📄 Saved final trades to: {RRR_PASS_FILE}")

if __name__ == "__main__":
    main()
