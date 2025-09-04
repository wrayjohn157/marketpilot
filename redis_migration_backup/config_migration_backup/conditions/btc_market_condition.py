#!/usr/bin/env python3

import logging
import sys
from pathlib import Path

# === Setup Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent  # /market7
sys.path.append(str(BASE_DIR))

from data.rolling_indicators import fetch_binance_klines, compute_ema, compute_adx

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Redis Client ===
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def determine_btc_market():
    """
    Analyzes BTCUSDT 1h chart to classify market condition: 'bullish', 'bearish', or 'neutral'.
    """
    df = fetch_binance_klines(symbol="BTCUSDT", interval="1h", limit=251)
    if df is None or df.empty:
        logging.error("❌ Failed to fetch BTCUSDT 1h klines.")
        return "neutral"

    ema50 = compute_ema(df, period=50)
    ema200 = compute_ema(df, period=200)
    adx = compute_adx(df, period=14)

    logging.info(f"📈 EMA50={ema50:.4f}, EMA200={ema200:.4f}, ADX={adx:.2f}")

    if ema50 is None or ema200 is None or adx is None:
        return "neutral"

    if ema50 > ema200 and adx >= 20:
        return "bullish"
    elif ema50 < ema200 and adx >= 20:
        return "bearish"
    else:
        return "neutral"

def save_market_condition_to_redis(condition: str):
    """
    Saves the computed market condition to Redis under key 'btc_condition'.
    """
    try:
        redis_client.set("cache:btc_condition", condition)
        logging.info(f"✅ Saved btc_condition = '{condition}' to Redis.")
    except Exception as e:
        logging.error(f"❌ Error saving btc_condition to Redis: {e}")

def main():
    market_condition = determine_btc_market()
    save_market_condition_to_redis(market_condition)

if __name__ == "__main__":
    main()
