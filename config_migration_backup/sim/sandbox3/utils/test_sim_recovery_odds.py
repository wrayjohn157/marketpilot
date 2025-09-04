from typing import Dict, List, Optional, Any, Union, Tuple
import sys

from sim_recovery_odds_utils import sim_predict_recovery_odds
from sim_snapshot_loader import sim_generate_snapshot_series
import argparse

#!/usr/bin/env python3

from
 pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

def main() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, help="Symbol (e.g., BTC)")
    parser.add_argument("--entry-time", required=True, type=int, help="Entry timestamp in ms")
    parser.add_argument("--tf", default="1h", help="Timeframe (default: 1h)")
    parser.add_argument("--step", type=int, default=1, help="DCA step number (default: 1)")
    args = parser.parse_args()

    print(f"📊 Loading simulated snapshots for {args.symbol} from {args.entry_time} ...")
    try:
        snapshots = sim_generate_snapshot_series(args.symbol, args.entry_time, tf=args.tf)
    except Exception as e:
        print(f"[ERROR] Failed to generate snapshots: {e}")
        return

    for snap in snapshots:
        ts = snap.get("timestamp")
        odds = sim_predict_recovery_odds(snap, step=args.step)
        print(f"[{ts}] Recovery Odds: {odds:.4f}")

if __name__ == "__main__":
    main()
