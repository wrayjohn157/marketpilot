import logging
from typing import Any, Dict, List, Optional, Tuple, Union

#!/usr/bin/env python3
import pandas as pd
import requests
import ta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def fetch_binance_klines(
    symbol: Any = "BTCUSDT", interval: Any = "1h", limit: Any = 251
) -> Any:
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
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
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        return df
    except Exception as e:
        logging.error(f"Error fetching klines: {e}")
        return None


def compute_ema(df: Any, period: Any = 50) -> Any:
    try:
        ema_indicator = ta.trend.EMAIndicator(close=df["close"], window=period)
        return ema_indicator.ema_indicator().iloc[-1]
    except Exception as e:
        logging.error(f"Error computing EMA({period}): {e}")
        return None


def compute_rsi(df: Any, period: Any = 14) -> Any:
    try:
        rsi_indicator = ta.momentum.RSIIndicator(close=df["close"], window=period)
        return rsi_indicator.rsi().iloc[-1]
    except Exception as e:
        logging.error(f"Error computing RSI({period}): {e}")
        return None


def compute_adx(df: Any, period: Any = 14) -> Any:
    try:
        adx_indicator = ta.trend.ADXIndicator(
            high=df["high"], low=df["low"], close=df["close"], window=period
        )
        return adx_indicator.adx().iloc[-1]
    except Exception as e:
        logging.error(f"Error computing ADX({period}): {e}")
        return None


def compute_qqe(df: Any, rsi_period: Any = 14, smoothing: Any = 5) -> Any:
    try:
        rsi_indicator = ta.momentum.RSIIndicator(close=df["close"], window=rsi_period)
        rsi = rsi_indicator.rsi()
        smoothed_rsi = rsi.rolling(window=smoothing).mean()
        return smoothed_rsi.iloc[-1]
    except Exception as e:
        logging.error(f"Error computing QQE: {e}")
        return None


def compute_psar(df: Any, step: Any = 0.02, max_step: Any = 0.2) -> Any:
    try:
        psar_indicator = ta.trend.PSARIndicator(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            step=step,
            max_step=max_step,
        )
        return psar_indicator.psar().iloc[-1]
    except Exception as e:
        logging.error(f"Error computing PSAR: {e}")
        return None


def compute_atr(df: Any, period: Any = 14) -> Any:
    try:
        atr_indicator = ta.volatility.AverageTrueRange(
            high=df["high"], low=df["low"], close=df["close"], window=period
        )
        return atr_indicator.average_true_range().iloc[-1]
    except Exception as e:
        logging.error(f"Error computing ATR({period}): {e}")
        return None


def compute_vwap(df: Any) -> Any:
    try:
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        cum_vol_price = (typical_price * df["volume"]).cumsum()
        cum_volume = df["volume"].cumsum()
        vwap_series = cum_vol_price / cum_volume
        return vwap_series.iloc[-1]
    except Exception as e:
        logging.error(f"Error computing VWAP: {e}")
        return None


def compute_macd_full(df: Any, fast: Any = 12, slow: Any = 26, signal: Any = 9) -> Any:
    try:
        macd_indicator = ta.trend.MACD(
            close=df["close"], window_fast=fast, window_slow=slow, window_sign=signal
        )
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()
        hist = macd_indicator.macd_diff()
        return {
            "MACD": macd_line.iloc[-1],
            "MACD_signal": signal_line.iloc[-1],
            "MACD_lift": macd_line.iloc[-1] - macd_line.iloc[-2],
            "MACD_Histogram": hist.iloc[-1],
            "MACD_Histogram_Prev": hist.iloc[-2],
        }
    except Exception as e:
        logging.error(f"Error computing MACD: {e}")
        return None


def compute_all_indicators(df: Any) -> Any:
    indicators = {}

    indicators["EMA50"] = compute_ema(df, 50)
    indicators["EMA200"] = compute_ema(df, 200)
    indicators["RSI14"] = compute_rsi(df, 14)
    indicators["ADX14"] = compute_adx(df, 14)
    indicators["QQE"] = compute_qqe(df)
    indicators["PSAR"] = compute_psar(df)
    indicators["ATR"] = compute_atr(df, 14)
    indicators["VWAP"] = compute_vwap(df)

    macd = compute_macd_full(df)
    if macd:
        indicators.update(macd)

    try:
        stoch_rsi = ta.momentum.StochRSIIndicator(
            df["close"], window=14, smooth1=3, smooth2=3
        )
        indicators["StochRSI_K"] = stoch_rsi.stochrsi_k().iloc[-1]
        indicators["StochRSI_D"] = stoch_rsi.stochrsi_d().iloc[-1]
    except Exception as e:
        logging.error(f"Error computing Stoch RSI: {e}")

    indicators["latest_close"] = df["close"].iloc[-1]
    return indicators


if __name__ == "__main__":
    df = fetch_binance_klines()
    if df is not None and not df.empty:
        indicators = compute_all_indicators(df)
        for key, value in indicators.items():
            logging.info(f"{key}: {value}")
