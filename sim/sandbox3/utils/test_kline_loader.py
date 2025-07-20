# test_kline_loader.py
from sim_kline_loader import load_klines_across_days
import sys

if __name__ == "__main__":
    symbol = sys.argv[1]
    entry_time_ms = int(sys.argv[2])
    tf = sys.argv[3] if len(sys.argv) > 3 else "1h"

    klines = load_klines_across_days(symbol, tf, entry_time_ms)
    print(f"\n✅ Loaded {len(klines)} klines")
    if klines:
        print(f"⏱️ First TS: {klines[0][0]}, Last TS: {klines[-1][0]}")
