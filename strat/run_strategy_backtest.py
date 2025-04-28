#!/usr/bin/env python3
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime

STRAT_PATH = Path("/home/signal/market6/live/strat/config")
FORK_HISTORY = Path("/home/signal/market6/output/fork_history")
OUTPUT_BASE = Path("/home/signal/market6/backtest/strategy_eval")
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

def load_strategy_config(name):
    path = STRAT_PATH / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Strategy config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)

def load_fork_scores():
    all_trades = []
    for folder in sorted(FORK_HISTORY.glob("*")):
        date_str = folder.name
        score_file = folder / "fork_scores.jsonl"
        if not score_file.exists():
            continue
        with open(score_file) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get("symbol") and obj.get("score") is not None:
                        obj["date"] = date_str
                        all_trades.append(obj)
                except:
                    continue
    return all_trades

def apply_strategy_filter(trades, config, start_date=None, end_date=None):
    min_score = config.get("min_score", 0.7)
    max_drawdown = config.get("max_drawdown", 10.0)
    max_tp1_shift = config.get("max_tp1_shift", 3.0)

    def date_in_range(d):
        if start_date and d < start_date:
            return False
        if end_date and d > end_date:
            return False
        return True

    filtered = []
    for t in trades:
        if not date_in_range(t.get("date", "")):
            continue
        if t.get("score", 0) < min_score:
            continue
        if t.get("tp1_shift", 0) > max_tp1_shift:
            continue
        if t.get("drawdown_pct", 0) > max_drawdown:
            continue
        filtered.append(t)
    return filtered

def summarize(filtered):
    by_date = {}
    for trade in filtered:
        date = trade.get("date")
        by_date.setdefault(date, []).append(trade)
    summary = {
        "total": len(filtered),
        "by_date": {d: len(v) for d, v in by_date.items()}
    }
    return summary

def save_summary(strategy_name, summary):
    out_path = OUTPUT_BASE / f"{strategy_name}_summary.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Saved: {out_path}")

def run(strategy_name, range_start=None, range_end=None):
    strategy = load_strategy_config(strategy_name)
    trades = load_fork_scores()
    filtered = apply_strategy_filter(trades, strategy, range_start, range_end)
    summary = summarize(filtered)
    save_summary(strategy_name, summary)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, required=True, help="Name of strategy YAML (without .yaml)")
    parser.add_argument("--range-start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--range-end", type=str, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    run(args.strategy, args.range_start, args.range_end)
