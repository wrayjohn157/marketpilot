import json
from pathlib import Path
from datetime import datetime

TV_KICKER_PATH = Path("/home/signal/market6/output/tv_history")
TV_RAW_PATH = Path("/home/signal/market6/output/tv_screener_raw_dict.txt")

def load_tv_kicker(symbol: str, date: str = None):
    """Return (tv_tag, tv_kicker) for a symbol from tv_kicker.jsonl"""
    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    file_path = TV_KICKER_PATH / date / "tv_kicker.jsonl"
    if not file_path.exists():
        return None, 0.0
    with open(file_path, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("symbol") == symbol:
                    return obj.get("tv_tag"), float(obj.get("tv_kicker", 0.0))
            except:
                continue
    return None, 0.0

def load_tv_tag(symbol: str):
    """Return only the 15m tag from tv_screener_raw_dict.txt"""
    if not TV_RAW_PATH.exists():
        return None
    try:
        with open(TV_RAW_PATH, "r") as f:
            data = json.load(f)
        tag = data.get(symbol, {}).get("15m")
        return tag
    except:
        return None
