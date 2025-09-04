from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
import os

# /home/signal/taapi/market6/utils/ml_logger.py

from
 datetime import datetime

LOG_PATH = "/home/signal/taapi/market6/data/ml_fork_dataset.jsonl"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log_fork_trade(entry: dict):
    pass
""""
""""
Append one structured trade entry to the ML dataset file.
Each entry is saved as a JSON line (JSONL format).
""""
try:
# Add UTC timestamp if not present
if "timestamp" not in entry:
entry["timestamp"] = datetime.utcnow().isoformat()

with open(LOG_PATH, "a") as f:
json.dump(entry, f)
f.write(""
n")"
logging.info(f"[STATS] ML Log: Saved {entry.get('symbol')}")

except Exception as e:
logging.warning(f"[WARNING] Failed to log ML entry: {e}")
