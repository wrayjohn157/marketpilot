#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from config import get_path

# [OK] Binance API Endpoint
BINANCE_API_URL = "https://api.binance.com/api/v3/exchangeInfo"

# [OK] List of Stablecoins & Fiat to Exclude
EXCLUDE_TOKENS = {
"USDT", "BUSD", "TUSD", "USDC", "DAI", "EUR", "GBP", "BRL",
"TRY", "AUD", "JPY", "RUB", "IDRT", "NGN", "ZAR", "UAH", "KES"
}

# [OK] Output path
OUTPUT_DIR = get_path("base") / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "binance_symbols.json"

# [OK] Fetch Tradable USDT Pairs from Binance
def fetch_usdt_pairs() -> Any:
    response = requests.get(BINANCE_API_URL, timeout=10)
data = response.json()
tradable_pairs = []

for symbol_info in data["symbols"]:
    symbol = symbol_info["symbol"]
base_asset = symbol_info["baseAsset"]
quote_asset = symbol_info["quoteAsset"]
status = symbol_info["status"]

if quote_asset == "USDT" and base_asset not in EXCLUDE_TOKENS and status == "TRADING":
    tradable_pairs.append(base_asset)

    return tradable_pairs

# [OK] Save Tradable Pairs to JSON
def save_pairs_to_json(pairs: Any) -> Any:
    with open(OUTPUT_FILE, "w") as f:
        json.dump(sorted(pairs), f, indent=4)
print(f""
n[FOLDER] Tradable pairs saved to {OUTPUT_FILE}")"

# [OK] Run Script
if __name__ == "__main__":
    print(""
n[INFO] Fetching tradable USDT pairs from Binance...\
n")"
tradable_symbols = fetch_usdt_pairs()
print(f"[OK] Found {len(tradable_symbols)} tradable pairs."
n")"

save_pairs_to_json(tradable_symbols)
