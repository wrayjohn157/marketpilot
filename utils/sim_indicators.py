from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging

import pandas as pd
import ta

# sim_indicators.py

import
 os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def load_klines_from_disk(symbol: str, tf: str, date_str: str) -> pd.DataFrame:
    filepath = f"/home/signal/market7/data/snapshots/{date_str}/{symbol}_{tf}_klines.json"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Snapshot file not found: {filepath}")
    
    with open(filepath, "r") as f:
        klines = json.load(f)

    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["open"] = pd.to_numeric(df["open"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    df["close"] = pd.to_numeric(df["close"])
    df["volume"] = pd.to_numeric(df["volume"])
    return df

def compute_ema(df: Any, period: Any = 50) -> Any:
    return ta.trend.EMAIndicator(close=df["close"], window=period).ema_indicator().iloc[-1]

def compute_rsi(df: Any, period: Any = 14) -> Any:
    return ta.momentum.RSIIndicator(close=df["close"], window=period).rsi().iloc[-1]

def compute_adx(df: Any, period: Any = 14) -> Any:
    return ta.trend.ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=period).adx().iloc[-1]

def compute_qqe(df: Any, rsi_period: Any = 14, smoothing: Any = 5) -> Any:
    rsi = ta.momentum.RSIIndicator(close=df["close"], window=rsi_period).rsi()
    return rsi.rolling(window=smoothing).mean().iloc[-1]

def compute_psar(df: Any, step: Any = 0.02, max_step: Any = 0.2) -> Any:
    return ta.trend.PSARIndicator(high=df["high"], low=df["low"], close=df["close"], step=step, max_step=max_step).psar().iloc[-1]

def compute_atr(df: Any, period: Any = 14) -> Any:
    return ta.volatility.AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=period).average_true_range().iloc[-1]

def compute_vwap(df: Any) -> Any:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol_price = (typical_price * df["volume"]).cumsum()
    cum_volume = df["volume"].cumsum()
    return (cum_vol_price / cum_volume).iloc[-1]

def compute_macd_full(df: Any, fast: Any = 12, slow: Any = 26, signal: Any = 9) -> Any:
    macd = ta.trend.MACD(close=df["close"], window_fast=fast, window_slow=slow, window_sign=signal)
    macd_line = macd.macd()
    signal_line = macd.macd_signal()
    hist = macd.macd_diff()
    return {
        "MACD": macd_line.iloc[-1],
        "MACD_signal": signal_line.iloc[-1],
        "MACD_lift": macd_line.iloc[-1] - macd_line.iloc[-2],
        "MACD_Histogram": hist.iloc[-1],
        "MACD_Histogram_Prev": hist.iloc[-2]
    }

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
    indicators.update(macd)

    try:
        stoch_rsi = ta.momentum.StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
        indicators["StochRSI_K"] = stoch_rsi.stochrsi_k().iloc[-1]
        indicators["StochRSI_D"] = stoch_rsi.stochrsi_d().iloc[-1]
    except Exception as e:
        logging.error(f"Error computing Stoch RSI: {e}")

    indicators["latest_close"] = df["close"].iloc[-1]
    return indicators
