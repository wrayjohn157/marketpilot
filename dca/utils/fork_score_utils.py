#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from indicators.fork_score_filter import compute_subscores

# === Dynamic Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /market7
FORK_HISTORY_BASE = BASE_DIR / "output" / "fork_history"

# === Entry Score Loader ===
def load_fork_entry_score(symbol: str, entry_ts: int) -> Optional[float]:
    """
    Return fork score closest to the trade entry timestamp from fork history.
    Both timestamps are in milliseconds. Only records with a timestamp <= entry_ts 
    are considered, and the record with the smallest delta (entry_ts - record_ts) is returned.
    """
    date_str = datetime.utcfromtimestamp(entry_ts / 1000).strftime("%Y-%m-%d")
    path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
    if not path.exists():
        return None

    best_match = None
    smallest_delta = float("inf")
    
    with open(path, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("symbol") != symbol:
                continue
            score_ts_raw = obj.get("timestamp")
            if not score_ts_raw or not str(score_ts_raw).isdigit():
                continue
            record_ts = int(score_ts_raw)  # record_ts in milliseconds
            if record_ts > entry_ts:
                continue
            delta = entry_ts - record_ts
            if delta < smallest_delta:
                smallest_delta = delta
                best_match = obj

    if best_match and "score" in best_match:
        return round(float(best_match["score"]), 4)

    print(f"[WARN] No matching entry score found for {symbol} at ts={entry_ts}")
    return None

# === Recent Score Loader ===
def load_recent_score(symbol: str, now_ts: int) -> Optional[Tuple[float, int]]:
    """
    Return (score, record_ts) for the most recent fork score record within 10 minutes of now_ts.
    """
    date_str = datetime.utcfromtimestamp(now_ts / 1000).strftime("%Y-%m-%d")
    path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
    if not path.exists():
        return None

    best = None
    best_diff = float("inf")
    best_record_ts = None

    with open(path, "r") as f:
        for line in f:
            try:
                record = json.loads(line)
            except Exception:
                continue
            if record.get("symbol") != symbol:
                continue
            ts = int(record.get("timestamp", 0))
            if ts > now_ts:
                continue
            diff = now_ts - ts
            if diff <= 600_000 and diff < best_diff:
                best = record
                best_diff = diff
                best_record_ts = ts

    if best:
        return best["score"], best_record_ts
    return None

# === Fallback Fork Scorer ===
def compute_fork_score(symbol: str) -> Optional[float]:
    """
    Fallback: recalculate fork score using the fork_score_filter subscores logic.
    """
    try:
        score, _, _, _ = compute_subscores(symbol)
        return score
    except Exception as e:
        print(f"[ERROR] Could not compute score for {symbol}: {e}")
        return None
