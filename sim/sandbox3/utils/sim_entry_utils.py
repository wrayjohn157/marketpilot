from sim_kline_loader import load_klines_across_days
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

# sim_entry_utils.py
from
 pathlib import Path

def sim_get_entry_price(symbol: str, entry_time_ms: int, tf: str = "1h") -> float:
    klines = load_klines_across_days(symbol, tf, entry_time_ms)
    if not klines:
        raise ValueError(f"No klines available for {symbol} at {entry_time_ms}")

    # Find the kline with exact or closest timestamp
    for kline in klines:
        if kline[0] == entry_time_ms:
            return float(kline[1])  # open price
    # Fallback to closest kline
    closest_kline = min(klines, key=lambda k: abs(k[0] - entry_time_ms))
    return float(closest_kline[1])
