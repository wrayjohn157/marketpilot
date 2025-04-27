#!/usr/bin/env python3
"""
Utility to predict DCA spend volume based on trained XGBoost model.
"""

import joblib
import pandas as pd
from pathlib import Path
import logging

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /market7
MODEL_PATH = BASE_DIR / "live" / "models" / "xgb_spend_model.pkl"

# === Configure logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("spend_predictor")

# === Load model ===
try:
    MODEL = joblib.load(str(MODEL_PATH))
    logger.info(f"🧠 Loaded spend model from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load spend model: {e}")
    MODEL = None

# === Required Features ===
FEATURES = [
    "entry_score", "current_score", "drawdown_pct", "safu_score", "macd_lift",
    "rsi", "rsi_slope", "adx", "tp1_shift", "recovery_odds", "confidence_score",
    "zombie_tagged", "btc_rsi", "btc_macd_histogram", "btc_adx", "btc_status"
]


def predict_spend_volume(input_features: dict) -> float:
    """Predict spend volume based on input feature dictionary."""
    if MODEL is None:
        logger.error("No spend model loaded; cannot predict volume.")
        return 0.0

    try:
        df = pd.DataFrame([{feat: input_features.get(feat, 0.0) for feat in FEATURES}])
        pred = MODEL.predict(df)[0]
        return float(pred)
    except Exception as e:
        logger.error(f"Spend prediction failed: {e}")
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
    min_tp1_shift_pct = 1.0         # Minimum TP1 shift %
    max_ratio = 10.0                # Max times already spent

    remaining_budget = max(0.0, max_budget - already_spent)

    if drawdown_pct < min_effective_dd_pct:
        return 0.0
    if tp1_shift_pct < min_tp1_shift_pct:
        return 0.0

    spend_limit = already_spent * max_ratio
    capped_volume = min(predicted_volume, remaining_budget, spend_limit)

    return round(capped_volume, 2)
