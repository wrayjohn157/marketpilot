# run_fork_strategy.py
import argparse
import json
from pathlib import Path
from datetime import datetime
from live.strat.strategy_loader import load_strategy_config
from indicators.modules.fork_score_module import score_fork_with_config

FORK_INPUT_FILE = Path("/home/signal/market6/output/final_forked_trades.json")
OUTPUT_FILE = Path("/home/signal/market6/output/final_fork_rrr_trades.json")
BACKTEST_CANDIDATES_FILE = Path("/home/signal/market6/output/fork_backtest_candidates.json")


def main(strategy_name):
    config = load_strategy_config(strategy_name)
    if not FORK_INPUT_FILE.exists():
        print(f"❌ Missing {FORK_INPUT_FILE}")
        return

    with open(FORK_INPUT_FILE) as f:
        symbols = json.load(f)

    results, candidates = [], []
    now_ts = int(datetime.utcnow().timestamp() * 1000)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    for sym in symbols:
        score, passed, subs, mult, raw_indicators = score_fork_with_config(sym, config)

        entry = {
            "symbol": sym.upper(),
            "score": score,
            "timestamp": now_ts,
            "score_hash": "_".join([f"{k}:{subs[k]}" for k in subs]),
            "score_components": subs,
            "btc_multiplier": mult,
            "entry_price": raw_indicators.get("price", 0),
            "raw_indicators": raw_indicators,
            "passed": passed,
            "source": strategy_name
        }
        candidates.append({k: entry[k] for k in ("symbol", "score", "timestamp", "raw_indicators")})

        if passed:
            results.append({
                "symbol": sym.upper(),
                "pair": f"{sym.upper()}_USDT",
                "score": score,
                "meta": subs,
                "score_hash": entry["score_hash"],
                "timestamp": now_ts
            })

        verdict = "✅" if passed else "❌"
        print(f"{verdict} {sym.upper()} | Score: {score:.3f} | Mult: {mult:.2f}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    with open(BACKTEST_CANDIDATES_FILE, "w") as f:
        json.dump(candidates, f, indent=2)

    print(f"📂 Saved {len(results)} trades to {OUTPUT_FILE}")
    print(f"📊 Backtest candidates saved to {BACKTEST_CANDIDATES_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, required=True, help="Name of strategy YAML (without .yaml)")
    args = parser.parse_args()
    main(args.strategy)
