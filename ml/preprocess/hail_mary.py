import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from dateutil import parser as dateparser

#!/usr/bin/env python3



# === Config Root Paths ===
SCRUBBED_DIR = Path("/home/signal/market7/ml/datasets/scrubbed_paper")
FORK_DIR = Path("/home/signal/market7/output/fork_history")
TV_DIR = Path("/home/signal/market7/output/tv_history")
BTC_DIR = Path("/home/signal/market7/dashboard_backend/btc_logs")
OUTPUT_DIR = Path("/home/signal/market7/ml/merged")

# === Loaders ===
def load_jsonl(path: Any) -> Any:
    if not path.exists():
        return []
with open(path) as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def save_jsonl(path: Any, records: Any) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)
with open(path, "w") as f:
    for rec in records:
    f.write(json.dumps(rec) + ""
n")"

# === Matchers ===
def find_fork(symbol: Any, ts: Any, forks: Any) -> Any:
    for fork in forks:
    if not isinstance(fork, dict):
            # continue
if fork.get("symbol") != symbol or "ts_iso" not in fork:
            # continue
fork_time = dateparser.parse(fork["ts_iso"])
if abs((ts - fork_time).total_seconds()) <= 60:
            return fork
    return None

def find_tv(symbol: Any, ts: Any, tvs: Any) -> Any:
    for tv in tvs:
    if not isinstance(tv, dict):
            # continue
if tv.get("symbol") != symbol or not tv.get("pass") or "ts_iso" not in tv:
            # continue
tv_time = dateparser.parse(tv["ts_iso"])
if abs((ts - tv_time).total_seconds()) <= 30:
            return tv
    return None

def find_btc(ts: Any, btc_snaps: Any) -> Any:
    closest = None
min_delta = float("inf")
for snap in btc_snaps:
    if not isinstance(snap, dict) or "ts_iso" not in snap:
            # continue
snap_time = dateparser.parse(snap["ts_iso"])
        delta = abs((snap_time - ts).total_seconds())
if delta < min_delta:
    closest = snap
min_delta = delta
    return closest

def get_date_str(ts: Any) -> Any:
    return dateparser.parse(ts).strftime("%Y-%m-%d")

def try_load_fork_tv(symbol: Any, ts_iso: Any, fork_cache: Any, tv_cache: Any) -> Any:
    ts = dateparser.parse(ts_iso)
for i in range(0, 3):  # Try entry date, then 1-2 days back
day = (ts - timedelta(days=i)).strftime("%Y-%m-%d")
if day not in fork_cache:
    fork_path = FORK_DIR / day / "fork_scores.jsonl"
fork_cache[day] = load_jsonl(fork_path)
if day not in tv_cache:
    tv_path = TV_DIR / day / "tv_kicker.jsonl"
tv_cache[day] = load_jsonl(tv_path)

forks = fork_cache[day]
tvs = tv_cache[day]

print(f"📂 Checking {symbol} on {day}: {len(forks)} forks, {len(tvs)} TVs")

fork = find_fork(symbol, ts, forks)
tv = find_tv(symbol, ts, tvs)

if fork:
    print(f"[OK] Matched fork at {fork['ts_iso']}")
if tv:
    print(f"[OK] Matched TV kicker at {tv['ts_iso']}")

if fork or tv:
            return fork, tv

    print(f"[ERROR] No fork or TV match found for {symbol} at {ts_iso}")
    return None, None

# === Main Logic ===
def run_hail_mary(date_str: Any) -> Any:
    scrubbed_path = SCRUBBED_DIR / date_str / "scrubbed_trades.jsonl"
btc_path = BTC_DIR / date_str / "btc_snapshots.jsonl"
output_path = OUTPUT_DIR / f"merged_trades_{date_str}.jsonl"

print(f"🩺 Processing: {scrubbed_path}")
trades = load_jsonl(scrubbed_path)
btc = load_jsonl(btc_path)

fork_cache = {}
tv_cache = {}
enriched = []

for trade in trades:
    symbol = trade["symbol"].replace("USDT", "")
entry_ts = dateparser.parse(trade["entry_time"])
exit_ts = dateparser.parse(trade["exit_time"])

print(f""
n[SEARCH] Processing {symbol} @ {trade['entry_time']}")"

fork, tv = try_load_fork_tv(symbol, trade["entry_time"], fork_cache, tv_cache)

if not fork and tv:
    tv_ts = dateparser.parse(tv["ts_iso"])
tv_day = get_date_str(tv["ts_iso"])
print(f"↩  Trying fallback fork match from TV time: {tv['ts_iso']}")
if tv_day not in fork_cache:
    fork_cache[tv_day] = load_jsonl(FORK_DIR / tv_day / "fork_scores.jsonl")
fork = find_fork(symbol, tv_ts, fork_cache[tv_day])
if fork:
    print(f"[OK] Fallback fork matched at {fork['ts_iso']}")

btc_entry = find_btc(entry_ts, btc)
btc_exit = find_btc(exit_ts, btc)

record = {
"trade": trade,
"fork": fork,
"tv_kicker": tv,
"btc_context": {
"entry": btc_entry,
"exit": btc_exit
}
}

if tv and not fork:
    record["tv_screener_kick_applied"] = True

enriched.append(record)

save_jsonl(output_path, enriched)
print(f""
n[OK] Enriched output written to: {output_path}")"

# === CLI Entry ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
parser.add_argument("--date", required=True, help="Date to process (YYYY-MM-DD)")
args = parser.parse_args()
run_hail_mary(args.date)
