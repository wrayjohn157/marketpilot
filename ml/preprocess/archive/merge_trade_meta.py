#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path

from config import get_path

# === Config Paths ===
ENRICHED_DIR = get_path("base") / "ml/datasets/enriched/2025-05-12"
TRADES_PATH = ENRICHED_DIR / "scrubbed_trades_fixed.jsonl"
TV_KICKER_PATH = Path(get_path("base") / "output/tv_history/2025-05-12/tv_kicker.jsonl")
OUTPUT_PATH = ENRICHED_DIR / "merged_trade_meta.jsonl"

MATCH_WINDOW_SECONDS = 1800  # 30 minutes


# === Load Functions ===
def load_jsonl(path):
    if not path.exists():
        print(f"⚠️ File not found: {path}")
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def parse_any_time(ts):
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str) and "T" in ts:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    return float(ts)


def normalize_symbol(sym):
    return sym.replace("USDT", "").upper()


# === Load data ===
trades = load_jsonl(TRADES_PATH)
tv_kicker = [x for x in load_jsonl(TV_KICKER_PATH) if x.get("pass")]
print(f"🔍 Loaded {len(trades)} trades and {len(tv_kicker)} tv kicker entries")

# === Merge logic ===
merged = []
matched = 0

for trade in trades:
    trade_sym = normalize_symbol(trade.get("symbol", ""))
    entry_ts = parse_any_time(trade.get("entry_time"))
    match = None
    min_delta = float("inf")

    for tv in tv_kicker:
        tv_sym = normalize_symbol(tv.get("symbol", ""))
        if tv_sym != trade_sym:
            continue
        tv_ts = parse_any_time(tv.get("timestamp") or tv.get("ts_iso"))
        delta = abs(tv_ts - entry_ts)
        if delta < min_delta:
            match = tv
            min_delta = delta

    if match and min_delta <= MATCH_WINDOW_SECONDS:
        trade["tv_boost"] = True
        trade["tv_kicker"] = match
        matched += 1
    else:
        trade["tv_boost"] = False
        print(
            f"❌ TV MISS  | {trade.get('symbol')} | Δt = {min_delta:.2f}s | Entry: {trade.get('entry_time')}"
        )

    merged.append(trade)

# === Save Output ===
with OUTPUT_PATH.open("w") as f:
    for row in merged:
        f.write(json.dumps(row) + "\n")

print(f"\n✅ Merged {matched} trades -> {OUTPUT_PATH}")
