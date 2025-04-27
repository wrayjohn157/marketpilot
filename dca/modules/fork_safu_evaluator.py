#!/usr/bin/env python3
import json
import yaml
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from ta.trend import MACD
from ta.momentum import RSIIndicator

# === Paths ===
SAFU_CONFIG_PATH = Path("/home/signal/market6/config/fork_safu_config.yaml")
SNAPSHOT_BASE = Path("/home/signal/market6/data/snapshots")

# === Load config ===
with open(SAFU_CONFIG_PATH) as f:
    safu_cfg = yaml.safe_load(f)
WEIGHTS = safu_cfg.get("weights", {})
MIN_SCORE = safu_cfg.get("min_score", 0.4)

# === Logging ===
logger = logging.getLogger("safu_eval")
logger.setLevel(logging.INFO)

def load_indicators_from_disk(symbol, tf="15m"):
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = SNAPSHOT_BASE / date_str / f"{symbol}_{tf}_klines.json"
    if not path.exists():
        logger.warning(f"[SAFU] Kline file not found: {path}")
        return {}

    try:
        with open(path) as f:
            raw = json.load(f)

        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_base_volume", "taker_quote_volume", "ignore"
        ])
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        if len(df) < 50:
            return {}

        macd = MACD(df["close"])
        rsi = RSIIndicator(df["close"])

        volume_ma = df["volume"].rolling(20).mean()
        volume_change = (df["volume"].iloc[-1] - volume_ma.iloc[-1]) / volume_ma.iloc[-1] * 100

        return {
            "MACD_diff": macd.macd_diff().iloc[-1],
            "RSI14": rsi.rsi().iloc[-1],
            "VWAP": (df["volume"] * df["close"]).cumsum().iloc[-1] / df["volume"].cumsum().iloc[-1],
            "volume_drop_pct": max(0.0, -volume_change)
        }

    except Exception as e:
        logger.warning(f"[SAFU] Error loading indicators from disk for {symbol}: {e}")
        return {}

def get_safu_score(symbol: str, entry_price: float, current_price: float) -> float:
    if entry_price == 0 or current_price == 0:
        return 0.0

    price_pct = (current_price - entry_price) / entry_price * 100
    indicators = load_indicators_from_disk(symbol)

    if not indicators:
        return 0.0

    score = 1.0
    try:
        if indicators.get("RSI14") is not None and indicators["RSI14"] < 35:
            score -= WEIGHTS.get("token_rsi_below_35", 0)
        if indicators.get("MACD_diff") is not None and indicators["MACD_diff"] < 0:
            score -= WEIGHTS.get("token_macd_bearish", 0)
        if indicators.get("VWAP") is not None and current_price < indicators["VWAP"]:
            score -= WEIGHTS.get("token_price_below_vwap", 0)
        if indicators.get("volume_drop_pct") is not None and indicators["volume_drop_pct"] > 20:
            score -= WEIGHTS.get("token_volume_drop", 0)
        if price_pct < -6:
            score -= WEIGHTS.get("drawdown_gt_6", 0)
        if price_pct < -7:
            score -= WEIGHTS.get("drawdown_gt_7", 0)
    except Exception as e:
        logger.warning(f"[SAFU] Scoring error for {symbol}: {e}")
        return 0.0

    return round(max(0.0, score), 3)
