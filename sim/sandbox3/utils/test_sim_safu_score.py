#!/usr/bin/env python3

# test_sim_safu_score.py
import argparse
import time
from utils.sim_safu_utils import sim_get_safu_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ts", type=int, help="Timestamp in ms", required=True)
    parser.add_argument("--entry", type=float, help="Entry price", required=True)
    parser.add_argument("--current", type=float, help="Current price", required=True)
    parser.add_argument("--symbol", type=str, default="BTC")
    parser.add_argument("--tf", type=str, default="1h")
    args = parser.parse_args()

    score = sim_get_safu_score(
        symbol=args.symbol,
        entry_price=args.entry,
        current_price=args.current,
        ts_ms=args.ts,
        tf=args.tf
    )

    print(f"🧠 SAFU Score for {args.symbol} at {args.ts} (tf={args.tf}): {score}")

if __name__ == "__main__":
    main()
