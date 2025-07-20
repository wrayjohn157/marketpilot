#!/usr/bin/env python3
import os
import json
import yaml
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from ta.trend import MACD
from ta.momentum import RSIIndicator

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAFU_CONFIG_PATH = BASE_DIR / "config" / "fork_safu_config.yaml"
SNAPSHOT_BASE = BASE_DIR / "data" / "snapshots"
MODEL_PATH = BASE_DIR / "ml" / "models" / "safu_exit_model.pkl"

# === Load config ===
with open(SAFU_CONFIG_PATH) as f:
    safu_cfg = yaml.safe_load(f)
WEIGHTS = safu_cfg.get("weights", {})
MIN_SCORE = safu_cfg.get("min_score", 0.4)

# === Logging ===
logger = logging.getLogger("safu_eval")
logger.setLevel(logging.INFO)


def load_indicators_from_disk(symbol: str, tf: str = "15m") -> dict:
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = SNAPSHOT_BASE / date_str / f"{symbol}_{tf}_klines.json"
    if not path.exists():
        logger.warning(f"[SAFU] Kline file not found: {path}")
        return {}

    try:
        with open(path) as f:
            raw = json.load(f)

        df = pd.DataFrame(
            raw,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "num_trades",
                "taker_base_volume",
                "taker_quote_volume",
                "ignore",
            ],
        )
        df = df.astype(
            {
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
            }
        )
        if len(df) < 50:
            return {}

        macd = MACD(df["close"])
        rsi = RSIIndicator(df["close"])

        volume_ma = df["volume"].rolling(20).mean()
        volume_change = (
            (df["volume"].iloc[-1] - volume_ma.iloc[-1]) / volume_ma.iloc[-1] * 100
        )

        return {
            "MACD_diff": macd.macd_diff().iloc[-1],
            "RSI14": rsi.rsi().iloc[-1],
            "VWAP": (df["volume"] * df["close"]).cumsum().iloc[-1]
            / df["volume"].cumsum().iloc[-1],
            "volume_drop_pct": max(0.0, -volume_change),
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
        if (
            indicators.get("volume_drop_pct") is not None
            and indicators["volume_drop_pct"] > 20
        ):
            score -= WEIGHTS.get("token_volume_drop", 0)
        if price_pct < -6:
            score -= WEIGHTS.get("drawdown_gt_6", 0)
        if price_pct < -7:
            score -= WEIGHTS.get("drawdown_gt_7", 0)
    except Exception as e:
        logger.warning(f"[SAFU] Scoring error for {symbol}: {e}")
        return 0.0

    return round(max(0.0, score), 3)


def load_safu_exit_model(model_path=MODEL_PATH):
    if not os.path.exists(model_path):
        print(f"⚠️ SAFU model not found at {model_path}")
        return None
    return joblib.load(model_path)


def get_safu_exit_decision(trade, config, model=None):
    """
    Evaluate whether a trade should be exited using traditional SAFU and/or ML classifier.

    Returns a tuple:
    (should_exit: bool, exit_reason: str, ml_exit_prob: float or None)
    """
    safu_score = trade.get("safu_score")
    drawdown = trade.get("drawdown_pct")
    tp1_shift = trade.get("tp1_shift")
    confidence_score = trade.get("confidence_score")
    recovery_odds = trade.get("recovery_odds")
    symbol = trade.get("symbol", "unknown")

    should_exit_safu = safu_score is not None and safu_score < config.get(
        "safu_threshold", 0.5
    )
    exit_reason = "safu_score_below_threshold" if should_exit_safu else None

    formatted_score = f"{safu_score:.2f}" if safu_score is not None else "N/A"
    print(
        f"\n📉 [SAFU Check] {symbol} | Score: {formatted_score} | Threshold: {config.get('safu_threshold', 0.5)} → {'❌ Exit' if should_exit_safu else '✅ Pass'}"
    )

    use_ml = config.get("use_safu_exit_model", False)
    ml_exit_prob = None
    should_exit_ml = False

    if use_ml and model:
        try:
            features = np.array(
                [
                    [
                        safu_score or 0.0,
                        drawdown or 0.0,
                        tp1_shift or 0.0,
                        trade.get("be_improvement", 0.0),
                        confidence_score or 0.0,
                        recovery_odds or 0.0,
                        trade.get("entry_score", 0.0),
                        trade.get("current_score", 0.0),
                        trade.get("macd_histogram", 0.0),
                        trade.get("rsi", 0.0),
                        trade.get("adx", 0.0),
                    ]
                ]
            )
            ml_exit_prob = model.predict_proba(features)[0][1]
            should_exit_ml = ml_exit_prob > config.get("ml_exit_threshold", 0.6)

            print(
                f"🤖 [ML Check] {symbol} | Exit Prob: {ml_exit_prob:.3f} | Threshold: {config.get('ml_exit_threshold', 0.6)} → {'❌ Exit' if should_exit_ml else '✅ Pass'}"
            )

        except Exception as e:
            print(f"⚠️ SAFU model inference failed: {e}")

    enforce_mode = config.get("enforce_if", "both")
    final_exit = False

    if enforce_mode == "ml_only":
        final_exit = should_exit_ml
        exit_reason = "ml_exit" if should_exit_ml else None
    elif enforce_mode == "score_only":
        final_exit = should_exit_safu
    else:
        final_exit = should_exit_safu or should_exit_ml
        if should_exit_ml:
            exit_reason = "ml_exit"
        elif should_exit_safu:
            exit_reason = "safu_score_below_threshold"

    print(
        f"🧠 [SAFU Decision] Mode: {enforce_mode} → Final Decision: {'❌ Reject Trade' if final_exit else '✅ Keep Trade'} | Reason: {exit_reason}"
    )

    return final_exit, exit_reason, ml_exit_prob
