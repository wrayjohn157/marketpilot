#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

# === Configurable Paths ===
FORK_PATH = Path("/home/signal/market7/output/fork_history/2025-05-12/fork_scores.jsonl")
TV_PATH = Path("/home/signal/market7/output/tv_history/2025-05-12/tv_kicker.jsonl")
BTC_PATH = Path("/home/signal/market7/dashboard_backend/btc_logs/2025-05-12/btc_snapshots.jsonl")

TRADE = {
    "trade_id": 2349642812,
    "symbol": "ALPHAUSDT",
    "entry_time": "2025-05-12T06:23:22Z",
    "exit_time": "2025-05-12T06:47:20Z",
    "entry_price": 0.0312312,
    "exit_price": 0.0313686,
    "pnl_pct": 0.44,
    "usd_profit": 1.17,
    "status": "completed",
    "strategy": "long",
    "safety_orders": 0,
    "max_safety_orders": 0,
    "tsl_enabled": False
}

# === Output Path ===
OUT_PATH = Path("merged_alpha_trade.jsonl")

# === Helpers ===
def parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def match_fork(forks, symbol, ts):
    ts_dt = parse_iso(ts)
    for fork in forks:
        if fork["symbol"] == symbol:
            fork_ts = datetime.fromisoformat(fork["ts_iso"].replace("Z", "+00:00"))
            if abs(ts_dt - fork_ts) < timedelta(seconds=3):
                return fork
    return None

def match_tv(tv_list, symbol, ts):
    ts_dt = parse_iso(ts)
    for entry in tv_list:
        if entry["symbol"] == symbol and entry["pass"]:
            tv_ts = datetime.fromisoformat(entry["ts_iso"].replace("Z", "+00:00"))
            if abs(ts_dt - tv_ts) < timedelta(seconds=5):
                return entry
    return None

def match_btc_snapshot(btc_list, ts: str):
    ts_dt = parse_iso(ts)
    closest = None
    min_diff = timedelta.max
    for snap in btc_list:
        snap_ts = datetime.fromisoformat(snap["ts_iso"].replace("Z", "+00:00"))
        diff = abs(snap_ts - ts_dt)
        if diff < min_diff:
            closest = snap
            min_diff = diff
    return closest

# === Main ===
def main():
    forks = load_jsonl(FORK_PATH)
    tvs = load_jsonl(TV_PATH)
    btc = load_jsonl(BTC_PATH)

    trade_symbol = TRADE["symbol"].replace("USDT", "")
    entry_ts = TRADE["entry_time"]
    exit_ts = TRADE["exit_time"]

    matched_fork = match_fork(forks, trade_symbol, entry_ts)
    matched_tv = match_tv(tvs, trade_symbol, entry_ts)
    btc_entry = match_btc_snapshot(btc, entry_ts)
    btc_exit = match_btc_snapshot(btc, exit_ts)

    out = {
        "trade": TRADE,
        "fork": matched_fork,
        "tv_kicker": matched_tv,
        "btc_context": {
            "entry": btc_entry,
            "exit": btc_exit
        }
    }

    with OUT_PATH.open("w") as f:
        f.write(json.dumps(out) + "\n")

    print(f"✅ Merged result written to {OUT_PATH}")

if __name__ == "__main__":
    main()
