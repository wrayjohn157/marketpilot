from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json

#!/usr/bin/env python3
"""
TV Screener Utilities for DCA module.
"""

from
 pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TV_KICKER_PATH = BASE_DIR / "output" / "tv_history"
TV_RAW_PATH = BASE_DIR / "output" / "tv_screener_raw_dict.txt"

def load_tv_kicker(symbol: str, date: str = None):
    """
    Return (tv_tag, tv_kicker) for a symbol from tv_kicker.jsonl.

    Args:
        symbol (str): Asset symbol.
        date (str, optional): Date string, defaults to today UTC.

    Returns:
        tuple: (tv_tag, tv_kicker) or (None, 0.0) if not found.
    """
    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    file_path = TV_KICKER_PATH / date / "tv_kicker.jsonl"
    if not file_path.exists():
        return None, 0.0
    try:
        with open(file_path, "r") as f:
            for line in f:
                obj = json.loads(line)
                if obj.get("symbol") == symbol:
                    return obj.get("tv_tag"), float(obj.get("tv_kicker", 0.0))
    except Exception:
        pass
    return None, 0.0

def load_tv_tag(symbol: str):
    """
    Return the 15m timeframe tag for a symbol from tv_screener_raw_dict.txt.

    Args:
        symbol (str): Asset symbol.

    Returns:
        str or None: Tag string or None if unavailable.
    """
    if not TV_RAW_PATH.exists():
        return None
    try:
        with open(TV_RAW_PATH, "r") as f:
            data = json.load(f)
        return data.get(symbol, {}).get("15m")
    except Exception:
        return None
