#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import argparse
from datetime import datetime
from utils.sim_confidence_utils import inject_snapshot, predict_sim_confidence_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, help="Symbol name (e.g., MAGIC)")
    parser.add_argument("--entry-time", type=int, required=True, help="Entry timestamp in ms")
    parser.add_argument("--step", type=int, default=1, help="Step number (e.g., 2)")
    args = parser.parse_args()

    print(f"📊 Generating snapshot for {args.symbol} at {args.entry_time} (step {args.step})...")

    try:
        snapshot = inject_snapshot(args.symbol, args.entry_time, args.step)
        ts = snapshot.get("timestamp")
        confidence = predict_sim_confidence_score(snapshot)
        print(f"[{ts}] Confidence Score: {confidence:.4f}")
    except Exception as e:
        print(f"❌ Error generating or scoring snapshot: {e}")

if __name__ == "__main__":
    main()
