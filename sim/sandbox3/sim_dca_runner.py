import sys
from pathlib import Path

# Ensure local modules can be imported
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "core"))
sys.path.append(str(BASE_DIR / "utils"))

import argparse
import yaml
import json
import os
from datetime import datetime

from sim_dca_engine import simulate_dca_engine
from sim_kline_loader import load_klines_for_symbol
from sim_entry_utils import get_entry_price_for_kline

def load_yaml_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, help="Symbol like LTC")
    parser.add_argument("--entry_time", type=int, required=True, help="Entry time in ms")
    parser.add_argument("--tf", default="1h", help="Timeframe like 1h")
    args = parser.parse_args()

    config_path = Path("/home/signal/market7/sim/config/dca_config.yaml")
    config = load_yaml_config(config_path)

    klines = load_klines_for_symbol(args.symbol, args.entry_time, args.tf)
    if not klines:
        print(f"[ERROR] No klines found for {args.symbol} at {args.entry_time}")
        return

    entry_price = get_entry_price_for_kline(klines, args.entry_time)
    if not entry_price:
        print(f"[ERROR] Entry price could not be determined")
        return

    results = simulate_dca_engine(
        klines=klines,
        entry_price=entry_price,
        entry_time=args.entry_time,
        symbol=args.symbol,
        tf=args.tf,
        config=config,
    )

    print(json.dumps(results, indent=2))

    # Save results to sim_output/<symbol>/ folder
    output_dir = output_dir = Path("sim_output") / args.symbol.upper()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.utcfromtimestamp(args.entry_time / 1000).strftime("%Y-%m-%dT%H%M%S")
    output_file = output_dir / f"{args.symbol}_{args.tf}_{timestamp_str}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[INFO] Saved simulation results to {output_file}")

if __name__ == "__main__":
    main()
