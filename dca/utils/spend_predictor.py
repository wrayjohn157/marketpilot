#!/usr/bin/env python3
"""
Utility to predict DCA spend volume based on trained XGBoost model.
"""
import joblib
import pandas as pd
from pathlib import Path
import logging

# Configure logging
d_logging = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Path to the trained model (saved via joblib)
MODEL_PATH = Path("/home/signal/market6/live/models/xgb_spend_model.pkl")

# Load model once
try:
    MODEL = joblib.load(str(MODEL_PATH))
    logging.info(f"🧠 Loaded spend model from {MODEL_PATH}")
except Exception as e:
    logging.error(f"Failed to load spend model: {e}")
    MODEL = None

# Required feature names (based on model training)
FEATURES = [
    "entry_score", "current_score", "drawdown_pct", "safu_score", "macd_lift",
    "rsi", "rsi_slope", "adx", "tp1_shift", "recovery_odds", "confidence_score",
    "zombie_tagged", "btc_rsi", "btc_macd_histogram", "btc_adx", "btc_status"
]


def predict_spend_volume(input_features: dict) -> float:
    """
    Predicts the spend volume given a feature dictionary.

    Args:
        input_features (dict): Mapping of feature names to values. Must include all FEATURES.

    Returns:
        float: Predicted spend volume, or 0.0 on error.
    """
    if MODEL is None:
        logging.error("No spend model loaded; cannot predict volume.")
        return 0.0

    # Build DataFrame for consistent ordering
    df = pd.DataFrame([{feat: input_features.get(feat, 0.0) for feat in FEATURES}])

    try:
        pred = MODEL.predict(df)[0]
        return float(pred)
    except Exception as e:
        logging.error(f"Spend prediction failed: {e}")
        return 0.0


def adjust_volume(
    predicted_volume: float,
    already_spent: float,
    max_budget: float = 2000.0,
    drawdown_pct: float = 0.0,
    tp1_shift_pct: float = 0.0
) -> float:
    """
    Adjusts the predicted volume based on remaining budget, TP1 feasibility, and sanity rules.

    Args:
        predicted_volume (float): Raw predicted volume from ML model.
        already_spent (float): Total spent so far in the trade.
        max_budget (float): Max allowable per trade. Default = 2000 USDT.
        drawdown_pct (float): Current drawdown percentage.
        tp1_shift_pct (float): Simulated TP1 shift percentage.

    Returns:
        float: Adjusted volume that does not exceed remaining budget or sane limits.
    """
    # === Sanity constraints ===
    min_effective_dd_pct = 1.0    # Skip DCA under this DD
    min_tp1_shift_pct = 1.0       # Skip DCA if TP1 is too close
    max_ratio = 10.0              # Don't spend more than X times current allocation

    remaining_budget = max(0.0, max_budget - already_spent)

    # Skip if the drawdown or recovery window is too small
    if drawdown_pct < min_effective_dd_pct:
        return 0.0
    if tp1_shift_pct < min_tp1_shift_pct:
        return 0.0

    # Limit ML prediction by remaining budget and sanity cap
    spend_limit = already_spent * max_ratio
    capped_volume = min(predicted_volume, remaining_budget, spend_limit)

    return round(capped_volume, 2)
