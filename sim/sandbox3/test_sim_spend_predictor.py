from typing import Dict, List, Optional, Any, Union, Tuple
import json

from utils.sim_confidence_utils import inject_snapshot
import argparse

#!/usr/bin/env python3
from
 utils.sim_spend_predictor import predict_sim_spend_volume, adjust_volume

parser = argparse.ArgumentParser(description="Test spend prediction using live-style snapshot features.")
parser.add_argument("--symbol", type=str, required=True, help="Symbol to simulate (e.g., LTC).")
parser.add_argument("--entry-time", type=int, required=True, help="Entry timestamp in ms.")
parser.add_argument("--step", type=int, default=1, help="Snapshot step.")
parser.add_argument("--spent", type=float, default=200.0, help="Already spent USDT.")
parser.add_argument("--budget", type=float, default=2000.0, help="Max trade budget.")
parser.add_argument("--dd", type=float, default=5.0, help="Drawdown pct.")
parser.add_argument("--tp1", type=float, default=8.0, help="TP1 shift pct.")

args = parser.parse_args()

snapshot = inject_snapshot(symbol=args.symbol, entry_time=args.entry_time, step=args.step)
feature_dict = snapshot.get("features", {})

pred = predict_sim_spend_volume(feature_dict)
adj = adjust_volume(pred, already_spent=args.spent, max_budget=args.budget, drawdown_pct=args.dd, tp1_shift_pct=args.tp1)

print(f"📈 Predicted spend volume: {pred:.2f}")
print(f"✅ Adjusted volume (based on budget/DD/TP1): {adj:.2f}")
