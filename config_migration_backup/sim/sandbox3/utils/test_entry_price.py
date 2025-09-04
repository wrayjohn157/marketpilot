from typing import Dict, List, Optional, Any, Union, Tuple
import os
import pathlib
import sys

# test_entry_price.py

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from
 sim_entry_utils import sim_get_entry_price

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 test_entry_price.py SYMBOL ENTRY_TIME_MS TIMEFRAME")
        sys.exit(1)

    symbol = sys.argv[1]
    entry_time_ms = int(sys.argv[2])
    tf = sys.argv[3]

    price = sim_get_entry_price(symbol, entry_time_ms, tf)
    print(f"✅ Entry price for {symbol} at {entry_time_ms} ({tf}): {price}")
