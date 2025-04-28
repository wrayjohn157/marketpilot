#!/usr/bin/env python3
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging
import redis

# === Setup ===
logging.basicConfig(level=logging.INFO)
SAVE_BASE = Path(__file__).resolve().parent / "btc_logs"
SYMBOL = "BTCUSDT"
LIMIT = 250
INTERVAL_1H = "1h"
INTERVAL_15M = "15m"
BINANCE_URL_1H = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL_1H}&limit={LIMIT}"
BINANCE_URL_15M = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={INTERVAL_15M}&limit={LIMIT}"

# Initialize Redis connection
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# === Fetch Klines from Binance ===
def get_binance_klines(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"
        ])
        df["timestamp"] = df["open_time"] // 1000
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df
    except Exception as e:
        logging.error(f"[ERROR] Failed to fetch Binance klines: {e}")
        return None

# === Indicator Calculations ===
def compute_ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()

def compute_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd_histogram(df):
    ema_fast = df["close"].ewm(span=12, adjust=False).mean()
    ema_slow = df["close"].ewm(span=26, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line - signal_line

def compute_adx(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = np.maximum.reduce([tr1, tr2, tr3])
    tr_smooth = pd.Series(tr).rolling(window=period).mean()

    plus_di = 100 * pd.Series(plus_dm).rolling(window=period).sum() / tr_smooth
    minus_di = 100 * pd.Series(minus_dm).rolling(window=period).sum() / tr_smooth
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    return adx

def compute_vwap_signal(df):
    tp = (df["high"] + df["low"] + df["close"]) / 3
    vwap = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
    return "above" if df["close"].iloc[-1] > vwap.iloc[-1] else "below"

# === Market Classification Logic (optional for logging) ===
def determine_market_condition(ema50, ema200, rsi, macd_hist, adx, vwap_sig):
    adx_strong = 25
    rsi_bull = 55
    rsi_bear = 45

    if ema50 > ema200 and macd_hist > 0 and rsi > rsi_bull and adx > adx_strong:
        return "bullish"
    elif ema50 < ema200 and macd_hist < 0 and rsi < rsi_bear and adx > adx_strong:
        return "bearish"
    else:
        return "neutral"

# === Run + Save Snapshot & Push to Redis ===
def log_btc_snapshot():
    # Fetch 1-hour data
    df_1h = get_binance_klines(BINANCE_URL_1H)
    if df_1h is None or df_1h.empty:
        logging.error("No 1h BTC data available.")
        return
    # Fetch 15-minute data
    df_15m = get_binance_klines(BINANCE_URL_15M)
    if df_15m is None or df_15m.empty:
        logging.error("No 15m BTC data available.")
        return

    # Compute 1-hour indicators for price, EMA50, and ADX:
    latest_close_1h = df_1h["close"].iloc[-1]
    ema50_1h = compute_ema(df_1h, 50).iloc[-1]
    adx_1h = compute_adx(df_1h).iloc[-1]

    # Compute 15-minute indicator for RSI:
    rsi_15m = compute_rsi(df_15m).iloc[-1]
    
    # (Optional additional 15m indicators for logging)
    ema50_15m = compute_ema(df_15m, 50).iloc[-1]
    ema200_15m = compute_ema(df_15m, 200).iloc[-1]
    macd_hist_15m = compute_macd_histogram(df_15m).iloc[-1]
    adx_15m = compute_adx(df_15m).iloc[-1]
    vwap_sig_15m = compute_vwap_signal(df_15m)
    
    market_condition = determine_market_condition(ema50_15m, ema200_15m, rsi_15m, macd_hist_15m, adx_15m, vwap_sig_15m)
    
    # Prepare snapshot for file logging:
    ts = int(datetime.utcnow().timestamp())
    ts_iso = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")
    day = datetime.utcnow().strftime("%Y-%m-%d")
    folder = SAVE_BASE / day
    folder.mkdir(parents=True, exist_ok=True)
    
    snapshot = {
        "timestamp": ts,
        "ts_iso": ts_iso,
        "ema_50": round(ema50_15m, 2),
        "ema_200": round(ema200_15m, 2),
        "rsi": round(rsi_15m, 2),
        "macd_histogram": round(macd_hist_15m, 6),
        "adx": round(adx_15m, 2),
        "vwap_signal": vwap_sig_15m,
        "market_condition": market_condition
    }
    
    file_path = folder / "btc_snapshots.jsonl"
    with open(file_path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")
    
    # Push the required BTC indicators to Redis for fork_scorer:
    r.set("BTC_1h_latest_close", latest_close_1h)
    r.set("BTC_1h_EMA50", round(ema50_1h, 2))
    r.set("BTC_1h_ADX14", round(adx_1h, 2))
    r.set("BTC_15m_RSI14", round(rsi_15m, 2))
    
    print(f"✅ Logged BTC snapshot @ {ts_iso}")
    print(f"📁 Snapshot saved to: {file_path}")

if __name__ == "__main__":
    log_btc_snapshot()
