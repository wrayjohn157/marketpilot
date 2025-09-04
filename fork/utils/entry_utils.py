from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os


# /home/signal/market7/fork/utils/entry_utils.py

from
 pathlib import Path

KLINE_BASE = Path(PATHS["kline_snapshots"])

# === Save a daily entry (optional for registry or logs) ===
def save_daily_entry(entry: dict):
    date_str = datetime.utcfromtimestamp(entry["entry_time"]).strftime("%Y-%m-%d")
    daily_folder = KLINE_BASE.parent / "fork_entry_logs" / date_str
    daily_folder.mkdir(parents=True, exist_ok=True)
    daily_file = daily_folder / "entries.jsonl"

    with daily_file.open("a") as f:
        f.write(json.dumps(entry) + "\n")

# === Get entry price from kline snapshot ===
def get_entry_price(symbol: str, entry_ts: int) -> float:
    symbol = symbol.replace("USDT", "")
    file_path = KLINE_BASE / f"{symbol}_5m_klines.json"
    if not file_path.exists():
        return 0.0

    with file_path.open() as f:
        klines = json.load(f)

    for candle in klines:
        if abs(candle[0] / 1000 - entry_ts) <= 300:
            return float(candle[1])

    return float(klines[-1][1]) if klines else 0.0

# === Compute score hash from indicators ===
def compute_score_hash(indicators: dict) -> str:
    if not indicators:
        return ""
    parts = [f"{k}:{v}" for k, v in sorted(indicators.items())]
    return "_".join(parts)

