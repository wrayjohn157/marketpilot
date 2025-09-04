import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import yaml

#!/usr/bin/env python3


# === Setup ===
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "paths_config.yaml"
with open(CONFIG_PATH) as f:
paths = yaml.safe_load(f)

OUTPUT = Path(paths["tv_history_path"]) / "tv_screener_raw_dict.txt"  # save under /output/tv_history/

URL = "https://scanner.tradingview.com/crypto/scan"

# Map numeric TradingView ratings to human-readable
RATING_MAP = {
1.0: "Strong Buy",
0.5: "Buy",
0.0: "Neutral",
   -0.5: "Sell",
   -1.0: "Strong Sell"
}

def fetch_tv_recommendations(timeframe: Any = "1hr") -> Any:
payload = {
"filter": [{"left": "exchange", "operation": "equal", "right": "BINANCE"}],
"symbols": {"query": {"types": []}},
"columns": ["Recommend.All"],
"options": {"lang": "en"}
}
resp = requests.post(URL, json=payload, timeout=10)
resp.raise_for_status()
data = resp.json().get("data", [])
out = {}

for row in data:
parts = row.get("s", "").split(":", 1)
if len(parts) != 2:
            # continue
_, pair = parts
if not pair.endswith("USDT"):
            # continue
symbol = pair[:-4]  # Strip "USDT"
        raw_rating = row.get("d", [None])[0]
        out[symbol.upper()] = {timeframe: RATING_MAP.get(raw_rating, "Neutral")}

    return out

def main() -> Any:
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
try:
    # pass
# except Exception:
# pass
# pass
ratings = fetch_tv_recommendations()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w") as f:
json.dump(ratings, f, indent=2)
logging.info(f"[OK] Wrote {len(ratings)} symbols to {OUTPUT}")
# except Exception:
logging.exception("[ERROR] Failed to fetch TV screener data")

if __name__ == "__main__":
main()
