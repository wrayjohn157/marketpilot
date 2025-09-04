#!/usr/bin/env python3
"""
Unified Indicator System - Fixes all indicator calculation and usage issues
Provides consistent, accurate, and validated indicator calculations across all timeframes
"""

import json
import logging
import redis
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np

# Technical Analysis
import ta
from ta.momentum import RSIIndicator, StochRSIIndicator, ROCIndicator
from ta.trend import EMAIndicator, ADXIndicator, MACD, PSARIndicator, IchimokuIndicator
from ta.volatility import AverageTrueRange, BollingerBands, KeltnerChannel
from ta.volume import VolumeSMAIndicator, VolumePriceTrendIndicator
from ta.others import DailyReturnIndicator

from config.config_loader import PATHS


class Timeframe(Enum):
    """Standardized timeframes for different purposes"""
    TREND = "1h"        # For trend analysis
    ENTRY = "15m"       # For entry signals
    VOLUME = "15m"      # For volume analysis
    LONG_TERM = "4h"    # For long-term analysis


class IndicatorType(Enum):
    """Indicator categories for proper usage"""
    TREND = "trend"         # MACD, ADX, EMA, QQE
    MOMENTUM = "momentum"   # RSI, StochRSI, ROC
    VOLATILITY = "volatility"  # ATR, Bollinger Bands
    VOLUME = "volume"       # Volume indicators
    SUPPORT_RESISTANCE = "support_resistance"  # Pivot points, levels


@dataclass
class IndicatorConfig:
    """Configuration for indicator calculation"""
    timeframe: Timeframe
    indicator_type: IndicatorType
    period: int
    validation_range: Tuple[float, float]
    description: str


@dataclass
class IndicatorResult:
    """Result of indicator calculation with validation"""
    value: float
    is_valid: bool
    confidence: float
    timestamp: datetime
    timeframe: Timeframe
    indicator_type: IndicatorType


class IndicatorValidator:
    """Comprehensive validation for all indicators"""
    
    @staticmethod
    def validate_rsi(rsi: float) -> Tuple[bool, float]:
        """Validate RSI value and return confidence"""
        if not (0 <= rsi <= 100):
            return False, 0.0
        
        # Higher confidence for extreme values
        if rsi < 20 or rsi > 80:
            return True, 0.9
        elif rsi < 30 or rsi > 70:
            return True, 0.7
        else:
            return True, 0.5
    
    @staticmethod
    def validate_macd(macd: float, signal: float, histogram: float) -> Tuple[bool, float]:
        """Validate MACD values and return confidence"""
        if abs(macd - signal) > 10:  # Unrealistic difference
            return False, 0.0
        
        # Higher confidence for strong signals
        if abs(histogram) > 0.01:
            return True, 0.8
        else:
            return True, 0.6
    
    @staticmethod
    def validate_adx(adx: float) -> Tuple[bool, float]:
        """Validate ADX value and return confidence"""
        if not (0 <= adx <= 100):
            return False, 0.0
        
        # Higher confidence for strong trends
        if adx > 50:
            return True, 0.9
        elif adx > 25:
            return True, 0.7
        else:
            return True, 0.5
    
    @staticmethod
    def validate_stoch_rsi(k: float, d: float) -> Tuple[bool, float]:
        """Validate Stochastic RSI values and return confidence"""
        if not (0 <= k <= 100) or not (0 <= d <= 100):
            return False, 0.0
        
        # Higher confidence for extreme values
        if k < 20 or k > 80:
            return True, 0.8
        else:
            return True, 0.6
    
    @staticmethod
    def validate_ema(ema: float, price: float) -> Tuple[bool, float]:
        """Validate EMA value and return confidence"""
        if ema <= 0 or price <= 0:
            return False, 0.0
        
        # Higher confidence when EMA is close to price
        deviation = abs(ema - price) / price
        if deviation < 0.05:  # Within 5%
            return True, 0.9
        elif deviation < 0.1:  # Within 10%
            return True, 0.7
        else:
            return True, 0.5


class IndicatorCalculator:
    """Unified indicator calculation with proper error handling"""
    
    def __init__(self):
        self.validator = IndicatorValidator()
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
    
    def fetch_klines(self, symbol: str, interval: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch klines from Binance with error handling"""
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "num_trades",
                "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
            ])
            
            # Convert to numeric
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            if len(df) < 50:  # Need minimum data for indicators
                return None
            
            return df
            
        except Exception as e:
            logging.error(f"Failed to fetch klines for {symbol} {interval}: {e}")
            return None
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> IndicatorResult:
        """Calculate RSI with proper validation"""
        try:
            rsi_indicator = RSIIndicator(close=df["close"], window=period)
            rsi_value = rsi_indicator.rsi().iloc[-1]
            
            is_valid, confidence = self.validator.validate_rsi(rsi_value)
            
            return IndicatorResult(
                value=rsi_value,
                is_valid=is_valid,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.ENTRY,
                indicator_type=IndicatorType.MOMENTUM
            )
        except Exception as e:
            logging.error(f"Failed to calculate RSI: {e}")
            return IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.ENTRY, IndicatorType.MOMENTUM)
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, IndicatorResult]:
        """Calculate MACD with proper validation"""
        try:
            macd_indicator = MACD(close=df["close"], window_fast=fast, window_slow=slow, window_sign=signal)
            
            macd_line = macd_indicator.macd().iloc[-1]
            signal_line = macd_indicator.macd_signal().iloc[-1]
            histogram = macd_indicator.macd_diff().iloc[-1]
            histogram_prev = macd_indicator.macd_diff().iloc[-2]
            
            is_valid, confidence = self.validator.validate_macd(macd_line, signal_line, histogram)
            
            return {
                "MACD": IndicatorResult(macd_line, is_valid, confidence, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND),
                "MACD_signal": IndicatorResult(signal_line, is_valid, confidence, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND),
                "MACD_Histogram": IndicatorResult(histogram, is_valid, confidence, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND),
                "MACD_Histogram_Prev": IndicatorResult(histogram_prev, is_valid, confidence, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND)
            }
        except Exception as e:
            logging.error(f"Failed to calculate MACD: {e}")
            return {
                "MACD": IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND),
                "MACD_signal": IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND),
                "MACD_Histogram": IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND),
                "MACD_Histogram_Prev": IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND)
            }
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> IndicatorResult:
        """Calculate ADX with proper validation"""
        try:
            adx_indicator = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=period)
            adx_value = adx_indicator.adx().iloc[-1]
            
            is_valid, confidence = self.validator.validate_adx(adx_value)
            
            return IndicatorResult(
                value=adx_value,
                is_valid=is_valid,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.TREND,
                indicator_type=IndicatorType.TREND
            )
        except Exception as e:
            logging.error(f"Failed to calculate ADX: {e}")
            return IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND)
    
    def calculate_ema(self, df: pd.DataFrame, period: int) -> IndicatorResult:
        """Calculate EMA with proper validation"""
        try:
            ema_indicator = EMAIndicator(close=df["close"], window=period)
            ema_value = ema_indicator.ema_indicator().iloc[-1]
            price = df["close"].iloc[-1]
            
            is_valid, confidence = self.validator.validate_ema(ema_value, price)
            
            return IndicatorResult(
                value=ema_value,
                is_valid=is_valid,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.TREND,
                indicator_type=IndicatorType.TREND
            )
        except Exception as e:
            logging.error(f"Failed to calculate EMA({period}): {e}")
            return IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND)
    
    def calculate_stoch_rsi(self, df: pd.DataFrame, window: int = 14, smooth1: int = 3, smooth2: int = 3) -> Dict[str, IndicatorResult]:
        """Calculate Stochastic RSI with proper validation"""
        try:
            stoch_rsi_indicator = StochRSIIndicator(close=df["close"], window=window, smooth1=smooth1, smooth2=smooth2)
            
            k_value = stoch_rsi_indicator.stochrsi_k().iloc[-1]
            d_value = stoch_rsi_indicator.stochrsi_d().iloc[-1]
            
            is_valid_k, confidence_k = self.validator.validate_stoch_rsi(k_value, d_value)
            is_valid_d, confidence_d = self.validator.validate_stoch_rsi(d_value, k_value)
            
            return {
                "StochRSI_K": IndicatorResult(k_value, is_valid_k, confidence_k, datetime.now(timezone.utc), Timeframe.ENTRY, IndicatorType.MOMENTUM),
                "StochRSI_D": IndicatorResult(d_value, is_valid_d, confidence_d, datetime.now(timezone.utc), Timeframe.ENTRY, IndicatorType.MOMENTUM)
            }
        except Exception as e:
            logging.error(f"Failed to calculate StochRSI: {e}")
            return {
                "StochRSI_K": IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.ENTRY, IndicatorType.MOMENTUM),
                "StochRSI_D": IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.ENTRY, IndicatorType.MOMENTUM)
            }
    
    def calculate_qqe(self, df: pd.DataFrame, rsi_period: int = 14) -> IndicatorResult:
        """Calculate QQE (Quantitative Qualitative Estimation) with correct formula"""
        try:
            rsi_series = RSIIndicator(close=df["close"], window=rsi_period).rsi()
            smoothed_rsi = rsi_series.ewm(alpha=1/14, adjust=False).mean()
            atr_rsi = abs(rsi_series - smoothed_rsi).ewm(alpha=1/14, adjust=False).mean()
            qqe_value = smoothed_rsi.iloc[-1] + 4.236 * atr_rsi.iloc[-1]
            
            # QQE validation (typically ranges from 0 to 100)
            is_valid = 0 <= qqe_value <= 100
            confidence = 0.8 if is_valid else 0.0
            
            return IndicatorResult(
                value=qqe_value,
                is_valid=is_valid,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.TREND,
                indicator_type=IndicatorType.TREND
            )
        except Exception as e:
            logging.error(f"Failed to calculate QQE: {e}")
            return IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND)
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> IndicatorResult:
        """Calculate ATR with proper validation"""
        try:
            atr_indicator = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=period)
            atr_value = atr_indicator.average_true_range().iloc[-1]
            
            # ATR should be positive and reasonable
            is_valid = atr_value > 0 and atr_value < df["close"].iloc[-1] * 0.1  # Less than 10% of price
            confidence = 0.8 if is_valid else 0.0
            
            return IndicatorResult(
                value=atr_value,
                is_valid=is_valid,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.VOLUME,
                indicator_type=IndicatorType.VOLATILITY
            )
        except Exception as e:
            logging.error(f"Failed to calculate ATR: {e}")
            return IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.VOLUME, IndicatorType.VOLATILITY)
    
    def calculate_psar(self, df: pd.DataFrame, step: float = 0.02, max_step: float = 0.2) -> IndicatorResult:
        """Calculate PSAR with proper validation"""
        try:
            psar_indicator = PSARIndicator(high=df["high"], low=df["low"], close=df["close"], step=step, max_step=max_step)
            psar_value = psar_indicator.psar().iloc[-1]
            price = df["close"].iloc[-1]
            
            # PSAR should be close to price
            is_valid = abs(psar_value - price) / price < 0.2  # Within 20% of price
            confidence = 0.7 if is_valid else 0.0
            
            return IndicatorResult(
                value=psar_value,
                is_valid=is_valid,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.TREND,
                indicator_type=IndicatorType.TREND
            )
        except Exception as e:
            logging.error(f"Failed to calculate PSAR: {e}")
            return IndicatorResult(0.0, False, 0.0, datetime.now(timezone.utc), Timeframe.TREND, IndicatorType.TREND)


class UnifiedIndicatorManager:
    """Main class for unified indicator management"""
    
    def __init__(self):
        self.calculator = IndicatorCalculator()
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
    
    def get_trend_indicators(self, symbol: str) -> Dict[str, IndicatorResult]:
        """Get trend indicators from 1h timeframe"""
        df = self.calculator.fetch_klines(f"{symbol}USDT", "1h")
        if df is None:
            return {}
        
        indicators = {}
        
        # MACD (trend direction and momentum)
        macd_results = self.calculator.calculate_macd(df)
        indicators.update(macd_results)
        
        # ADX (trend strength)
        indicators["ADX14"] = self.calculator.calculate_adx(df)
        
        # EMA (trend direction)
        indicators["EMA50"] = self.calculator.calculate_ema(df, 50)
        indicators["EMA200"] = self.calculator.calculate_ema(df, 200)
        
        # QQE (trend momentum)
        indicators["QQE"] = self.calculator.calculate_qqe(df)
        
        # PSAR (trend direction)
        indicators["PSAR"] = self.calculator.calculate_psar(df)
        
        return indicators
    
    def get_entry_indicators(self, symbol: str) -> Dict[str, IndicatorResult]:
        """Get entry indicators from 15m timeframe"""
        df = self.calculator.fetch_klines(f"{symbol}USDT", "15m")
        if df is None:
            return {}
        
        indicators = {}
        
        # RSI (overbought/oversold)
        indicators["RSI14"] = self.calculator.calculate_rsi(df)
        
        # Stochastic RSI (entry timing)
        stoch_results = self.calculator.calculate_stoch_rsi(df)
        indicators.update(stoch_results)
        
        # ATR (volatility for position sizing)
        indicators["ATR"] = self.calculator.calculate_atr(df)
        
        return indicators
    
    def get_volume_indicators(self, symbol: str) -> Dict[str, IndicatorResult]:
        """Get volume indicators from 15m timeframe"""
        df = self.calculator.fetch_klines(f"{symbol}USDT", "15m")
        if df is None:
            return {}
        
        indicators = {}
        
        # Volume SMA
        try:
            volume_sma = VolumeSMAIndicator(close=df["close"], volume=df["volume"], window=9)
            volume_sma_value = volume_sma.volume_sma().iloc[-1]
            current_volume = df["volume"].iloc[-1]
            
            indicators["volume_sma9"] = IndicatorResult(
                value=volume_sma_value,
                is_valid=True,
                confidence=0.8,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.VOLUME,
                indicator_type=IndicatorType.VOLUME
            )
            
            # Volume ratio
            volume_ratio = current_volume / volume_sma_value if volume_sma_value > 0 else 1.0
            indicators["volume_ratio"] = IndicatorResult(
                value=volume_ratio,
                is_valid=True,
                confidence=0.8,
                timestamp=datetime.now(timezone.utc),
                timeframe=Timeframe.VOLUME,
                indicator_type=IndicatorType.VOLUME
            )
        except Exception as e:
            logging.error(f"Failed to calculate volume indicators: {e}")
        
        return indicators
    
    def get_all_indicators(self, symbol: str) -> Dict[str, IndicatorResult]:
        """Get all indicators for a symbol"""
        all_indicators = {}
        
        # Get trend indicators
        trend_indicators = self.get_trend_indicators(symbol)
        all_indicators.update(trend_indicators)
        
        # Get entry indicators
        entry_indicators = self.get_entry_indicators(symbol)
        all_indicators.update(entry_indicators)
        
        # Get volume indicators
        volume_indicators = self.get_volume_indicators(symbol)
        all_indicators.update(volume_indicators)
        
        return all_indicators
    
    def save_to_redis(self, symbol: str, indicators: Dict[str, IndicatorResult]):
        """Save indicators to Redis with proper formatting"""
        try:
            # Save trend indicators (1h)
            trend_data = {}
            for name, result in indicators.items():
                if result.timeframe == Timeframe.TREND:
                    trend_data[name] = result.value
            
            if trend_data:
                self.redis.set(f"{symbol.upper()}_1h", json.dumps(trend_data))
            
            # Save entry indicators (15m)
            entry_data = {}
            for name, result in indicators.items():
                if result.timeframe == Timeframe.ENTRY:
                    entry_data[name] = result.value
            
            if entry_data:
                self.redis.set(f"{symbol.upper()}_15m", json.dumps(entry_data))
            
            # Save individual indicators for quick access
            for name, result in indicators.items():
                if result.is_valid:
                    self.redis.set(f"{symbol.upper()}_{result.timeframe.value}_{name}", result.value)
            
        except Exception as e:
            logging.error(f"Failed to save indicators to Redis: {e}")
    
    def get_indicator_quality_report(self, symbol: str) -> Dict[str, Any]:
        """Get quality report for all indicators"""
        indicators = self.get_all_indicators(symbol)
        
        total_indicators = len(indicators)
        valid_indicators = sum(1 for result in indicators.values() if result.is_valid)
        avg_confidence = np.mean([result.confidence for result in indicators.values() if result.is_valid])
        
        return {
            "symbol": symbol,
            "total_indicators": total_indicators,
            "valid_indicators": valid_indicators,
            "invalid_indicators": total_indicators - valid_indicators,
            "validity_rate": valid_indicators / total_indicators if total_indicators > 0 else 0,
            "average_confidence": avg_confidence,
            "quality_score": (valid_indicators / total_indicators) * avg_confidence if total_indicators > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    manager = UnifiedIndicatorManager()
    
    # Get all indicators for BTC
    indicators = manager.get_all_indicators("BTC")
    
    # Print results
    for name, result in indicators.items():
        status = "✅" if result.is_valid else "❌"
        print(f"{status} {name}: {result.value:.4f} (confidence: {result.confidence:.2f})")
    
    # Get quality report
    quality_report = manager.get_indicator_quality_report("BTC")
    print(f"\nQuality Report: {quality_report}")