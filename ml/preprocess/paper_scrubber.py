import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

#!/usr/bin/env python3



# === Updated Dynamic Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/marketpilot
RAW_DIR = PROJECT_ROOT / "ml/datasets/raw_paper"
SCRUBBED_DIR = PROJECT_ROOT / "ml/datasets/scrubbed_paper"

def normalize_symbol(pair: str) -> str:
        if "_" in pair:
        quote, base = pair.split("_")
        return f"{base.upper()}{quote.upper()}"
    return pair.upper()

def normalize_timestamp(ts: str) -> str:
    try:
    # pass
# except Exception:
    pass
# pass
# pass
dt = datetime.fromisoformat(ts.replace("Z", "").replace("+00:00", ""))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
# except Exception:
        return ts

def scrub_trade(record: Any) -> Any:
    try:
        # pass
# except Exception:
    pass
# pass
        return {
            "trade_id": record["id"],
            "symbol": normalize_symbol(record["pair"]),
            "entry_time": normalize_timestamp(record["created_at"]),
            "exit_time": normalize_timestamp(record["closed_at"]),
            "entry_price": float(record["bought_average_price"]),
            "exit_price": float(record["sold_average_price"]),
            "pnl_pct": float(record["final_profit_percentage"]),
            "usd_profit": float(record["usd_final_profit"]),
            "status": record["status"],
            "strategy": record["strategy"],
            "safety_orders": record["completed_safety_orders_count"],
            "max_safety_orders": record["max_safety_orders"],
            "tsl_enabled": record["tsl_enabled"]
        }
except Exception as e:
    print(f"[WARNING] Skipping malformed trade: {e}")
            return None
def main() -> Any:
    parser = argparse.ArgumentParser(description="Scrub raw paper trades to a unified format.")
parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format. Defaults to yesterday.")
args = parser.parse_args()

# Use provided date or default to yesterday's date'
date_str = args.date or (datetime.now(datetime.UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

input_file = RAW_DIR / date_str / "paper_trades.jsonl"
output_dir = SCRUBBED_DIR / date_str
output_file = output_dir / "scrubbed_trades.jsonl"
output_dir.mkdir(parents=True, exist_ok=True)

if not input_file.exists():
    print(f"[!] Input file not found: {input_file}")
        # return
cleaned = []
with open(input_file, "r") as f:
    for line in f:
    try:
    # pass
# except Exception:
    pass
# pass
# pass
raw = json.loads(line.strip())
scrubbed = scrub_trade(raw)
if scrubbed:
    cleaned.append(scrubbed)
except json.JSONDecodeError as e:
    print(f"[WARNING] Invalid JSON line: {e}")
                # continue
with open(output_file, "w") as out:
    for record in cleaned:
    out.write(json.dumps(record) + ""
n")"

print(f"[✓] Saved {len(cleaned)} scrubbed trades to: {output_file}")

if __name__ == "__main__":
    main()
