# redis_reader.py
import redis
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def get_indicator_data(symbol: str, timeframe: str):
    key = f"{symbol.upper()}_{timeframe}"
    try:
        data = r.get(key)
        if data is None:
            logging.warning(f"❌ No data found for {key}")
            return None
        indicators = json.loads(data)
        logging.info(f"✅ Indicators for {key}:\n{json.dumps(indicators, indent=2)}")
        return indicators
    except Exception as e:
        logging.error(f"Error retrieving data for {key}: {e}")
        return None

if __name__ == "__main__":
    while True:
        symbol = input("Enter symbol (e.g. BTC): ").strip()
        if symbol.lower() == "exit":
            break
        tf = input("Enter timeframe (15m / 1h / 4h): ").strip()
        get_indicator_data(symbol, tf)
