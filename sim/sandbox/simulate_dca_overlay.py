from typing import Dict, List, Optional, Any, Union, Tuple
import json

from modules.sim_core_engine import run_dca_simulation, load_config
from sim.sandbox.utils.trade_utils import build_mock_trade
import argparse

#!/usr/bin/env python3

from
 pathlib import Path

def main() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, help="Symbol (e.g., BTCUSDT)")
    parser.add_argument(
        "--entry_time", type=int, required=True, help="Entry timestamp in ms"
    )
    parser.add_argument("--tf", default="1h", help="Timeframe (default: 1h)")
    parser.add_argument("--config", type=str, help="Optional path to DCA config YAML")
    args = parser.parse_args()

    # Build a mock trade
    trade = build_mock_trade(symbol=args.symbol, entry_time=args.entry_time, tf=args.tf)
    if not trade:
        print("[ERROR] Failed to build trade input.")
        return

    # Load DCA config
    config = load_config(path=Path(args.config)) if args.config else load_config()

    # Run full DCA simulation across all bars
    result = run_dca_simulation(
        symbol=args.symbol,
        entry_time=args.entry_time,
        tf=args.tf,
        config_path=args.config
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
