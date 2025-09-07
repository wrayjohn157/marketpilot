#!/usr/bin/env python3
"""
Standalone Indicator Service - No continuous loops
Can be run via cron or external scheduler
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import MACD, ADXIndicator, EMAIndicator, PSARIndicator
from ta.volatility import AverageTrueRange

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from config.unified_config_manager import get_path
from utils.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
KLINE_LIMIT = 210
TIMEFRAMES = ["15m", "1h", "4h"]

# Paths
FILTERED_FILE = get_path("filtered_pairs")
SNAPSHOTS_BASE = get_path("snapshots")


def load_symbols() -> List[str]:
    """Load symbols from filtered pairs file"""
    try:
        if FILTERED_FILE.exists():
            with open(FILTERED_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return list(data.keys())
        return []
    except Exception as e:
        logger.error(f"Error loading symbols: {e}")
        return []


def get_klines(symbol: str, timeframe: str, limit: int = 210) -> Optional[pd.DataFrame]:
    """Get kline data from Binance"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": timeframe, "limit": limit}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        df = pd.DataFrame(
            data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )

        # Convert to numeric
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        return df

    except Exception as e:
        logger.error(f"Error getting klines for {symbol} {timeframe}: {e}")
        return None


def calculate_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate technical indicators"""
    try:
        indicators = {}

        # RSI
        rsi = RSIIndicator(df["close"], window=14)
        indicators["rsi"] = rsi.rsi().iloc[-1]

        # MACD
        macd = MACD(df["close"])
        indicators["macd"] = macd.macd().iloc[-1]
        indicators["macd_signal"] = macd.macd_signal().iloc[-1]
        indicators["macd_histogram"] = macd.macd_diff().iloc[-1]

        # ADX
        adx = ADXIndicator(df["high"], df["low"], df["close"], window=14)
        indicators["adx"] = adx.adx().iloc[-1]

        # EMA
        ema_20 = EMAIndicator(df["close"], window=20)
        ema_50 = EMAIndicator(df["close"], window=50)
        indicators["ema_20"] = ema_20.ema_indicator().iloc[-1]
        indicators["ema_50"] = ema_50.ema_indicator().iloc[-1]

        # Stochastic RSI
        stoch_rsi = StochRSIIndicator(df["high"], df["low"], df["close"])
        indicators["stoch_rsi"] = stoch_rsi.stochrsi().iloc[-1]
        indicators["stoch_rsi_k"] = stoch_rsi.stochrsi_k().iloc[-1]
        indicators["stoch_rsi_d"] = stoch_rsi.stochrsi_d().iloc[-1]

        # ATR
        atr = AverageTrueRange(df["high"], df["low"], df["close"], window=14)
        indicators["atr"] = atr.average_true_range().iloc[-1]

        # PSAR
        psar = PSARIndicator(df["high"], df["low"], df["close"])
        indicators["psar"] = psar.psar().iloc[-1]

        return indicators

    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return {}


def save_to_redis(symbol: str, timeframe: str, indicators: Dict[str, Any]):
    """Save indicators to Redis"""
    try:
        r = get_redis_manager()

        key = f"indicators:{symbol}:{timeframe}"
        data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": int(datetime.now(datetime.UTC).timestamp()),
            "indicators": indicators,
        }

        r.set(key, json.dumps(data), ex=3600)  # Expire in 1 hour
        logger.info(f"✅ {symbol} {timeframe} indicators saved to Redis")

    except Exception as e:
        logger.error(f"Error saving to Redis: {e}")


def save_to_disk(symbol: str, timeframe: str, indicators: Dict[str, Any]):
    """Save indicators to disk"""
    try:
        snapshot_dir = SNAPSHOTS_BASE / datetime.now(datetime.UTC).strftime("%Y-%m-%d")
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        file_path = snapshot_dir / f"{symbol}_{timeframe}_indicators.json"

        data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": int(datetime.now(datetime.UTC).timestamp()),
            "indicators": indicators,
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"✅ {symbol} {timeframe} indicators saved to disk")

    except Exception as e:
        logger.error(f"Error saving to disk: {e}")


def run_indicator_cycle():
    """Run a single indicator calculation cycle"""
    logger.info("🚀 Starting indicator calculation cycle")

    symbols = load_symbols()
    if not symbols:
        logger.warning("No symbols found, skipping indicator calculation")
        return

    successful = 0
    failed = 0

    for symbol in symbols:
        full_symbol = symbol.upper() + "USDT"

        for timeframe in TIMEFRAMES:
            try:
                # Get kline data
                df = get_klines(full_symbol, timeframe, KLINE_LIMIT)
                if df is None or df.empty:
                    logger.warning(f"No data for {full_symbol} {timeframe}")
                    failed += 1
                    continue

                # Calculate indicators
                indicators = calculate_indicators(df)
                if not indicators:
                    logger.warning(
                        f"No indicators calculated for {full_symbol} {timeframe}"
                    )
                    failed += 1
                    continue

                # Save to Redis and disk
                save_to_redis(symbol, timeframe, indicators)
                save_to_disk(symbol, timeframe, indicators)

                successful += 1

            except Exception as e:
                logger.error(f"Error processing {full_symbol} {timeframe}: {e}")
                failed += 1

    logger.info(f"🎉 Indicator cycle complete: {successful} successful, {failed} failed")
    return {"successful": successful, "failed": failed}


def main():
    """Main entry point"""
    try:
        results = run_indicator_cycle()
        logger.info(f"Results: {results}")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
