from typing import Dict, List, Optional, Any, Union, Tuple
import sys

from utils.sim_trade_health_evaluator import evaluate_trade_health
import argparse

from
 pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
sys.path.append(str(Path(__file__).resolve().parent / "utils"))

def main() -> Any:
    parser = argparse.ArgumentParser(description="Test SIM Trade Health Evaluator")
    parser.add_argument("--entry_score", type=float, default=0.7)
    parser.add_argument("--current_score", type=float, default=0.4)
    parser.add_argument("--recovery_odds", type=float, default=0.8)
    parser.add_argument("--confidence_score", type=float, default=0.75)
    parser.add_argument("--safu_score", type=float, default=0.65)
    parser.add_argument("--rsi", type=float, default=50)
    parser.add_argument("--macd_histogram", type=float, default=0.001)
    parser.add_argument("--adx", type=float, default=22)
    args = parser.parse_args()

    trade = {
        "entry_score": args.entry_score,
        "current_score": args.current_score,
        "recovery_odds": args.recovery_odds,
        "confidence_score": args.confidence_score,
        "safu_score": args.safu_score,
        "rsi": args.rsi,
        "macd_histogram": args.macd_histogram,
        "adx": args.adx,
    }

    result = evaluate_trade_health(trade)
    print(f"🩺 Trade Health: {result['health_status']} ({result['health_score']})")

if __name__ == "__main__":
    main()
