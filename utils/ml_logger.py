# /home/signal/taapi/market6/utils/ml_logger.py

import json
import os
from datetime import datetime
import logging

LOG_PATH = "/home/signal/taapi/market6/data/ml_fork_dataset.jsonl"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log_fork_trade(entry: dict):
    """
    Append one structured trade entry to the ML dataset file.
    Each entry is saved as a JSON line (JSONL format).
    """
    try:
        # Add UTC timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.utcnow().isoformat()

        with open(LOG_PATH, "a") as f:
            json.dump(entry, f)
            f.write("\n")
        logging.info(f"📊 ML Log: Saved {entry.get('symbol')}")

    except Exception as e:
        logging.warning(f"⚠️ Failed to log ML entry: {e}")
