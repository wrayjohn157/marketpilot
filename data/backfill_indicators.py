from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
import os

from ta.momentum import StochRSIIndicator, RSIIndicator
from ta.trend import EMAIndicator, ADXIndicator, MACD, PSARIndicator
from ta.volatility import AverageTrueRange
import pandas as pd
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


#!/usr/bin/env python3
from
 pathlib import Path

# === Config ===
BASE_DIR = Path("/home/signal/market7")
SYMBOLS_FILE = BASE_DIR / "data" / "binance_symbols.json"
SNAPSHOT_DIR = get_path("snapshots")
TIMEFRAMES = ["1h", "4h", "15m"]
KLINE_LIMIT = 210
START_DATE = datetime(2025, 6, 1)
END_DATE = datetime(2025, 6, 27)

# === Logging ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Load symbols ===
with open(SYMBOLS_FILE) as f:
    SYMBOLS = json.load(f)

# === Helpers ===
def fetch_klines(symbol: Any, interval: Any, end_ts: Any, limit: Any = KLINE_LIMIT) -> Any:
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}&endTime={end_ts}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        df = pd.DataFrame(
            r.json(),
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "qav",
                "num_trades",
                "tb_base_vol",
                "tbqav",
                "ignore",
            ],
        )
        df = df.astype(
            {
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
            }
        )
        return df
    except Exception as e:
        logging.warning(f"❌ {symbol} {interval}: {e}")
        return None

def compute_indicators(df: Any) -> Any:
    try:
        indicators = {
            "EMA50": EMAIndicator(df["close"], 50).ema_indicator().iloc[-1],
            "EMA200": EMAIndicator(df["close"], 200).ema_indicator().iloc[-1],
            "RSI14": RSIIndicator(df["close"]).rsi().iloc[-1],
            "ADX14": ADXIndicator(df["high"], df["low"], df["close"]).adx().iloc[-1],
            "QQE": df["close"].ewm(alpha=1 / 14, adjust=False).mean().iloc[-1],
            "PSAR": PSARIndicator(df["high"], df["low"], df["close"]).psar().iloc[-1],
            "ATR": AverageTrueRange(df["high"], df["low"], df["close"])
            .average_true_range()
            .iloc[-1],
        }

        stoch_rsi = StochRSIIndicator(df["close"])
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
        indicators["timestamp"] = int(df["time"].iloc[-1] // 1000)

        return indicators
    except Exception as e:
        logging.warning(f"⚠️ Indicator calc failed: {e}")
        return None

def save_snapshot(symbol: Any, tf: Any, date_str: Any, indicators: Any) -> Any:
    day_folder = SNAPSHOT_DIR / date_str
    day_folder.mkdir(parents=True, exist_ok=True)
    jsonl_file = day_folder / f"{symbol}_{tf}.jsonl"
    with open(jsonl_file, "a") as f:
        f.write(json.dumps(indicators) + "\n")

# === Main ===

def process_symbol_tf(symbol: Any, tf: Any) -> Any:
    interval_ms = {
        "1h": 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
    }[tf]
    full_symbol = symbol.upper() + "USDT"
    day = START_DATE
    while day <= END_DATE:
        for i in range(0, 24 if tf == "1h" else 6, int(tf[:-1])):
            hour_time = day + pd.Timedelta(hours=i)
            end_ts = int(hour_time.timestamp() * 1000)
            df = fetch_klines(full_symbol, tf, end_ts)
            if df is not None and len(df) >= 100:
                indicators = compute_indicators(df)
                if indicators:
                    save_snapshot(symbol, tf, day.strftime("%Y-%m-%d"), indicators)
                    logging.info(f"✅ {symbol} {tf} {hour_time}")
            else:
                logging.info(f"⏭️ Skipped {symbol} {tf} {hour_time} (insufficient data)")
            time.sleep(0.1)
        day += pd.Timedelta(days=1)

def run_backfill() -> Any:
    max_workers = 10
    for tf in TIMEFRAMES:
        if tf == "15m":
            continue  # Skip 15m for now
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_symbol_tf, symbol, tf) for symbol in SYMBOLS]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Thread failed: {e}")

if __name__ == "__main__":
    run_backfill()

