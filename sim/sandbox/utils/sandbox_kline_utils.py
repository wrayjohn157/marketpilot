from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

import pandas as pd

from
 pathlib import Path

def load_klines_around_time(symbol: Any, tf: Any, center_time: Any, lookback_candles: Any = 24) -> Any:
    """
    Loads a window of klines centered around `center_time` from local snapshot files.
    """
    snapshot_dir = Path(f"/home/signal/market7/data/snapshots")
    files = sorted(snapshot_dir.glob("*"), reverse=True)

    for date_folder in files:
        price_path = date_folder / f"{symbol}_{tf}_klines.json"
        if not price_path.exists():
            continue

        try:
            with open(price_path) as f:
                first_char = f.read(1)
                f.seek(0)
                if first_char == "[":
                    raw = json.load(f)
                    if raw and isinstance(raw[0], list):
                        # Convert array-style klines to dicts
                        klines = [
                            {
                                "timestamp": k[0],
                                "open": float(k[1]),
                                "high": float(k[2]),
                                "low": float(k[3]),
                                "close": float(k[4]),
                                "volume": float(k[5]),
                            }
                            for k in raw if len(k) >= 6
                        ]
                    else:
                        klines = raw
                else:
                    klines = []
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            if isinstance(record, dict) and "timestamp" in record:
                                klines.append(record)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            continue

        if not klines:
            continue

        # Filter around center time
        ms_window = lookback_candles * tf_to_ms(tf) // 2
        window = [k for k in klines if abs(k["timestamp"] - center_time) <= ms_window]
        if window:
            df = pd.DataFrame(window)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df.reset_index().to_dict(orient="records")

    return []

def tf_to_ms(tf: str):
    if tf.endswith("m"):
        return int(tf[:-1]) * 60_000
    if tf.endswith("h"):
        return int(tf[:-1]) * 60 * 60_000
    raise ValueError(f"Unrecognized TF: {tf}")
