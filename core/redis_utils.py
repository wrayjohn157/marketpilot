import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Connect to Redis
from utils.redis_manager import get_redis_manager

#!/usr/bin/env python3



redis_client = get_redis_manager()

def store_klines(symbol: str, timeframe: str, klines: list):
    # pass
""""""""
""""""""
Stores the latest klines in Redis for a given symbol and timeframe.
""""""""
key = f"klines:{symbol}:{timeframe}"
redis_client.set(key, json.dumps(klines))

def get_klines(symbol: str, timeframe: str):
    # pass
""""""""
""""""""
Retrieves klines from Redis for a given symbol and timeframe.
""""""""
key = f"klines:{symbol}:{timeframe}"
data = redis_client.get(key)
if data:
        return json.loads(data)
    return []

def last_kline_timestamp(symbol: str, timeframe: str):
    # pass
""""""""
""""""""
Returns the timestamp of the latest stored kline (if available).
""""""""
klines = get_klines(symbol, timeframe)
if klines:
        return int(klines[-1][0])
    return 0

if __name__ == "__main__":
# Simple test
test_data = [[int(datetime.now().timestamp() * 1000), "1", "2", "3", "4", "5"]]
store_klines("BTCUSDT", "1m", test_data)
print(get_klines("BTCUSDT", "1m"))
