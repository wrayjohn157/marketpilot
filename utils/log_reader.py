# utils/log_reader.py

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DCA_LOG_BASE = Path("/home/signal/market7/dca/logs")


def load_latest_dca_logs(date: str = None) -> list:
    """
    Reads the latest dca_log.jsonl file for the given date (or today by default)
    and returns the most recent entry per deal_id.
    """
    import datetime as dt
    if date is None:
        date = dt.datetime.now().strftime("%Y-%m-%d")

    log_path = DCA_LOG_BASE / date / "dca_log.jsonl"
    if not log_path.exists():
        return []

    latest_by_deal = {}

    with open(log_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                deal_id = entry.get("deal_id")
                ts = entry.get("timestamp")
                if not deal_id or not ts:
                    continue

                # Keep latest per deal_id
                existing = latest_by_deal.get(deal_id)
                if not existing or ts > existing["timestamp"]:
                    latest_by_deal[deal_id] = entry

            except json.JSONDecodeError:
                continue

    return list(latest_by_deal.values())
