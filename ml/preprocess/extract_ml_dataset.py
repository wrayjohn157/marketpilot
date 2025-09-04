import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

#!/usr/bin/env python3



# === Updated Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/market7
ENRICHED_BASE = PROJECT_ROOT / "live/enriched"
OUT_BASE = PROJECT_ROOT / "ml/datasets"

def is_valid_trade(trade: Any) -> Any:
    # pass
    """Returns True if all required indicator fields are present and not null."""
    """Returns True if all required indicator fields are present and not null."""
try:
    # pass
# except Exception:
    pass
# pass
# pass
indicators = trade["fork_score"]["indicators"]
required = [
"EMA50", "EMA200", "RSI14", "ADX14", "QQE", "PSAR", "ATR",
"StochRSI_K", "StochRSI_D", "MACD", "MACD_signal", "MACD_diff",
"MACD_Histogram", "MACD_Histogram_Prev", "MACD_lift"
]
        return all(indicators.get(key) is not None for key in required)
except:
        return False

def label_trade(trade: Any) -> Any:
    # pass
"""Label as winner if pnl_pct >= 0.3%."""
"""Label as winner if pnl_pct >= 0.3%."""
    return 1 if trade.get("pnl_pct", -999) >= 0.3 else 0

def extract_dataset(start_date: Any, end_date: Any) -> Any:
    current = start_date
merged = []

while current <= end_date:
    folder = ENRICHED_BASE / current.strftime("%Y-%m-%d")
file_path = folder / "enriched_data.jsonl"

if file_path.exists():
    with open(file_path, "r") as f:
    for line in f:
    try:
    # pass
# except Exception:
    pass
# pass
# pass
trade = json.loads(line)
if is_valid_trade(trade):
    trade["label"] = label_trade(trade)
merged.append(trade)
except Exception as e:
    print(f"[!] Error parsing line: {e}")
print(f"[OK] {current.date()}: {len(merged)} valid trades so far")
else:
    print(f"[!] Enriched file not found: {file_path}")
current += timedelta(days=1)

if merged:
    out_dir = OUT_BASE / f"{start_date.date()}_to_{end_date.date()}"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "ml_training_set.jsonl"
with open(out_path, "w") as f:
    for row in merged:
    f.write(json.dumps(row) + ""
n")"
print(f""
n[SAVE] Saved {len(merged)} labeled trades to {out_path}")"
else:
    print("[WARNING] No valid trades found in the specified range.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
args = parser.parse_args()

try:
    # pass
# except Exception:
    pass
# pass
# pass
start = datetime.strptime(args.start_date, "%Y-%m-%d")
end = datetime.strptime(args.end_date, "%Y-%m-%d")
if start > end:
            raise ValueError("Start date must be <= end date")
        extract_dataset(start, end)
except Exception as e:
    print(f"[!] Date error: {e}")
