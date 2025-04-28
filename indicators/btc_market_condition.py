#!/usr/bin/env python3
import sys
from pathlib import Path

# === Patch sys.path to project root ===
sys.path.append(str(Path(__file__).resolve().parent.parent))

import logging
import redis
import json
from utils.local_indicators import fetch_binance_klines, compute_ema, compute_adx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# Initialize Redis client (using DB 0; adjust if necessary)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def determine_btc_market():
    """
    Fetches BTCUSDT 1h klines and computes EMA(50), EMA(200), and ADX(14).
    Returns 'bullish' if EMA50 > EMA200 and ADX >= 20,
            'bearish' if EMA50 < EMA200 and ADX >= 20,
            otherwise 'neutral'.
    """
    df = fetch_binance_klines(symbol="BTCUSDT", interval="1h", limit=251)
    if df is None or df.empty:
        logging.error("Failed to fetch klines data for BTC.")
        return "neutral"  # Fallback

    ema50 = compute_ema(df, period=50)
    ema200 = compute_ema(df, period=200)
    adx = compute_adx(df, period=14)
    logging.info(f"Computed EMA50: {ema50}, EMA200: {ema200}, ADX: {adx}")

    if ema50 is None or ema200 is None or adx is None:
        return "neutral"

    if ema50 > ema200 and adx >= 20:
        return "bullish"
    elif ema50 < ema200 and adx >= 20:
        return "bearish"
    else:
        return "neutral"

def save_market_condition_to_redis(condition):
    """
    Saves the market condition string into Redis under the key 'btc_condition'
    so that the dashboard and other pipeline components can use it.
    """
    try:
        r.set("btc_condition", condition)
        logging.info(f"Saved btc_condition to Redis: {condition}")
    except Exception as e:
        logging.error(f"Error saving btc_condition to Redis: {e}")

def main():
    market_condition = determine_btc_market()
    logging.info(f"Market condition detected: {market_condition}")
    save_market_condition_to_redis(market_condition)

if __name__ == "__main__":
    main()
