from datetime import datetime
from pathlib import Path
from typing import List, Dict
import json
import os

    from glob import glob
import math

SNAPSHOT_BASE = Path("/home/signal/market7/data/snapshots")

def sim_generate_snapshot_series(symbol: str, entry_time_ms: int, tf: str = "1h") -> List[dict]:

    def parse_kline_file(path):
        with open(path, "r") as f:
            raw_klines = json.load(f)
        result = []
        for k in raw_klines:
            if isinstance(k, list) and len(k) >= 5:
                result.append({
                    "timestamp": k[0],
                    "close": float(k[4]),
                    "rsi": 50,
                    "macd_histogram": 0,
                    "adx": 20,
                    "macd_lift": 0,
                    "rsi_slope": 0
                })
            elif isinstance(k, dict) and "timestamp" in k and "latest_close" in k:
                result.append({
                    "timestamp": k["timestamp"] * 1000 if k["timestamp"] < 1e12 else k["timestamp"],
                    "close": float(k["latest_close"]),
                    "rsi": k.get("RSI14", 50),
                    "macd_histogram": k.get("MACD_Histogram", 0),
                    "adx": k.get("ADX14", 20),
                    "macd_lift": k.get("MACD_lift", 0),
                    "rsi_slope": 0
                })
        return result

    def load_indicators(paths):
        combined = {}
        for path in paths:
            try:
                with open(path, "r") as f:
                    for line in f:
                        row = json.loads(line)
                        ts_raw = row["timestamp"]
                        ts_ms = ts_raw if ts_raw > 1e12 else ts_raw * 1000  # Detect seconds vs ms
                        if ts_ms not in combined or row.get("latest_close", 0) > combined[ts_ms].get("latest_close", 0):
                            combined[ts_ms] = row
            except:
                continue
        return combined

    # === Gather all folders from entry date forward ===
    entry_date = datetime.utcfromtimestamp(entry_time_ms / 1000).strftime("%Y-%m-%d")
    all_folders = sorted(p.name for p in SNAPSHOT_BASE.iterdir() if p.is_dir())
    selected_folders = [d for d in all_folders if d >= entry_date]

    klines = []
    indicator_paths = []
    for folder in selected_folders:
        k_path = SNAPSHOT_BASE / folder / f"{symbol}_{tf}_klines.json"
        i_path = SNAPSHOT_BASE / folder / f"{symbol}_{tf}.jsonl"
        if k_path.exists():
            klines += parse_kline_file(k_path)
        if i_path.exists():
            indicator_paths.append(i_path)

    # Filter to only timestamps at or after entry_time and remove duplicates
    dedup = {}
    for k in klines:
        ts = k["timestamp"]
        if ts >= entry_time_ms:
            dedup[ts] = k
    # Sort chronologically
    klines = [dedup[ts] for ts in sorted(dedup)]

    if not klines:
        raise ValueError("No valid klines found after entry time.")

    indicator_by_ts = load_indicators(indicator_paths)
    base_price = klines[0]["close"]
    entry_score = 0.75
    safu_score = 0.75
    snapshots = []

    for k in klines:
        ts_ms = k["timestamp"]
        price = k["close"]

        # Indicator alignment with grace
        GRACE_MS = 5 * 60 * 1000   # 5 minutes
        indicator_row = indicator_by_ts.get(ts_ms)
        if not indicator_row:
            ts_candidates = [ts for ts in indicator_by_ts if abs(ts - ts_ms) <= GRACE_MS]
            if ts_candidates:
                closest_ts = min(ts_candidates, key=lambda x: abs(x - ts_ms))
                indicator_row = indicator_by_ts.get(closest_ts)
            else:
                indicator_row = {}

        rsi = indicator_row.get("RSI14", k.get("rsi", 50))
        macd_hist = indicator_row.get("MACD_Histogram", k.get("macd_histogram", 0))
        adx = indicator_row.get("ADX14", k.get("adx", 20))
        macd_lift = indicator_row.get("MACD_lift", k.get("macd_lift", 0))
        rsi_slope = k.get("rsi_slope", 0)
        stoch_k = indicator_row.get("StochRSI_K", None)
        stoch_d = indicator_row.get("StochRSI_D", None)
        ema_50 = indicator_row.get("EMA50", None)
        ema_200 = indicator_row.get("EMA200", None)

        drawdown = max(0, (base_price - price) / base_price * 100)
        tp1_shift = round(1.5 + 0.5 * math.sin(ts_ms / 1e6), 2)
        be_improvement = round(0.1 + 0.05 * math.cos(ts_ms / 1e6), 2)
        recovery_odds = 0.85 if drawdown < 2 else 0.65
        confidence_score = 0.82 if drawdown < 2 else 0.6
        current_score = round(entry_score * (1 - 0.01 * drawdown), 4)

        snapshots.append({
            "timestamp": datetime.utcfromtimestamp(ts_ms / 1000).isoformat(),
            "symbol": symbol,
            "entry_score": entry_score,
            "current_score": current_score,
            "btc_status": "SAFE",
            "safu_score": safu_score,
            "tp1_shift": tp1_shift,
            "be_improvement": be_improvement,
            "recovery_odds": recovery_odds,
            "confidence_score": confidence_score,
            "rsi": rsi,
            "macd_histogram": macd_hist,
            "adx": adx,
            "macd_lift": macd_lift,
            "rsi_slope": rsi_slope,
            "drawdown_pct": drawdown,
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
            "ema_50": ema_50,
            "ema_200": ema_200,
        })

    return snapshots
