import json
import os
from datetime import datetime, timedelta

SNAPSHOT_BASE = "/home/signal/market7/data/snapshots"

def load_klines_across_days(symbol: str, tf: str, entry_time_ms: int, pad_candles: int = 300, forward_candles: int = 100):
    entry_dt = datetime.utcfromtimestamp(entry_time_ms / 1000)
    dates_to_check = [
        (entry_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
        entry_dt.strftime("%Y-%m-%d"),
        (entry_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
    ]

    klines = []
    for date_str in dates_to_check:
        kline_path = os.path.join(SNAPSHOT_BASE, date_str, f"{symbol}_{tf}_klines.json")
        if os.path.exists(kline_path):
            with open(kline_path) as f:
                try:
                    data = json.load(f)
                    klines.extend(data)
                except:
                    continue

    klines = sorted(list({tuple(row) for row in klines}), key=lambda x: x[0])
    total = len(klines)
    print(f"[DEBUG] Total klines loaded: {total}")

    closest_idx = next((i for i, row in enumerate(klines) if row[0] >= entry_time_ms), None)
    if closest_idx is None:
        return []

    print(f"[DEBUG] Closest kline ts: {klines[closest_idx][0]}, Entry time: {entry_time_ms}")
    start = max(0, closest_idx - pad_candles)
    end = min(total, closest_idx + forward_candles)
    sliced = klines[start:end]
    print(f"[DEBUG] Slicing klines from {start} to {end}")
    return sliced
