from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

from
 datetime import datetime

FORK_HISTORY_BASE = Path("/home/signal/market7/output/fork_history")

def sim_load_fork_meta(symbol: str, entry_time_ms: int) -> dict:
    # Derive date folder from timestamp
    entry_date = datetime.utcfromtimestamp(entry_time_ms / 1000).strftime("%Y-%m-%d")
    target_file = FORK_HISTORY_BASE / entry_date / "fork_scores.jsonl"

    if not target_file.exists():
        raise FileNotFoundError(f"Fork file not found: {target_file}")

    with open(target_file, "r") as f:
        for line in f:
            try:
                record = json.loads(line)
                ts_val = record.get("timestamp", 0)
                if isinstance(ts_val, str):
                    try:
                        ts_val = int(datetime.fromisoformat(ts_val.replace("Z", "")).timestamp() * 1000)
                    except ValueError:
                        continue  # Skip if malformed
                if record.get("symbol") == symbol and abs(ts_val - entry_time_ms) <= 120000:
                    return record
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No matching fork entry for {symbol} at {entry_time_ms}")
