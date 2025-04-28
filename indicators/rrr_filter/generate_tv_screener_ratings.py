#!/usr/bin/env python3
import os
import json
import glob
import numpy as np
from pathlib import Path
from datetime import datetime
from utils.path_utils import load_paths

# === Config ===
paths = load_paths()
SNAPSHOT_DIR = paths["snapshots_path"]
TV_HISTORY_DIR = paths["tv_history_path"]
TARGET_TIMEFRAME = "15m"

# === Prepare paths ===
today = datetime.utcnow().strftime("%Y-%m-%d")
snapshot_path = os.path.join(SNAPSHOT_DIR, today)
tv_day_folder = os.path.join(TV_HISTORY_DIR, today)
os.makedirs(tv_day_folder, exist_ok=True)
OUTPUT_FILE = os.path.join(tv_day_folder, "tv_screener_raw_dict.txt")

# === Helper Functions ===
def load_klines(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def compute_tv_rating(klines):
    closes = [float(k[4]) for k in klines[-50:]]
    highs = [float(k[2]) for k in klines[-50:]]
    lows = [float(k[3]) for k in klines[-50:]]

    if len(closes) < 14:
        return "neutral"

    # RSI
    deltas = np.diff(closes)
    seed = deltas[:14]
    up = seed[seed >= 0].sum() / 14
    down = -seed[seed < 0].sum() / 14
    rs = up / down if down != 0 else 0
    rsi = 100 - 100 / (1 + rs)

    # MACD (simplified)
    ema_12 = np.mean(closes[-12:])
    ema_26 = np.mean(closes[-26:])
    macd = ema_12 - ema_26
    macd_signal = np.mean([ema_12 - ema_26 for _ in range(9)])
    macd_hist = macd - macd_signal

    # ADX (simplified)
    tr = [max(h - l, abs(h - c), abs(l - c)) for h, l, c in zip(highs, lows, closes)]
    atr = np.mean(tr)
    adx = min(100, 100 * atr / closes[-1])

    # EMA Trend
    ema_10 = np.mean(closes[-10:])
    ema_50 = np.mean(closes[-50:])
    bullish_trend = ema_10 > ema_50

    # === Score ===
    score = 0
    if rsi > 60: score += 1
    if macd_hist > 0: score += 1
    if adx > 20: score += 1
    if bullish_trend: score += 1

    if score >= 3:
        return "strong_buy"
    elif score == 2:
        return "buy"
    elif score == 1:
        return "neutral"
    else:
        return "sell"

# === Main Logic ===
files = glob.glob(f"{snapshot_path}/*_{TARGET_TIMEFRAME}_klines.json")

tv_dict = {}

for file_path in files:
    symbol = Path(file_path).stem.replace(f"_{TARGET_TIMEFRAME}_klines", "")
    try:
        klines = load_klines(file_path)
        rating = compute_tv_rating(klines)
        tv_dict[symbol.upper()] = {TARGET_TIMEFRAME: rating}
    except Exception as e:
        print(f"⚠️ Error processing {symbol}: {e}")

# Save output
with open(OUTPUT_FILE, "w") as f:
    json.dump(tv_dict, f, indent=2)

print(f"✅ Screener output written to {OUTPUT_FILE}")
