#!/usr/bin/env python3
"""
time_ticker_utils.py

Utility module for timestamp parsing, ticker normalization,
and fuzzy BTC kline indicator lookup from kline-style indicator files.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === BTC Snapshot Fields ===
BTC_FIELDS = ["rsi", "macd_histogram", "adx", "vwap_signal", "market_condition"]

# Base folder for BTC snapshot/kline files.
# Ensure this points to your snapshots directory WITHOUT any extra folder like "BTCUSDT".
BTC_SNAPSHOT_BASE = Path("/home/signal/market6/data/snapshots")

# === Timestamp Utilities ===
def parse_timestamp(raw_value):
    """
    Convert raw timestamp (int, float, ISO string, or datetime) to a UTC-aware datetime.
    """
    if isinstance(raw_value, datetime):
        return raw_value if raw_value.tzinfo else raw_value.replace(tzinfo=timezone.utc)
    if isinstance(raw_value, (int, float)):
        if raw_value > 1e10:
            dt = datetime.utcfromtimestamp(raw_value / 1000)
        else:
            dt = datetime.utcfromtimestamp(raw_value)
        return dt.replace(tzinfo=timezone.utc)
    elif isinstance(raw_value, str):
        try:
            dt = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception as e:
            raise ValueError(f"Cannot parse timestamp string: {raw_value}") from e
    else:
        raise TypeError("Unsupported timestamp type.")

def to_iso(dt):
    """
    Convert datetime to ISO8601 UTC string with 'Z' suffix.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

def closest_timestamp(target, timestamps):
    """
    Return the datetime from the list that is closest to the target.
    """
    if not timestamps:
        return None
    return min(timestamps, key=lambda dt: abs(dt - target))

# === Ticker Normalization ===
def normalize_ticker(ticker):
    """
    Normalize ticker format: USDT_DOGE, DOGE_USDT -> DOGEUSDT.
    """
    if "_" in ticker:
        parts = ticker.split("_")
        if parts[0].upper() == "USDT":
            return parts[1].upper() + "USDT"
        elif parts[-1].upper() == "USDT":
            return "".join(parts).upper()
    return ticker.upper()

# === BTC Kline Loader ===
def load_btc_kline_data(date_str, timeframe="15m"):
    """
    Load BTC indicator snapshot from the snapshots folder.
    Expects the file to be named "BTC_15m.json" inside the folder for the given date.
    """
    snapshot_path = BTC_SNAPSHOT_BASE / date_str / f"BTC_{timeframe}.json"
    if not snapshot_path.exists():
        print(f"⚠️ BTC kline snapshot not found: {snapshot_path}")
        return None
    try:
        with open(snapshot_path, "r") as f:
            data = json.load(f)
            # If the file contains a dict (single snapshot), wrap it in a list.
            return [data] if isinstance(data, dict) else data
    except Exception as e:
        print(f"⚠️ Error reading BTC kline snapshot: {e}")
        return None

# === Fuzzy BTC Kline Matching ===
def fuzzy_btc_kline_match(target_ts, btc_data, max_diff_sec=1800):
    """
    Return BTC indicator block closest to the given target timestamp within max_diff_sec.
    Expects btc_data as a list of dicts, each with a "timestamp" field.
    """
    target_dt = parse_timestamp(target_ts)
    if not btc_data:
        return {k: "unknown" for k in BTC_FIELDS}
    best = None
    best_diff = timedelta(seconds=max_diff_sec)
    for entry in btc_data:
        ts = entry.get("timestamp")
        if not ts:
            continue
        try:
            entry_dt = parse_timestamp(ts)
        except Exception:
            continue
        diff = abs(target_dt - entry_dt)
        if diff < best_diff:
            best_diff = diff
            best = entry
    if best:
        return {
            "rsi": round(best.get("RSI14", 0), 2),
            "macd_histogram": round(best.get("MACD_Histogram", 0), 6),
            "adx": round(best.get("ADX14", 0), 2),
            "vwap_signal": best.get("vwap_signal", "unknown"),
            "market_condition": best.get("market_condition", "unknown")
        }
    return {k: "unknown" for k in BTC_FIELDS}

# === Self-test ===
if __name__ == "__main__":
    raw_ts = 1743903067
    iso_ts = "2025-04-06T01:31:07Z"
    dt = parse_timestamp(raw_ts)
    print("Parsed:", dt, "ISO:", to_iso(dt))
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    btc = load_btc_kline_data(today)
    if btc:
        result = fuzzy_btc_kline_match(iso_ts, btc)
        print("Closest BTC Kline Snapshot:", result)
