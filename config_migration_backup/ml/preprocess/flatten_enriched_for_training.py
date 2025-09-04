from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import json

import argparse

#!/usr/bin/env python3
from
 pathlib import Path

ENRICHED_ROOT = Path("/home/signal/market7/ml/datasets/enriched")
FLATTENED_ROOT = Path("/home/signal/market7/ml/datasets/flattened")
CLEANED_PREFIX = "cleaned_flattened_"

REQUIRED_TRADE_FIELDS = [
    "trade_id", "entry_time", "exit_time", "entry_price",
    "exit_price", "symbol", "pnl_pct", "safety_orders", "status"
]

def is_valid_entry(entry: Any) -> Any:
    trade = entry.get("trade")
    fork = entry.get("fork")

    if not trade or not fork:
        return False
    if not isinstance(fork.get("raw_indicators"), dict):
        return False
    for field in REQUIRED_TRADE_FIELDS:
        if field not in trade or trade[field] is None:
            return False
    if any(v is None for v in fork["raw_indicators"].values()):
        return False
    return True

def flatten_entry(entry: Any) -> Any:
    flat = {}

    trade = entry["trade"]
    fork = entry["fork"]
    indicators = fork["raw_indicators"]
    btc = entry.get("btc_context", {}).get("entry", {})
    tv = entry.get("tv_kicker", {})

    flat["trade_id"] = int(trade.get("trade_id"))
    flat["symbol"] = trade.get("symbol")
    flat["entry_time"] = trade.get("entry_time")
    flat["exit_time"] = trade.get("exit_time")
    flat["entry_price"] = trade.get("entry_price")
    flat["exit_price"] = trade.get("exit_price")
    flat["pnl_pct"] = trade.get("pnl_pct")
    flat["safety_orders"] = trade.get("safety_orders")
    flat["status"] = trade.get("status")
    flat["fork_score"] = fork.get("score")

    for k, v in indicators.items():
        flat[f"ind_{k}"] = v

    # Derived field: macd_lift = hist - prev
    macd_hist = indicators.get("macd_hist")
    macd_hist_prev = indicators.get("macd_hist_prev")
    if macd_hist is not None and macd_hist_prev is not None:
        flat["ind_macd_lift"] = macd_hist - macd_hist_prev

    for k, v in btc.items():
        if v is not None:
            flat[f"btc_{k}"] = v

    if tv:
        flat["tv_tag"] = tv.get("tv_tag")
        flat["tv_kicker"] = tv.get("tv_kicker")
        flat["tv_pass"] = tv.get("pass", False)

    return flat

def process_file(date_str: Any) -> Any:
    input_path = ENRICHED_ROOT / date_str / "enriched_data.jsonl"
    output_path = FLATTENED_ROOT / f"{CLEANED_PREFIX}{date_str}.jsonl"

    if not input_path.exists():
        print(f"❌ Missing: {input_path}")
        return 0

    with open(input_path, "r") as f:
        raw = [json.loads(line) for line in f if line.strip()]
    cleaned = [flatten_entry(e) for e in raw if is_valid_entry(e)]

    FLATTENED_ROOT.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for row in cleaned:
            f.write(json.dumps(row) + "\n")

    print(f"✅ {date_str}: Saved {len(cleaned)} rows → {output_path.name}")
    return len(cleaned)

def main() -> Any:
    parser = argparse.ArgumentParser(description="Flatten enriched_data.jsonl for ML training.")
    parser.add_argument("--date", help="Target date (YYYY-MM-DD), defaults to yesterday UTC")
    args = parser.parse_args()

    date_str = args.date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    process_file(date_str)

if __name__ == "__main__":
    main()
