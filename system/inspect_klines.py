#!/usr/bin/env python3
import redis
import json
import sys

def main(symbol="GALA", timeframe="15m"):
    key = f"{symbol.upper()}_{timeframe}_klines"

    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    if not r.exists(key):
        print(f"❌ Redis key not found: {key}")
        return

    key_type = r.type(key)
    if key_type != "list":
        print(f"❌ Redis key is not a list (type={key_type}): {key}")
        return

    length = r.llen(key)
    if length < 2:
        print(f"❌ Not enough klines in {key} to compute change.")
        return

    first = json.loads(r.lindex(key, 0))
    last = json.loads(r.lindex(key, -1))

    open_price = float(first[1])
    close_price = float(last[4])
    change = abs((close_price - open_price) / open_price) * 100

    print(f"\n🔎 Inspecting {symbol.upper()} {timeframe} klines")
    print(f"Open  (first candle): {open_price}")
    print(f"Close (last candle):  {close_price}")
    print(f"Price change:         {change:.4f}%\n")

if __name__ == "__main__":
    args = sys.argv[1:]
    symbol = args[0] if len(args) > 0 else "GALA"
    timeframe = args[1] if len(args) > 1 else "15m"
    main(symbol, timeframe)
