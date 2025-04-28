import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

FORK_HISTORY_BASE = Path("/home/signal/market6/output/fork_history")

def load_scores(date_str):
    path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

def dry_run_simulate(start_date, end_date, config):
    current = start_date
    all_rows = []

    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        rows = load_scores(date_str)
        all_rows.extend(rows)
        current += timedelta(days=1)

    results = []
    for row in all_rows:
        score = row.get("score", 0)
        rsi = row.get("raw_indicators", {}).get("rsi", 0)
        passed = row.get("passed", False)
        tp1_shift = row.get("score_components", {}).get("mean_reversion_score", 1.0)

        if score < config.get("min_score", 0.7):
            continue
        if rsi < config.get("min_rsi", 30):
            continue
        if config.get("require_passed", True) and not passed:
            continue
        if tp1_shift > config.get("max_tp1_shift", 3.0):
            continue

        results.append({
            "symbol": row.get("symbol"),
            "score": round(score, 4),
            "rsi": round(rsi, 2),
            "passed": passed,
            "tp1_shift": round(tp1_shift, 3),
        })

    return results

def print_summary(trades):
    print("\n📋 Dry-Run Simulation Results:")
    if not trades:
        print("No trades passed filters.")
        return
    df = pd.DataFrame(trades)
    print(df.to_string(index=False))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--range-start", type=str, required=True)
    parser.add_argument("--range-end", type=str, required=True)
    parser.add_argument("--config", type=str, default=None)
    return parser.parse_args()

def main():
    args = parse_args()
    start_date = datetime.strptime(args.range_start, "%Y-%m-%d")
    end_date = datetime.strptime(args.range_end, "%Y-%m-%d")

    config = {
        "min_score": 0.73,
        "min_rsi": 30,
        "max_tp1_shift": 3.0,
        "require_passed": True
    }
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config.update(json.load(f))

    results = dry_run_simulate(start_date, end_date, config)
    print_summary(results)

if __name__ == "__main__":
    main()
