#!/usr/bin/env python3
import os
import time
import json
import redis
import logging
import requests
import pandas as pd
from datetime import datetime
from ta.momentum import StochRSIIndicator, RSIIndicator
from ta.trend import EMAIndicator, ADXIndicator, MACD, PSARIndicator
from ta.volatility import AverageTrueRange

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REFRESH_INTERVAL = 60
KLINE_LIMIT = 210
TIMEFRAMES = ["15m", "1h", "4h"]

# Paths
BASE_PATH = os.path.dirname(__file__)
FILTERED_FILE = os.path.join(BASE_PATH, "filtered_pairs.json")

def get_snapshot_dir():
    path = os.path.join(BASE_PATH, "snapshots", datetime.utcnow().strftime("%Y-%m-%d"))
    os.makedirs(path, exist_ok=True)
    return path

# Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def fetch_klines(symbol, interval, limit=150):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        df = pd.DataFrame(resp.json(), columns=[
            "time", "open", "high", "low", "close", "volume", "close_time",
            "qav", "num_trades", "tb_base_vol", "tbqav", "ignore"
        ])
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        return df
    except Exception as e:
        logging.warning(f"Failed to fetch klines for {symbol} {interval}: {e}")
        return None

def compute_indicators(df):
    indicators = {}
    indicators["EMA50"] = EMAIndicator(df["close"], 50).ema_indicator().iloc[-1]
    indicators["EMA200"] = EMAIndicator(df["close"], 200).ema_indicator().iloc[-1]
    indicators["RSI14"] = RSIIndicator(df["close"]).rsi().iloc[-1]
    indicators["ADX14"] = ADXIndicator(df["high"], df["low"], df["close"]).adx().iloc[-1]

    rsi_series = RSIIndicator(df["close"]).rsi()
    smoothed_rsi = rsi_series.ewm(alpha=1/14, adjust=False).mean()
    atr_rsi = abs(rsi_series - smoothed_rsi).ewm(alpha=1/14, adjust=False).mean()
    indicators["QQE"] = smoothed_rsi.iloc[-1] + 4.236 * atr_rsi.iloc[-1]

    indicators["PSAR"] = PSARIndicator(df["high"], df["low"], df["close"]).psar().iloc[-1]
    indicators["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"]).average_true_range().iloc[-1]

    stoch_rsi = StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
    indicators["StochRSI_K"] = stoch_rsi.stochrsi_k().iloc[-1]
    indicators["StochRSI_D"] = stoch_rsi.stochrsi_d().iloc[-1]

    macd = MACD(df["close"])
    indicators["MACD"] = macd.macd().iloc[-1]
    indicators["MACD_signal"] = macd.macd_signal().iloc[-1]
    indicators["MACD_diff"] = macd.macd_diff().iloc[-1]
    indicators["MACD_Histogram"] = macd.macd_diff().iloc[-1]
    indicators["MACD_Histogram_Prev"] = macd.macd_diff().iloc[-2]
    indicators["MACD_lift"] = macd.macd().iloc[-1] - macd.macd().iloc[-2]

    indicators["latest_close"] = df["close"].iloc[-1]
    indicators["timestamp"] = int(time.time())

    return indicators

def load_filtered_tokens():
    if not os.path.exists(FILTERED_FILE):
        logging.error("Missing filtered_pairs.json")
        return []
    with open(FILTERED_FILE, "r") as f:
        return json.load(f)

def save_to_disk(symbol, tf, indicators):
    snapshot_dir = get_snapshot_dir()
    filename = os.path.join(snapshot_dir, f"{symbol.upper()}_{tf}.json")
    try:
        with open(filename, "w") as f:
            json.dump(indicators, f, indent=2)
        logging.info(f"📂 {symbol.upper()}_{tf} indicators saved to disk")
    except Exception as e:
        logging.error(f"❌ Failed to save {symbol.upper()}_{tf} to disk: {e}")

def main():
    logging.info("📊 Starting indicator updater...")
    while True:
        symbols = load_filtered_tokens()
        for symbol in symbols:
            full_symbol = symbol.upper() + "USDT"
            for tf in TIMEFRAMES:
                df = fetch_klines(full_symbol, tf, limit=KLINE_LIMIT)
                if df is None or len(df) < 100:
                    continue
                indicators = compute_indicators(df)
                key = f"{symbol.upper()}_{tf}"
                r.set(key, json.dumps(indicators))

                # ✅ Write individual indicators for fork scoring
                try:
                    r.set(f"{symbol.upper()}_{tf}_RSI14", indicators["RSI14"])
                    r.set(f"{symbol.upper()}_{tf}_StochRSI_K", indicators["StochRSI_K"])
                    r.set(f"{symbol.upper()}_{tf}_StochRSI_D", indicators["StochRSI_D"])
                except Exception as e:
                    logging.warning(f"⚠️ Failed to write individual indicators for {symbol}: {e}")

                save_to_disk(symbol, tf, indicators)
                logging.info(f"✅ {key} indicators written to Redis")
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()
