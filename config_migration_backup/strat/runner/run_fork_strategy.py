from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import sys

from config_loader import PATHS
from scorer.fork_scorer import score_fork
from utils.strategy_loader import load_strategy_config
import argparse

# /market7/strat/runner/run_fork_strategy.py

from
 pathlib import Path

# === Add /market7/strat and /market7/config to PYTHONPATH ===
sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[2] / "config"))

# === Dynamic paths from PATHS ===
FORK_INPUT_FILE = PATHS["fork_candidates"] #FORK_INPUT_FILE = PATHS["final_forked_trades"]
OUTPUT_FILE = PATHS["final_fork_rrr_trades"]
BACKTEST_CANDIDATES_FILE = PATHS["fork_backtest_candidates"]

def main(strategy_name: Any) -> Any:
    config = load_strategy_config(strategy_name)

    if not FORK_INPUT_FILE.exists():
        print(f"❌ Missing input: {FORK_INPUT_FILE}")
        return

    with open(FORK_INPUT_FILE) as f:
        symbols = json.load(f)

    results, candidates = [], []
    now_ts = int(datetime.utcnow().timestamp() * 1000)

    for sym, snapshot in symbols.items():
        indicators = snapshot.get("raw_indicators", {})
        result = score_fork(sym, now_ts, indicators, config)

        candidates.append({
            "symbol": sym,
            "score": result["score"],
            "timestamp": now_ts,
            "raw_indicators": indicators
        })

        if result["passed"]:
            results.append({
                "symbol": sym,
                "pair": f"{sym}_USDT",
                "score": result["score"],
                "meta": result["score_components"],
                "score_hash": "_".join(f"{k}:{v}" for k, v in result["score_components"].items()),
                "timestamp": now_ts
            })

        verdict = "✅" if result["passed"] else "❌"
        print(f"{verdict} {sym} | Score: {result['score']:.3f}")

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
