import os
import json
from datetime import datetime
from typing import Optional

# Allow overriding the snapshot directory via env var
DEFAULT_BTC_CONTEXT_DIR = os.environ.get(
    "BTC_CONTEXT_DIR",
    "/home/signal/market7/dashboard_backend/btc_logs"
)

def get_btc_context_for_sim(entry_time: int, base_dir: str = None) -> Optional[dict]:
    """
    Get BTC context from simulated snapshot data for the given entry timestamp (in ms).
    Searches the closest hourly indicator snapshot on the same day.
    """
    base = base_dir or DEFAULT_BTC_CONTEXT_DIR
    ts_sec = entry_time // 1000
    GRACE_SEC = 300
    date_str = datetime.utcfromtimestamp(ts_sec).strftime("%Y-%m-%d")
    # Expect indicator file like btc_snapshots.jsonl under each date folder
    filepath = os.path.join(base, date_str, "btc_snapshots.jsonl")

    if not os.path.exists(filepath):
        # fallback defaults
        return {
            "rsi": 45,
            "adx": 20,
            "macd_histogram": 0,
            "status": "SAFE",
            "status_score": 0.5,
            "vwap": 0,
            "timestamp": ts_sec
        }

    closest = None
    closest_delta = float("inf")

    with open(filepath, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                # timestamp in sec or ms?
                ts_row = data.get("timestamp", 0)
                if ts_row > 1e12:
                    ts_row //= 1000
                delta = abs(ts_row - ts_sec)
                if delta < closest_delta:
                    closest = data
                    closest_delta = delta
            except Exception:
                continue

    # enforce maximum allowed time difference
    if closest_delta > GRACE_SEC:
        closest = None

    if not closest:
        return {
            "rsi": 45,
            "adx": 20,
            "macd_histogram": 0,
            "status": "SAFE",
            "status_score": 0.5,
            "vwap": 0,
            "timestamp": ts_sec
        }

    rsi_val = closest.get("rsi", 45)
    adx_val = closest.get("adx", 20)
    macd_hist_val = closest.get("macd_histogram", 0)
    status_val = closest.get("market_condition", "SAFE")
    status_score_val = closest.get("status_score", 0.5)
    vwap_val = closest.get("vwap_signal", 0)

    # Normalize for engine
    return {
        "rsi": rsi_val,
        "adx": adx_val,
        "macd_histogram": macd_hist_val,
        "status": status_val,
        "status_score": status_score_val,
        "vwap": vwap_val,
        "timestamp": closest.get("timestamp", ts_sec)
    }

def load_btc_snapshot_for_time(entry_time: int, tf: str = "1h") -> dict:
    """
    Compatibility wrapper for simulator expecting `load_btc_snapshot_for_time`.
    """
    full = get_btc_context_for_sim(entry_time)
    return {
        "btc_rsi": full.get("rsi", 45),
        "btc_adx": full.get("adx", 20),
        "btc_macd_histogram": full.get("macd_histogram", 0),
        "btc_status_score": full.get("status_score", 0.5),
    }
