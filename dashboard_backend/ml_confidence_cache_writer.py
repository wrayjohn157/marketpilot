#!/usr/bin/env python3
# /market7/dashboard_backend/ml_confidence_cache_writer.py

import sys
import json
import redis
from datetime import datetime, timedelta
from pathlib import Path

# === Correct import root ===
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.config_loader import PATHS
from dca.utils.entry_utils import get_live_3c_trades

# === Config ===
REDIS_KEY = "confidence_list"
LOG_BASE = PATHS["live_logs"].parent / "dca" / "logs"   # /market7/live/dca/logs
CACHE_PATH = PATHS["live_logs"] / "ml_confidence.json"
MAX_ENTRIES = 20
DAYS_BACK = 5

REDIS = redis.Redis(host="localhost", port=6379, db=0)

def load_active_deal_ids():
    try:
        active = get_live_3c_trades()
        return {str(deal["id"]) for deal in active if "id" in deal}
    except Exception as e:
        print(f"❌ Failed to fetch active trades: {e}")
        return set()

def scan_logs_for_active_deals(active_ids):
    latest_logs = {}
    for delta in range(DAYS_BACK):
        day = (datetime.utcnow() - timedelta(days=delta)).strftime("%Y-%m-%d")
        log_path = LOG_BASE / day / "dca_log.jsonl"
        if not log_path.exists():
            continue

        try:
            with open(log_path, "r") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                        deal_id = str(row.get("deal_id"))
                        if deal_id in active_ids and isinstance(row.get("confidence_score"), (int, float)):
                            prev = latest_logs.get(deal_id)
                            if not prev or row.get("timestamp", 0) > prev.get("timestamp", 0):
                                latest_logs[deal_id] = row
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[WARN] Error reading {log_path}: {e}")
            continue

    return latest_logs

def build_confidence_cache(deal_logs):
    filtered = [
        row for row in deal_logs.values()
        if isinstance(row.get("confidence_score"), (int, float))
    ]
    sorted_logs = sorted(filtered, key=lambda x: x["confidence_score"], reverse=True)

    cache = []
    for row in sorted_logs[:MAX_ENTRIES]:
        cache.append({
            "symbol": row.get("symbol"),
            "confidence_score": round(row["confidence_score"], 4),
            "decision": row.get("decision", "n/a"),
            "rejection_reason": row.get("rejection_reason", "n/a")
        })
    return cache

def main():
    active_ids = load_active_deal_ids()
    if not active_ids:
        print("⚠️ No active trades to match.")
        return

    deal_logs = scan_logs_for_active_deals(active_ids)
    if not deal_logs:
        print("⚠️ No matching DCA entries across recent logs.")
        return

    confidence_cache = build_confidence_cache(deal_logs)

    # ✅ Save to Redis
    REDIS.set(REDIS_KEY, json.dumps(confidence_cache))
    print(f"✅ Cached {len(confidence_cache)} confidence entries to Redis.")

    # ✅ Also save to file (for fallback)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(confidence_cache, f, indent=2)
    print(f"📁 Also saved to: {CACHE_PATH}")

if __name__ == "__main__":
    main()
