#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparser

# === Paths ===
PROJECT_ROOT = Path("/home/signal/market7").resolve()
ML_BASE = PROJECT_ROOT / "ml"
DCA_LOG_PATH = PROJECT_ROOT / "dca/logs"
SNAPSHOT_PATH = ML_BASE / "datasets/recovery_snapshots"
OUTPUT_PATH = ML_BASE / "datasets/recovery_training"

# === Fields required by the confidence model trainer
REQUIRED_FIELDS = [
    "deal_id", "step", "entry_score", "current_score", "tp1_shift", "safu_score",
    "rsi", "macd_histogram", "adx", "macd_lift", "rsi_slope", "drawdown_pct",
    "snapshot_score_trend", "snapshot_rsi_trend",
    "snapshot_max_drawdown", "snapshot_min_score", "snapshot_min_rsi",
    "snapshot_time_to_max_drawdown_min", "recovery_odds", "confidence_score_ml"
]

def load_jsonl(path: Path):
    """Load JSONL file into a list of dicts."""
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def extract_trends(snapshots: list):
    """Extract trend and extreme features from snapshot list."""
    times, dd_vals, score_vals, rsi_vals = [], [], [], []
    for s in snapshots:
        ts = s.get("timestamp")
        try:
            dt = dtparser.parse(ts)
        except:
            continue
        dd = s.get("drawdown_pct")
        sc = s.get("current_score")
        rsi = s.get("rsi")
        if dd is None or sc is None or rsi is None:
            continue
        times.append(dt)
        dd_vals.append(dd)
        score_vals.append(sc)
        rsi_vals.append(rsi)

    if not times:
        return {
            "snapshot_score_trend": 0.0,
            "snapshot_rsi_trend": 0.0,
            "snapshot_max_drawdown": 0.0,
            "snapshot_min_score": 0.0,
            "snapshot_min_rsi": 0.0,
            "snapshot_time_to_max_drawdown_min": 0.0
        }

    if len(times) == 1:
        return {
            "snapshot_score_trend": 0.0,
            "snapshot_rsi_trend": 0.0,
            "snapshot_max_drawdown": dd_vals[0],
            "snapshot_min_score": score_vals[0],
            "snapshot_min_rsi": rsi_vals[0],
            "snapshot_time_to_max_drawdown_min": 0.0
        }

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

def compute_drawdown_pct(current: float, entry: float):
    """Compute drawdown percentage from entry price to current price."""
    try:
        return ((entry - current) / entry) * 100
    except:
        return None

def main(date_str: str):
    log_file = DCA_LOG_PATH / date_str / "dca_log.jsonl"
    out_file = OUTPUT_PATH / f"{date_str}_confscored.jsonl"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    logs = load_jsonl(log_file)
    saved = 0
    skipped = 0

    with open(out_file, "w") as fout:
        for entry in logs:
            if entry.get("decision") != "fired":
                continue

            deal_id = entry.get("deal_id")
            step = entry.get("step")
            short = entry.get("symbol", "").replace("USDT_", "")

            # Load snapshots
            snap_file = SNAPSHOT_PATH / f"{short}_{deal_id}.jsonl"
            snaps = load_jsonl(snap_file)
            if not snaps:
                print(f"⚠️ Missing snapshots for {short} {deal_id}")
                skipped += 1
                continue

            last = snaps[-1]
            current_price = last.get("current_price", entry.get("current_price"))
            entry_price = last.get("avg_entry_price", entry.get("avg_entry_price"))
            drawdown = compute_drawdown_pct(current_price, entry_price)

            record = {
                "deal_id": deal_id,
                "step": step,
                "entry_score": entry.get("entry_score"),
                "current_score": entry.get("current_score"),
                "tp1_shift": entry.get("tp1_shift"),
                "safu_score": entry.get("safu_score"),
                "rsi": last.get("rsi"),
                "macd_histogram": last.get("macd_histogram"),
                "adx": last.get("adx"),
                "macd_lift": last.get("macd_lift"),
                "rsi_slope": last.get("rsi_slope"),
                "drawdown_pct": drawdown,
                "recovery_odds": entry.get("recovery_odds"),
                "confidence_score_ml": entry.get("confidence_score")
            }

            trends = extract_trends(snaps)
            record.update(trends)

            missing = [f for f in REQUIRED_FIELDS if record.get(f) is None]
            if missing:
                skipped += 1
                continue

            fout.write(json.dumps(record) + "\n")
            saved += 1

    print(f"✅ Saved {saved} rows to {out_file}")
    print(f"⚠️ Skipped {skipped} rows due to missing fields")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build confidence ML dataset.")
    parser.add_argument("date", help="YYYY-MM-DD format")
    args = parser.parse_args()
    main(args.date)
