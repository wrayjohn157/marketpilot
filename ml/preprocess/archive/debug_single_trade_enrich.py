#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

# === Input files ===
TRADE_PATH = Path("/home/signal/market7/ml/datasets/scrubbed_paper/2025-05-12/scrubbed_trades.jsonl")
FORK_PATH = Path("/home/signal/market7/output/fork_history/2025-05-12/fork_scores.jsonl")
TV_PATH = Path("/home/signal/market7/output/tv_history/2025-05-12/tv_kicker.jsonl")
BTC_PATH = Path("/home/signal/market7/dashboard_backend/btc_logs/2025-05-12/btc_snapshots.jsonl")

FORK_GRACE = 1800  # seconds
BTC_GRACE = 120
TARGET_SYMBOL = "ALPHAUSDT"

def load_jsonl(path):
    return [json.loads(line) for line in open(path) if line.strip()]

def iso_ts(s):
    s = s.rstrip("Z")
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f").timestamp()
    except ValueError:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").timestamp()

def normalize(symbol):
    return symbol.replace("USDT", "").upper()

def main():
    trades = load_jsonl(TRADE_PATH)
    forks = load_jsonl(FORK_PATH)
    tvs = load_jsonl(TV_PATH)
    btc_snaps = load_jsonl(BTC_PATH)

    trade = next((t for t in trades if t.get("symbol") == TARGET_SYMBOL), None)
    if not trade:
        print(f"❌ Trade for {TARGET_SYMBOL} not found.")
        return

    entry_ts = iso_ts(trade["entry_time"])
    base_symbol = normalize(trade["symbol"])

    # === Fork Match ===
    fork = next(
        (f for f in forks if normalize(f["symbol"]) == base_symbol and abs(iso_ts(f["ts_iso"]) - entry_ts) <= FORK_GRACE),
        None
    )

    # === TV Match ===
    tv = next(
        (t for t in tvs if t.get("pass") and normalize(t["symbol"]) == base_symbol and abs(t["timestamp"] - entry_ts) <= FORK_GRACE),
        None
    )

    # === BTC Snapshot Match ===
    btc = next(
        (b for b in btc_snaps if abs(iso_ts(b["ts_iso"]) - entry_ts) <= BTC_GRACE),
        None
    )

    # === Assemble merged result
    result = {
        "trade": trade,
        "fork_score": fork.get("score") if fork else None,
        "fork_ts": fork.get("ts_iso") if fork else None,
        "tv_boost": tv is not None,
        "tv_score": tv.get("tv_score") if tv else None,
        "tv_ts": tv.get("ts_iso") if tv else None,
        "btc_context": btc or {}
    }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
