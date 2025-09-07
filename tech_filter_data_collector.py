#!/usr/bin/env python3

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import MACD, ADXIndicator, EMAIndicator, PSARIndicator
from ta.volatility import AverageTrueRange

from utils.redis_manager import get_redis_manager

"""
Tech Filter Data Collector
Focused data collection for essential tech filter indicators
"""

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REDIS = get_redis_manager()
SYMBOLS = ["BTC", "XRP"]  # Focus on active trading pairs
TIMEFRAMES = ["15m", "1h", "4h"]  # Essential timeframes
BINANCE_BASE_URL = "https://api.binance.com/api/v3/klines"


class TechFilterDataCollector:
    def __init__(self):
        self.redis = REDIS
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MarketPilot-TechFilter/1.0"})

    def fetch_klines(
        self, symbol: str, interval: str, limit: int = 100
    ) -> pd.DataFrame:
        """Fetch klines with rate limiting"""
        try:
            url = f"{BINANCE_BASE_URL}?symbol={symbol}USDT&interval={interval}&limit={limit}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            df = pd.DataFrame(
                data,
                columns=[
                    "open_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_asset_volume",
                    "num_trades",
                    "taker_buy_base_asset_volume",
                    "taker_buy_quote_asset_volume",
                    "ignore",
                ],
            )

            # Convert to numeric
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna()
            return df

        except Exception as e:
            logger.error(f"Failed to fetch {symbol} {interval}: {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate essential tech filter indicators"""
        if len(df) < 50:
            return {}

        try:
            indicators = {}

            # Price data
            indicators["close"] = float(df["close"].iloc[-1])
            indicators["high"] = float(df["high"].iloc[-1])
            indicators["low"] = float(df["low"].iloc[-1])
            indicators["volume"] = float(df["volume"].iloc[-1])

            # Trend indicators
            ema_50 = EMAIndicator(df["close"], 50).ema_indicator()
            ema_200 = EMAIndicator(df["close"], 200).ema_indicator()
            indicators["ema_50"] = float(ema_50.iloc[-1]) if not ema_50.empty else None
            indicators["ema_200"] = (
                float(ema_200.iloc[-1]) if not ema_200.empty else None
            )

            # Momentum indicators
            rsi = RSIIndicator(df["close"], 14).rsi()
            indicators["rsi"] = float(rsi.iloc[-1]) if not rsi.empty else None

            # MACD
            macd = MACD(df["close"])
            indicators["macd"] = (
                float(macd.macd().iloc[-1]) if not macd.macd().empty else None
            )
            indicators["macd_signal"] = (
                float(macd.macd_signal().iloc[-1])
                if not macd.macd_signal().empty
                else None
            )
            indicators["macd_histogram"] = (
                float(macd.macd_diff().iloc[-1]) if not macd.macd_diff().empty else None
            )

            # Volatility
            adx = ADXIndicator(df["high"], df["low"], df["close"], 14).adx()
            indicators["adx"] = float(adx.iloc[-1]) if not adx.empty else None

            atr = AverageTrueRange(
                df["high"], df["low"], df["close"], 14
            ).average_true_range()
            indicators["atr"] = float(atr.iloc[-1]) if not atr.empty else None

            # Stochastic RSI
            stoch_rsi = StochRSIIndicator(df["close"], 14, 3, 3)
            indicators["stoch_rsi_k"] = (
                float(stoch_rsi.stochrsi_k().iloc[-1])
                if not stoch_rsi.stochrsi_k().empty
                else None
            )
            indicators["stoch_rsi_d"] = (
                float(stoch_rsi.stochrsi_d().iloc[-1])
                if not stoch_rsi.stochrsi_d().empty
                else None
            )

            # Parabolic SAR
            psar = PSARIndicator(df["high"], df["low"], df["close"]).psar()
            indicators["psar"] = float(psar.iloc[-1]) if not psar.empty else None

            # Timestamp
            indicators["timestamp"] = int(time.time())

            return indicators

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}

    def save_to_redis(self, symbol: str, timeframe: str, indicators: dict):
        """Save indicators to Redis"""
        try:
            key = f"tech_filter:{symbol}:{timeframe}"
            self.redis.setex(key, 3600, json.dumps(indicators))  # 1 hour TTL
            logger.info(f"Saved {symbol} {timeframe} indicators to Redis")
        except Exception as e:
            logger.error(f"Failed to save to Redis: {e}")

    def collect_data(self):
        """Main data collection loop"""
        logger.info("🚀 Starting tech filter data collection")

        for symbol in SYMBOLS:
            for timeframe in TIMEFRAMES:
                try:
                    logger.info(f"Collecting {symbol} {timeframe}")

                    # Fetch klines
                    df = self.fetch_klines(symbol, timeframe)
                    if df.empty:
                        logger.warning(f"No data for {symbol} {timeframe}")
                        continue

                    # Calculate indicators
                    indicators = self.calculate_indicators(df)
                    if not indicators:
                        logger.warning(f"No indicators for {symbol} {timeframe}")
                        continue

                    # Save to Redis
                    self.save_to_redis(symbol, timeframe, indicators)

                    # Rate limiting
                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error processing {symbol} {timeframe}: {e}")
                    continue

        logger.info("✅ Tech filter data collection complete")


def main():
    collector = TechFilterDataCollector()
    collector.collect_data()


if __name__ == "__main__":
    main()
