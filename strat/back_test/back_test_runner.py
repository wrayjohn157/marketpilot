import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from statistics import mean
from live.strat.strategy_loader import load_strategy_config

HISTORY_PATH = Path("/home/signal/market6/output/fork_history")


def load_all_scores(start_date, end_date):
    current = start_date
    all_entries = []
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        file_path = HISTORY_PATH / date_str / "fork_scores.jsonl"
        if file_path.exists():
            with open(file_path) as f:
                for line in f:
                    try:
                        all_entries.append(json.loads(line))
                    except:
                        continue
        current += timedelta(days=1)
    return all_entries


def apply_strategy(entries, strat):
    min_score = strat.get("min_score", 0.7)
    min_rsi = strat.get("min_rsi", 40)
    max_tp1 = strat.get("max_tp1_shift", 3.0)
    results = []
    for e in entries:
        score = e.get("score", 0.0)
        rsi = e.get("raw_indicators", {}).get("rsi", 0.0)
        price = e.get("raw_indicators", {}).get("price", 0.0)
        atr = e.get("raw_indicators", {}).get("atr", 0.01)
        tp1_shift = round(((1.015 * price - price) / price) * 100, 2) if price else None
        passed = (
            score >= min_score and
            rsi >= min_rsi and
            tp1_shift is not None and tp1_shift <= max_tp1
        )
        e["tp1_shift"] = tp1_shift
        e["strategy_passed"] = passed
        e["strategy_min_score"] = min_score
        e["strategy_min_rsi"] = min_rsi
        e["strategy_max_tp1"] = max_tp1
        results.append(e)
    return results


def summarize(results):
    passed = [r for r in results if r.get("strategy_passed")]
    failed = [r for r in results if not r.get("strategy_passed")]
    avg_score = mean(r["score"] for r in results if "score" in r)
    avg_rsi = mean(r["raw_indicators"]["rsi"] for r in results if r.get("raw_indicators", {}).get("rsi") is not None)
    return {
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "avg_score": round(avg_score, 4),
        "avg_rsi": round(avg_rsi, 2),
        "pass_rate": round(100 * len(passed) / max(len(results), 1), 2)
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, required=True)
    parser.add_argument("--range-start", type=str, required=True)
    parser.add_argument("--range-end", type=str, required=True)
    args = parser.parse_args()

    strategy = load_strategy_config(args.strategy)
    start_date = datetime.strptime(args.range_start, "%Y-%m-%d")
    end_date = datetime.strptime(args.range_end, "%Y-%m-%d")

    print(f"📂 Loading data from {args.range_start} to {args.range_end}...")
    entries = load_all_scores(start_date, end_date)
    print(f"🔍 Evaluating {len(entries)} entries using strategy: {args.strategy}")

    results = apply_strategy(entries, strategy)
    summary = summarize(results)
    print(json.dumps(summary, indent=2))

    print("\n🔬 Sample failed reasons:")
    for r in results[:10]:
        if not r.get("strategy_passed"):
            print(f"❌ {r['symbol']} | Score: {r['score']} | RSI: {r['raw_indicators'].get('rsi')} | TP1 Shift: {r.get('tp1_shift')}")


if __name__ == "__main__":
    main()
