# /market7/dashboard_backend/redis_interface.py

import json

# === Redis connection ===
from utils.redis_manager import get_redis_manager
r = get_redis_manager()

def get_active_trades() -> list[dict]:
    """
    Pulls active trade objects stored in Redis matching USDT_* keys.
    """
    keys = r.get_key_stats()
    trades = []
    for key in keys:
        data = r.get_cache(key)
        if data:
            try:
                parsed = json.loads(data)
                trades.append(parsed)
            except Exception:
                continue
    return trades
