#!/usr/bin/env python3
import asyncio
import websockets
import json
import time
import logging
from datetime import datetime
import pandas as pd
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

BASE_PATH = os.path.dirname(__file__)
FILTERED_FILE = os.path.join(BASE_PATH, "filtered_pairs.json")
KLINE_STORE = os.path.join(BASE_PATH, "klines")

os.makedirs(KLINE_STORE, exist_ok=True)

TIMEFRAME = "1m"
KLINE_LIMIT = 100

live_klines = {}

def save_kline_df(symbol, df):
    df.to_csv(os.path.join(KLINE_STORE, f"{symbol}.csv"))

async def handle_kline_stream(symbols):
    stream_url = f"wss://stream.binance.com:9443/stream?streams=" + "/".join([f"{sym.lower()}usdt@kline_{TIMEFRAME}" for sym in symbols])
    async with websockets.connect(stream_url) as websocket:
        logging.info("WebSocket connection established.")
        while True:
            try:
                msg = await websocket.recv()
                data = json.loads(msg)
                k = data["data"]["k"]

                if not k["x"]:  # Ignore if candle is not closed
                    continue

                symbol = k["s"].replace("USDT", "")
                kline_data = {
                    "timestamp": int(k["t"]),
                    "open": float(k["o"]),
                    "high": float(k["h"]),
                    "low": float(k["l"]),
                    "close": float(k["c"]),
                    "volume": float(k["v"])
                }

                if symbol not in live_klines:
                    live_klines[symbol] = []

                live_klines[symbol].append(kline_data)

                if len(live_klines[symbol]) > KLINE_LIMIT:
                    live_klines[symbol] = live_klines[symbol][-KLINE_LIMIT:]

                df = pd.DataFrame(live_klines[symbol])
                save_kline_df(symbol, df)

            except Exception as e:
                logging.error(f"Error in WebSocket stream: {e}")
                await asyncio.sleep(5)

def load_filtered_symbols():
    with open(FILTERED_FILE, "r") as f:
        return json.load(f)

def main():
    symbols = load_filtered_symbols()
    asyncio.run(handle_kline_stream(symbols))

if __name__ == "__main__":
    main()
