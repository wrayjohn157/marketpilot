# /market7/dashboard_backend/redis_interface.py

import redis
import json

# === Redis connection ===
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def get_active_trades() -> list[dict]:
    """
    Pulls active trade objects stored in Redis matching USDT_* keys.
    """
    keys = r.keys("USDT_*")
    trades = []
    for key in keys:
        data = r.get(key)
        if data:
            try:
                parsed = json.loads(data)
                trades.append(parsed)
            except Exception:
                continue
    return trades
