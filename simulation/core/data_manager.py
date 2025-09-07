#!/usr/bin/env python3

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import requests

from config.unified_config_manager import get_path

"""
Historical Data Manager for DCA Simulation
Loads and manages historical klines data for simulation purposes
"""

# === Logging ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """Manages historical klines data for DCA simulation"""

    def __init__(self):
        self.binance_base_url = "https://api.binance.com/api/v3"
        self.snapshots_dir = get_path("snapshots")
        self.cache_dir = Path("simulation/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_klines(
        self,
        symbol: str,
        timeframe: str,
        start_time: int,
        end_time: int,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Load historical klines data

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Timeframe ('15m', '1h', '4h', '1d')
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Try to load from cache first
            if use_cache:
                cached_data = self._load_from_cache(
                    symbol, timeframe, start_time, end_time
                )
                if cached_data is not None:
                    logger.info(
                        f"Loaded {len(cached_data)} candles from cache for {symbol} {timeframe}"
                    )
                    return cached_data

            # Load from Binance API
            logger.info(f"Loading klines from Binance API for {symbol} {timeframe}")
            klines = self._fetch_from_binance(symbol, timeframe, start_time, end_time)

            if klines.empty:
                raise ValueError(f"No data available for {symbol} {timeframe}")

            # Cache the data
            self._save_to_cache(klines, symbol, timeframe, start_time, end_time)

            logger.info(
                f"Successfully loaded {len(klines)} candles for {symbol} {timeframe}"
            )
            return klines

        except Exception as e:
            logger.error(f"Error loading klines for {symbol} {timeframe}: {e}")
            raise

    def _fetch_from_binance(
        self, symbol: str, timeframe: str, start_time: int, end_time: int
    ) -> pd.DataFrame:
        """Fetch klines data from Binance API"""
        url = f"{self.binance_base_url}/klines"
        params = {
            "symbol": symbol,
            "interval": timeframe,
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000,
        }

        all_klines = []
        current_start = start_time

        while current_start < end_time:
            params["startTime"] = current_start
            params["endTime"] = min(
                current_start + self._get_timeframe_ms(timeframe) * 1000, end_time
            )

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            klines = response.json()
            if not klines:
                break

            all_klines.extend(klines)
            current_start = klines[-1][6] + 1  # Next start time

            # Rate limiting
            time.sleep(0.1)

        if not all_klines:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(
            all_klines,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "num_trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )

        # Convert data types
        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_asset_volume",
        ]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

        # Remove duplicates and sort
        df = (
            df.drop_duplicates(subset=["timestamp"])
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        return df

    def _get_timeframe_ms(self, timeframe: str) -> int:
        """Convert timeframe to milliseconds"""
        timeframe_map = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
        }
        return timeframe_map.get(timeframe, 60 * 60 * 1000)

    def _load_from_cache(
        self, symbol: str, timeframe: str, start_time: int, end_time: int
    ) -> Optional[pd.DataFrame]:
        """Load data from cache if available"""
        cache_file = (
            self.cache_dir / f"{symbol}_{timeframe}_{start_time}_{end_time}.parquet"
        )
        if cache_file.exists():
            try:
                return pd.read_parquet(cache_file)
            except Exception as e:
                logger.warning(f"Error loading from cache: {e}")
        return None

    def _save_to_cache(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        start_time: int,
        end_time: int,
    ):
        """Save data to cache"""
        cache_file = (
            self.cache_dir / f"{symbol}_{timeframe}_{start_time}_{end_time}.parquet"
        )
        try:
            df.to_parquet(cache_file, index=False)
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")

    def get_available_symbols(self) -> List[str]:
        """Get list of available trading symbols"""
        try:
            response = requests.get(f"{self.binance_base_url}/exchangeInfo", timeout=10)
            response.raise_for_status()

            exchange_info = response.json()
            symbols = []
            for symbol_info in exchange_info["symbols"]:
                if symbol_info["status"] == "TRADING" and symbol_info[
                    "symbol"
                ].endswith("USDT"):
                    symbols.append(symbol_info["symbol"])

            return sorted(symbols)
        except Exception as e:
            logger.error(f"Error fetching available symbols: {e}")
            return []

    def get_available_timeframes(self) -> List[str]:
        """Get list of available timeframes"""
        return ["15m", "1h", "4h", "1d"]

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data quality and return metrics"""
        if df.empty:
            return {"valid": False, "reason": "Empty dataset"}

        # Check for missing values
        missing_values = df[["open", "high", "low", "close", "volume"]].isnull().sum()

        # Check for zero or negative prices
        invalid_prices = (df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()

        # Check for high-low consistency
        invalid_hl = (df["high"] < df["low"]).sum()

        # Check for open-close consistency
        invalid_oc = (df["open"] < 0).sum() + (df["close"] < 0).sum()

        quality_score = 1.0
        issues = []

        if missing_values.any():
            quality_score -= 0.3
            issues.append(f"Missing values: {missing_values.to_dict()}")

        if invalid_prices > 0:
            quality_score -= 0.4
            issues.append(f"Invalid prices: {invalid_prices} rows")

        if invalid_hl > 0:
            quality_score -= 0.2
            issues.append(f"High < Low: {invalid_hl} rows")

        if invalid_oc > 0:
            quality_score -= 0.1
            issues.append(f"Negative prices: {invalid_oc} rows")

        return {
            "valid": quality_score > 0.5,
            "quality_score": quality_score,
            "total_candles": len(df),
            "missing_values": missing_values.to_dict(),
            "invalid_prices": invalid_prices,
            "invalid_hl": invalid_hl,
            "issues": issues,
            "date_range": {
                "start": df["timestamp"].min().isoformat(),
                "end": df["timestamp"].max().isoformat(),
            },
        }

    def get_data_summary(
        self, symbol: str, timeframe: str, start_time: int, end_time: int
    ) -> Dict[str, Any]:
        """Get summary of available data for a symbol/timeframe"""
        try:
            # Load a small sample to check availability
            sample_end = (
                start_time + self._get_timeframe_ms(timeframe) * 10
            )  # 10 candles
            df = self.load_klines(
                symbol, timeframe, start_time, sample_end, use_cache=True
            )

            if df.empty:
                return {"available": False, "reason": "No data available"}

            # Get full range info
            full_df = self.load_klines(
                symbol, timeframe, start_time, end_time, use_cache=True
            )
            quality = self.validate_data_quality(full_df)

            return {
                "available": True,
                "total_candles": len(full_df),
                "quality": quality,
                "price_range": {
                    "min": full_df["low"].min(),
                    "max": full_df["high"].max(),
                    "avg": full_df["close"].mean(),
                },
                "volume_stats": {
                    "total": full_df["volume"].sum(),
                    "avg": full_df["volume"].mean(),
                    "max": full_df["volume"].max(),
                },
            }
        except Exception as e:
            return {"available": False, "reason": str(e)}
