# hyperopt_sim_runner.py
import argparse
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

STRATEGY_DIR = Path("/home/signal/market6/live/strat/config")
BACKTEST_SUMMARY_BASE = Path("/home/signal/market6/backtest/data/summary")


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def simulate(strategy_name, date):
    env = os.environ.copy()
    env["STRATEGY_NAME"] = strategy_name
    print(f"\n📆 Running strategy '{strategy_name}' for {date}...")
    result = subprocess.run(["python3", "fork_score_filter.py"], env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed for {strategy_name} on {date}: {result.stderr.strip()}")
        return None

    summary_file = BACKTEST_SUMMARY_BASE / f"{date}_summary.json"
    if summary_file.exists():
        try:
            import json
            with open(summary_file) as f:
                return json.load(f)
        except:
            return None
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--range-start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--range-end", type=str, required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start_date = datetime.strptime(args.range_start, "%Y-%m-%d").date()
    end_date = datetime.strptime(args.range_end, "%Y-%m-%d").date()

    strategy_files = sorted(STRATEGY_DIR.glob("*.yaml"))
    strategies = [f.stem for f in strategy_files]
    print(f"🧪 Testing {len(strategies)} strategies from {start_date} to {end_date}...")

    results = {}
    for strategy in strategies:
        scores = []
        for day in daterange(start_date, end_date):
            day_str = day.strftime("%Y-%m-%d")
            sim_result = simulate(strategy, day_str)
            if sim_result:
                tp1 = sim_result.get("tp1_hit_rate", 0)
                dd = sim_result.get("avg_drawdown_pct", 0)
                scores.append((tp1, dd))

        if scores:
            avg_tp1 = sum(t[0] for t in scores) / len(scores)
            avg_dd = sum(t[1] for t in scores) / len(scores)
            results[strategy] = {"avg_tp1": round(avg_tp1, 2), "avg_drawdown": round(avg_dd, 2)}

    print("\n📊 Strategy Comparison Results:")
    for strat, vals in sorted(results.items(), key=lambda x: -x[1]["avg_tp1"]):
        print(f"• {strat:25} | TP1: {vals['avg_tp1']:.2f}% | Drawdown: {vals['avg_drawdown']:.2f}%")


if __name__ == "__main__":
    main()
