from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
import os
import sys

import pandas as pd
import yaml

import re

#!/usr/bin/env python3
from ta.momentum import RSIIndicator, StochRSIIndicator
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


# === Setup ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# --- Load paths from config_loader ---

CONFIG_PATH = get_path("base") / "config" / "fork_score_config.yaml"
FORK_INPUT_FILE = get_path("fork_candidates")
OUTPUT_FILE = get_path("final_fork_rrr_trades")
BACKTEST_CANDIDATES_FILE = get_path("fork_backtest_candidates")
FORK_HISTORY_BASE = get_path("fork_history")
SNAPSHOT_BASE = get_path("snapshots")

REDIS_SET = "queues:fork_rrr_passed"
REDIS_FINAL_TRADES = "FORK_FINAL_TRADES"

from utils.redis_manager import get_redis_manager
from config.unified_config_manager import get_config
r = get_redis_manager()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Load config ===
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)
MIN_SCORE = config.get("min_score", 0.73)
WEIGHTS = config.get("weights", {})
OPTIONS = config.get("options", {})

def extract_float(val: Any) -> Any:
    if val is None:
        return 0.0
    s = str(val).strip().replace("'", "").replace('"', "")
    if s.lower() == "none":
        return 0.0
    try:
        s_clean = s.replace("np.float64(", "").replace(")", "")
        return float(s_clean)
    except:
        match = re.search(r"[-+]?\
d*\
.\
d+|\
d+", s)
        return float(match.group()) if match else 0.0

def btc_sentiment_multiplier() -> Any:
    price = extract_float(r.get_cache("indicators:BTC:1h:latest_close"))
    ema50 = extract_float(r.get_cache("indicators:BTC:1h:EMA50"))
    rsi = extract_float(r.get_cache("indicators:BTC:15m:RSI14"))
    adx = extract_float(r.get_cache("indicators:BTC:1h:ADX14"))
    mult = 1.0
    if price > ema50 and adx > 20:
        mult += 0.10
    elif price > ema50:
        mult += 0.05
    elif price < ema50 and adx > 15:
        mult -= 0.05
    if rsi < 35:
        mult -= 0.05
    return max(0.8, min(mult, 1.2))

def compute_stoch_slope(symbol: Any) -> Any:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filepath = SNAPSHOT_BASE / today / f"{symbol.upper()}_15m_klines.json"
    if not filepath.exists():
        return 0.0, None
    try:
        with open(filepath) as f:
            klines = json.load(f)
        closes = [float(k[4]) for k in klines][-30:]
        if len(closes) < 20:
            return 0.0, None
        df = pd.DataFrame({"close": closes})
        df["stoch_rsi_k"] = stochrsi(df["close"], window=14, smooth1=3, smooth2=3)
        k_vals = df["stoch_rsi_k"].dropna().tolist()
        if len(k_vals) >= 4:
            slope = k_vals[-1] - k_vals[-4]
            score = max(0.0, min(round(slope * 5, 4), 1.0))
            return score, round(slope, 6)
    except Exception as e:
        logging.warning(f"[WARN] Failed to compute stoch slope for {symbol}: {e}")
    return 0.0, None

def load_kline_volumes(symbol: Any) -> Any:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filepath = SNAPSHOT_BASE / today / f"{symbol.upper()}_15m_klines.json"
    if not filepath.exists():
        return None, None
    try:
        with open(filepath, "r") as f:
            klines = json.load(f)
        volumes = [float(c[5]) for c in klines[-9:]]
        if len(volumes) < 2:
            return None, None
        return volumes[-1], sum(volumes[:-1]) / (len(volumes) - 1)
    except:
        return None, None

def compute_subscores(symbol: Any) -> Any:
    data = r.get_cache(f"{symbol.upper()}_1h")
    data = json.loads(data) if data else {}

    price = extract_float(data.get("latest_close"))
    ema50 = extract_float(data.get("EMA50"))
    adx = extract_float(data.get("ADX14"))
    atr = extract_float(data.get("ATR"))
    macd = extract_float(data.get("MACD"))
    macd_signal = extract_float(data.get("MACD_signal"))
    macd_hist = extract_float(data.get("MACD_Histogram"))
    macd_hist_prev = extract_float(data.get("MACD_Histogram_Prev"))

    rsi = extract_float(r.get_cache(f"{symbol.upper()}_15m_RSI14"))
    k = extract_float(r.get_cache(f"{symbol.upper()}_15m_StochRSI_K"))
    d = extract_float(r.get_cache(f"{symbol.upper()}_15m_StochRSI_D"))

    current_vol = extract_float(r.get_cache(f"{symbol.upper()}_15m_volume"))
    sma9_vol = extract_float(r.get_cache(f"{symbol.upper()}_15m_volume_sma9"))
    if current_vol == 0 or sma9_vol == 0:
        current_vol, sma9_vol = load_kline_volumes(symbol)

    stoch_slope_score, stoch_raw_slope = compute_stoch_slope(symbol)

    mean_reversion_score = 1.0
    if price > ema50 and atr > 0:
        dist = (price - ema50) / atr
        if dist > 3:
            mean_reversion_score = 0.0
        elif dist > 2:
            mean_reversion_score = 0.25
        elif dist > 1.5:
            mean_reversion_score = 0.5

    macd_histogram_score = (
        1.0 if (macd > macd_signal and macd_hist > macd_hist_prev) else 0.0
    )
    if not OPTIONS.get("use_macd_bearish_check", True):
        macd_histogram_score = 0.0
    macd_bearish_cross = 1.0 if macd < macd_signal else 0.0
    stoch_ob_penalty = 0.0 if (k > 90 and d > 90) else 1.0
    if not OPTIONS.get("use_stoch_ob_penalty", True):
        stoch_ob_penalty = 0.0
    volume_penalty = (
        0.0 if (sma9_vol and current_vol and current_vol > sma9_vol * 2) else 1.0
    )
    if not OPTIONS.get("use_volume_penalty", True):
        volume_penalty = 0.0

    rsi_recovery = min(max((rsi - 30) / 20, 0), 1)
    stoch_rsi_cross = min(max((k - d) / 25, 0), 1) if (k > d and k < 80) else 0.0
    adx_rising = min(adx / 20, 1.0) if adx > 10 else 0.0
    ema_price_reclaim = 1.0 if price > ema50 else 0.0

    subscores = {
        "macd_histogram": macd_histogram_score,
        "macd_bearish_cross": macd_bearish_cross,
        "rsi_recovery": rsi_recovery,
        "stoch_rsi_cross": stoch_rsi_cross,
        "stoch_overbought_penalty": stoch_ob_penalty,
        "adx_rising": adx_rising,
        "ema_price_reclaim": ema_price_reclaim,
        "mean_reversion_score": mean_reversion_score,
        "volume_penalty": volume_penalty,
        "stoch_rsi_slope": stoch_slope_score,
    }

    base_score = sum(subscores[k] * WEIGHTS.get(k, 0) for k in subscores)
    mult = btc_sentiment_multiplier()
    adjusted = round(base_score * mult, 4)

    raw_indicators = {
        "price": price,
        "ema50": ema50,
        "adx": adx,
        "atr": atr,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "macd_hist_prev": macd_hist_prev,
        "rsi": rsi,
        "stoch_rsi_k": k,
        "stoch_rsi_d": d,
        "volume": current_vol,
        "volume_sma9": sma9_vol,
        "stoch_slope": stoch_raw_slope,
    }

    return adjusted, subscores, mult, raw_indicators

def write_to_history_log(entry: Any, date_str: Any) -> Any:
    path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\
n")

def main() -> Any:
    if not FORK_INPUT_FILE.exists():
        logging.error(f"Missing: {FORK_INPUT_FILE}")
        return

    with open(FORK_INPUT_FILE) as f:
        symbols = json.load(f)

    r.cleanup_expired_keys()
    r.cleanup_expired_keys()

    now = datetime.utcnow()
    now_ts = int(now.timestamp() * 1000)
    ts_iso = now.isoformat() + "Z"
    today = now.strftime("%Y-%m-%d")
    results, candidates = [], []

    for sym in symbols:
        score, subs, mult, raw_indicators = compute_subscores(sym)
        price = raw_indicators.get("price", 0.0)
        passed = score >= MIN_SCORE and (
            subs.get("rsi_recovery", 0) > 0 or subs.get("stoch_rsi_cross", 0) > 0
        )

        log = {
            "symbol": sym.upper(),
            "score": score,
            "timestamp": now_ts,
            "ts_iso": ts_iso,
            "score_hash": "_".join([f"{k}:{subs[k]}" for k in subs]),
            "score_components": subs,
            "btc_multiplier": mult,
            "entry_price": price, #"entry_price": extract_float(r.get_cache(f"{sym.upper()}_1h_latest_close")),
            "raw_indicators": raw_indicators,
            "passed": passed,
            "source": "fork_score_filter",
        }

        write_to_history_log(log, today)
        candidates.append(
            {
                "symbol": log["symbol"],
                "score": log["score"],
                "timestamp": log["timestamp"],
                "ts_iso": log["ts_iso"],
                "raw_indicators": log["raw_indicators"],
            }
        )

        if passed:
            trade = {
                "symbol": sym.upper(),
                "pair": f"{sym.upper()}_USDT",
                "score": score,
                "meta": subs,
                "score_hash": log["score_hash"],
                "timestamp": now_ts,
                "ts_iso": ts_iso,
            }
            r.store_trade_data({\
"symbol\
": sym})
            r.store_trade_data(trade)
            results.append(trade)

        verdict = "✅" if passed else "❌"
        log_lines = [
            f"{verdict} {sym.upper()} | Score: {score:.3f} | Mult: {mult:.2f}"
        ] + [
            f"    • {k.replace('_',' ').title():25}: {'✅' if subs[k] >= 1 else '❌' if subs[k] == 0 else f'{subs[k]:.3f}'}"
            for k in subs
        ]
        logging.info("\
n" + "\
n".join(log_lines))

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    with open(BACKTEST_CANDIDATES_FILE, "w") as f:
        json.dump(candidates, f, indent=2)

    logging.info(f"📂 Saved {len(results)} trades to {OUTPUT_FILE}")
    logging.info(f"📊 Backtest candidates saved to {BACKTEST_CANDIDATES_FILE}")

if __name__ == "__main__":
    main()
