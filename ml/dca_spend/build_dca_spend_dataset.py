from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os
import sys

from dateutil import parser as dtparser
import argparse
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


#!/usr/bin/env python3
from
 datetime import datetime

# === Use dynamic path loader ===
sys.path.append("/home/signal/market7")

# === Helpers ===
def load_jsonl(path: Any) -> Any:
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def index_by_deal_id(rows: Any) -> Any:
    return {r["deal_id"]: r for r in rows if "deal_id" in r}

def load_btc_context(date_str: Any) -> Any:
    path = get_path("btc_logs") / date_str / "btc_snapshots.jsonl"
    if not path.exists():
        return [], []
    snapshots = load_jsonl(path)
    timestamps = []
    for x in snapshots:
        ts = x.get("timestamp")
        try:
            dt = datetime.utcfromtimestamp(ts / 1000 if ts > 1e10 else ts) if isinstance(ts, (int, float)) else datetime.fromisoformat(ts)
            x["__dt"] = dt
            timestamps.append(dt)
        except:
            continue
    return snapshots, timestamps

def find_closest_btc_snapshot(ts: Any, btc_snapshots: Any) -> Any:
    if not btc_snapshots:
        return {}
    delta = lambda snap: abs((snap["__dt"] - ts).total_seconds())
    closest = min(btc_snapshots, key=delta)
    return {
        "btc_rsi": closest.get("rsi"),
        "btc_macd_histogram": closest.get("macd_histogram"),
        "btc_adx": closest.get("adx"),
        "btc_status": closest.get("market_condition"), #"btc_status": closest.get("status"),
    }

def load_latest_snapshot(symbol: Any, deal_id: Any) -> Any:
    path = PATHS["recovery_snapshots"] / f"{symbol}_{deal_id}.jsonl"
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            lines = f.readlines()
            if not lines:
                return {}
            return json.loads(lines[-1])
    except:
        return {}

# === Main logic ===
def main(date_str: Any) -> Any:
    dca_path = PATHS["dca_log"] / date_str / "dca_log.jsonl"
    enriched_path = PATHS["enriched"] / date_str / "enriched_data.jsonl"
    out_path = PATHS["dca_spend"] / f"{date_str}.jsonl" #out_path = PATHS["ml_dataset"] / "dca_spend" / f"{date_str}.jsonl"

    if not dca_path.exists() or not enriched_path.exists():
        print("Missing required input file(s)")
        return

    dca_logs = load_jsonl(dca_path)
    enriched_logs = index_by_deal_id(load_jsonl(enriched_path))
    fired_steps = load_jsonl(PATHS["dca_tracking"])
    fired_lookup = {(x["deal_id"], x["step"]): x for x in fired_steps}
    btc_snapshots, _ = load_btc_context(date_str)

    rows = []
    for log in dca_logs:
        if log.get("decision") != "fired" or log.get("volume_sent") is None:
            continue

        deal_id = log.get("deal_id")
        step = log.get("step")
        enriched = enriched_logs.get(deal_id, {})
        timestamp = dtparser.parse(log["timestamp"])
        btc_context = find_closest_btc_snapshot(timestamp, btc_snapshots)

        symbol = log.get("symbol")
        snapshot = load_latest_snapshot(symbol.replace("USDT_", ""), deal_id)

        def fallback(key):
            return log.get("indicators", {}).get(key) or snapshot.get(key)

        row = {
            "deal_id": deal_id,
            "symbol": symbol,
            "step": step,
            "timestamp": log.get("timestamp"),
            "entry_score": log.get("entry_score"),
            "current_score": log.get("current_score"),
            "drawdown_pct": fallback("drawdown_pct"),
            "safu_score": log.get("safu_score"),
            "macd_lift": fallback("macd_lift"),
            "rsi": fallback("rsi"),
            "rsi_slope": fallback("rsi_slope"),
            "adx": fallback("adx"),
            "tp1_shift": log.get("tp1_shift"),
            "recovery_odds": log.get("recovery_odds"),
            "confidence_score": log.get("confidence_score"),
            "volume_sent": log.get("volume_sent"),
            "zombie_tagged": enriched.get("safu_good_but_zombie", False),
        }
        row.update(btc_context)
        rows.append(row)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    print(f"✅ Saved {len(rows)} rows to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()
    main(args.date)
