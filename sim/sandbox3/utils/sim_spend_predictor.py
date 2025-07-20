#!/usr/bin/env python3
"""
Sim utility to predict DCA spend volume using the trained XGBoost model.
Allows injection of model overrides for testing.
"""

import joblib
import pandas as pd
from pathlib import Path
import logging

# === Paths ===
BASE_DIR = Path(__file__).resolve().parents[3]  # /market7
MODEL_PATH = BASE_DIR / "ml" / "models" / "xgb_spend_model.pkl"

# === Configure logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sim_spend_predictor")

# === Load model ===
try:
    MODEL = joblib.load(str(MODEL_PATH))
    logger.info(f"🧠 Loaded spend model from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load spend model from {MODEL_PATH}: {e}")
    MODEL = None

# === Required Feature Set for Base Inputs (excluding one-hot btc_status)
BASE_FEATURES = [
    "entry_score", "current_score", "drawdown_pct", "safu_score", "macd_lift",
    "rsi", "rsi_slope", "adx", "tp1_shift", "recovery_odds", "confidence_score",
    "zombie_tagged", "btc_rsi", "btc_macd_histogram", "btc_adx"
]

# === One-hot Encoded btc_status Feature Keys
BTC_STATUS_KEYS = [
    "btc_status_bullish",
    "btc_status_bearish",
    "btc_status_neutral",
    "btc_status_nan"
]


def predict_sim_spend_volume(input_features: dict, model_override=None) -> float:
    """Sim version of spend prediction with optional model injection."""
    model = model_override or MODEL
    if model is None:
        logger.error("No spend model loaded; cannot predict volume.")
        return 0.0

    try:
        # Extract base features
        base_data = {key: input_features.get(key, 0.0) for key in BASE_FEATURES}

        # Map btc_status to one-hot fields
        btc_status = str(input_features.get("btc_status", "nan")).lower()
        btc_data = {
            "btc_status_bullish": int(btc_status == "bullish"),
            "btc_status_bearish": int(btc_status == "bearish"),
            "btc_status_neutral": int(btc_status == "neutral"),
            "btc_status_nan": int(btc_status not in {"bullish", "bearish", "neutral"}),
        }

        # Combine all features
        row = {**base_data, **btc_data}
        df = pd.DataFrame([row])

        pred = model.predict(df)[0]
        return float(pred)

    except Exception as e:
        logger.error(f"Sim spend prediction failed: {e}")
        return 0.0


def adjust_volume(
    predicted_volume: float,
    already_spent: float,
    max_budget: float = 2000.0,
    drawdown_pct: float = 0.0,
    tp1_shift_pct: float = 0.0
) -> float:
    """Adjust predicted DCA volume based on sanity checks and budget limits."""
    min_effective_dd_pct = 1.0     # Minimum drawdown %
    min_tp1_shift_pct = 1.0        # Minimum TP1 shift %
    max_ratio = 10.0               # Max times already spent

    remaining_budget = max(0.0, max_budget - already_spent)

    if drawdown_pct < min_effective_dd_pct:
        return 0.0
    if tp1_shift_pct < min_tp1_shift_pct:
        return 0.0

    spend_limit = already_spent * max_ratio
    capped_volume = min(predicted_volume, remaining_budget, spend_limit)

    return round(capped_volume, 2)
