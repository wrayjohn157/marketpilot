#!/usr/bin/env python3
import requests
import json
import logging
from pathlib import Path

# where tv_screener_score.py expects it
OUTPUT = Path("/home/signal/market6/output/tv_screener_raw_dict.txt")

# TradingView’s crypto scanner endpoint
URL = "https://scanner.tradingview.com/crypto/scan"

# map their numeric ratings → human strings
RATING_MAP = {
    1.0: "Strong Buy",
    0.5: "Buy",
    0.0: "Neutral",
   -0.5: "Sell",
   -1.0: "Strong Sell"
}

def fetch(timeframe="1hr"):
    payload = {
        "filter": [
            { "left": "exchange", "operation": "equal", "right": "BINANCE" }
        ],
        "symbols": {
            "query": { "types": [] }
        },
        "columns": ["Recommend.All"],
        "options": { "lang": "en" }
    }

    resp = requests.post(URL, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    out = {}

    for row in data:
        # row["s"] looks like "BINANCE:BTCUSDT"
        exchange_and_pair = row.get("s", "")
        parts = exchange_and_pair.split(":", 1)
        if len(parts) != 2:
            continue
        _, pair = parts
        if not pair.endswith("USDT"):
            continue
        sym = pair[:-4]  # strip "USDT" → "BTC", "DOGE", etc.

        raw_rating = row.get("d", [None])[0]
        human = RATING_MAP.get(raw_rating, "Neutral")
        out[sym] = {timeframe: human}

    return out

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    try:
        d = fetch()
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT, "w") as f:
            json.dump(d, f, indent=2)
        logging.info(f"Wrote {len(d)} symbols to {OUTPUT}")
    except Exception:
        logging.exception("Failed to fetch TV screener data")

if __name__ == "__main__":
    main()
