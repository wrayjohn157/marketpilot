from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

from dateutil import parser as dtparser
import argparse

#!/usr/bin/env python3
from
 pathlib import Path

# === Paths ===
PROJECT_ROOT = Path("/home/signal/market7").resolve()
FLATTENED_PATH = PROJECT_ROOT / "ml/datasets/flattened"
DCA_LOG_BASE = PROJECT_ROOT / "dca/logs"
SNAPSHOT_PATH = PROJECT_ROOT / "ml/datasets/recovery_snapshots"
OUTPUT_FILE = PROJECT_ROOT / "ml/datasets/unified/master_ml_dataset.jsonl"

# === Helpers ===
def load_jsonl(path: Path):
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def extract_snapshot_meta(snapshots: Any) -> Any:
    times, dd_vals, score_vals, rsi_vals = [], [], [], []
    for snap in snapshots:
        ts = snap.get("timestamp")
        try:
            dt = dtparser.parse(ts)
        except:
            continue
        dd = snap.get("drawdown_pct")
        sc = snap.get("current_score")
        rsi = snap.get("rsi")
        if dd is None or sc is None or rsi is None:
            continue
        times.append(dt)
        dd_vals.append(dd)
        score_vals.append(sc)
        rsi_vals.append(rsi)

    if not times:
        return {}

    score_trend = score_vals[-1] - score_vals[0]
    rsi_trend = rsi_vals[-1] - rsi_vals[0]
    max_dd = max(dd_vals)
    min_score = min(score_vals)
    min_rsi = min(rsi_vals)
    try:
        idx_max = dd_vals.index(max_dd)
        time_to_max = (times[idx_max] - times[0]).total_seconds() / 60.0
    except:
        time_to_max = 0.0

    return {
        "snapshot_score_trend": score_trend,
        "snapshot_rsi_trend": rsi_trend,
        "snapshot_max_drawdown": max_dd,
        "snapshot_min_score": min_score,
        "snapshot_min_rsi": min_rsi,
        "snapshot_time_to_max_drawdown_min": time_to_max
    }

# === Unified Builder ===
def build_unified_dataset() -> Any:
    total_written = 0
    total_skipped = 0

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as fout:
        for flat_file in sorted(FLATTENED_PATH.glob("cleaned_flattened_*.jsonl")):
            date_str = flat_file.stem.replace("cleaned_flattened_", "")
            dca_file = DCA_LOG_BASE / date_str / "dca_log.jsonl"
            flattened = load_jsonl(flat_file)
            dca_log = load_jsonl(dca_file)

            flattened_map = {
                e["trade_id"]: e
                for e in flattened
                if "trade_id" in e
            }

            for dca in dca_log:
                if dca.get("decision") != "fired":
                    continue

                indicators = dca.get("indicators", {})
                if not indicators:
                    total_skipped += 1
                    continue

                deal_id = dca.get("deal_id")
                symbol = dca.get("symbol", "").replace("USDT_", "")
                trade_id = int(deal_id) if deal_id else None
                enriched_entry = flattened_map.get(trade_id)

                if not enriched_entry:
                    total_skipped += 1
                    continue

                snapshot_file = SNAPSHOT_PATH / f"{symbol}_{deal_id}.jsonl"
                snapshots = load_jsonl(snapshot_file)
                meta = extract_snapshot_meta(snapshots) if snapshots else {}

                row = {
                    "deal_id": deal_id,
                    "step": dca.get("step"),
                    "entry_score": dca.get("entry_score"),
                    "current_score": dca.get("current_score"),
                    "tp1_shift": dca.get("tp1_shift"),
                    "safu_score": dca.get("safu_score"),
                    "rsi": indicators.get("rsi"),
                    "macd_histogram": indicators.get("macd_histogram"),
                    "adx": indicators.get("adx"),
                    "macd_lift": indicators.get("macd_lift"),
                    "rsi_slope": indicators.get("rsi_slope"),
                    "drawdown_pct": indicators.get("drawdown_pct"),
                    "recovery_odds": dca.get("recovery_odds"),
                    "confidence_score": dca.get("confidence_score"),
                    "zombie_tagged": dca.get("zombie_tagged", False),
                    "btc_rsi": enriched_entry.get("btc_rsi"),
                    "btc_macd_histogram": enriched_entry.get("btc_macd_histogram"),
                    "btc_adx": enriched_entry.get("btc_adx"),
                    "btc_status": dca.get("btc_status", "UNKNOWN"),
                    "volume_sent": dca.get("volume_sent"),
                    "recovery_label": 1 if enriched_entry.get("status") == "passed" else 0,
                    "safu_good_but_zombie": enriched_entry.get("safu_good_but_zombie", False),
                    **meta
                }

                fout.write(json.dumps(row) + "\n")
                total_written += 1

            print(f"✅ {date_str}: {len(dca_log)} DCA logs checked → {len(flattened_map)} flattened entries")

    print(f"\n📦 Done! Total rows written: {total_written}")
    print(f"⚠️  Total skipped due to unmatched trade_id or missing indicators: {total_skipped}")

# === CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Required to confirm full run")
    args = parser.parse_args()

    if args.all:
        build_unified_dataset()
    else:
        print("❌ Please pass --all to run the full unified dataset builder")
