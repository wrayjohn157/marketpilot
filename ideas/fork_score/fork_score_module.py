# fork_score_module.py
import json
import logging
import re
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
from ta.momentum import stochrsi
from utils.redis_manager import get_redis_manager, RedisKeyManager


# === Setup ===
CONFIG_PATH = Path("/home/signal/market6/config/fork_score_config.yaml")
SNAPSHOT_BASE = Path("/home/signal/market6/data/snapshots")
r = get_redis_manager()

# === Utilities ===
def extract_float(val):
    if val is None: return 0.0
    s = str(val).strip().replace("'", "").replace('"', "")
    if s.lower() == "none": return 0.0
    try:
        s_clean = s.replace("np.float64(", "").replace(")", "")
        return float(s_clean)
    except:
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

def compute_stoch_slope(symbol):
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

def load_kline_volumes(symbol):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filepath = SNAPSHOT_BASE / today / f"{symbol.upper()}_15m_klines.json"
    if not filepath.exists(): return None, None
    try:
        with open(filepath) as f:
            klines = json.load(f)
        volumes = [float(c[5]) for c in klines[-9:]]
        return volumes[-1], sum(volumes[:-1]) / (len(volumes) - 1) if len(volumes) > 1 else (None, None)
    except: return None, None

def score_symbol(symbol: str, strat_config: dict):
    data = r.get_cache(f"{symbol.upper()}_1h")
    data = json.loads(data) if data else {}
    
    # === Extract indicators ===
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

    stoch_slope_score, _ = compute_stoch_slope(symbol)

    # === Scores ===
    weights = strat_config.get("weights", {})
    options = strat_config.get("options", {})

    mean_reversion_score = 1.0
    if price > ema50 and atr > 0:
        dist = (price - ema50) / atr
        if dist > 3: mean_reversion_score = 0.0
        elif dist > 2: mean_reversion_score = 0.25
        elif dist > 1.5: mean_reversion_score = 0.5

    macd_histogram_score = 1.0 if (macd > macd_signal and macd_hist > macd_hist_prev) else 0.0
    if not options.get("use_macd_bearish_check", True):
        macd_histogram_score = 0.0
    macd_bearish_cross = 1.0 if macd < macd_signal else 0.0
    stoch_ob_penalty = 0.0 if (k > 90 and d > 90) else 1.0
    if not options.get("use_stoch_ob_penalty", True):
        stoch_ob_penalty = 0.0
    volume_penalty = 0.0 if (sma9_vol and current_vol and current_vol > sma9_vol * 2) else 1.0
    if not options.get("use_volume_penalty", True):
        volume_penalty = 0.0

    rsi_recovery = min(max((rsi - 30) / 20, 0), 1)
    stoch_rsi_cross = min(max((k - d) / 25, 0), 1) if (k > d and k < 80) else 0.0
    adx_rising = min(adx / 20, 1.0) if adx > 10 else 0.0
    ema_price_reclaim = 1.0 if price > ema50 else 0.0

    components = {
        "macd_histogram": macd_histogram_score,
        "macd_bearish_cross": macd_bearish_cross,
        "rsi_recovery": rsi_recovery,
        "stoch_rsi_cross": stoch_rsi_cross,
        "stoch_overbought_penalty": stoch_ob_penalty,
        "adx_rising": adx_rising,
        "ema_price_reclaim": ema_price_reclaim,
        "mean_reversion_score": mean_reversion_score,
        "volume_penalty": volume_penalty,
        "stoch_rsi_slope": stoch_slope_score
    }

    raw_indicators = {
        "price": price, "ema50": ema50, "adx": adx, "atr": atr,
        "macd": macd, "macd_signal": macd_signal,
        "macd_hist": macd_hist, "macd_hist_prev": macd_hist_prev,
        "rsi": rsi, "stoch_rsi_k": k, "stoch_rsi_d": d,
        "volume": current_vol, "volume_sma9": sma9_vol
    }

    base_score = sum(components[k] * weights.get(k, 0) for k in components)
    final_score = round(base_score, 4)

    return {
        "symbol": symbol,
        "score": final_score,
        "components": components,
        "indicators": raw_indicators
    }
