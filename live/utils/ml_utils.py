# ml_utils.py
import os
import joblib
import numpy as np
import logging
from pathlib import Path

MODEL_PATH = Path("/home/signal/market6/live/models/xgb_model.pkl")

# === Load Model ===
_model = None

def load_model():
    global _model
    if _model is None:
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
            logging.info(f"✅ Loaded model from {MODEL_PATH}")
        else:
            raise FileNotFoundError(f"❌ Model not found: {MODEL_PATH}")
    return _model

def prepare_features(indicator_data: dict) -> np.ndarray:
    """
    Expected input is a dictionary like:
    {
        'macd_histogram': float,
        'rsi_recovery': float,
        'adx_rising': float,
        'stoch_rsi_cross': float,
        'ema_price_reclaim': float,
        'mean_reversion_score': float,
        'volume_penalty': float,
        ... any other features used in training
    }
    """
    # Define expected order of features (must match training)
    feature_order = [
        'macd_histogram',
        'macd_bearish_cross',
        'rsi_recovery',
        'stoch_rsi_cross',
        'stoch_overbought_penalty',
        'adx_rising',
        'ema_price_reclaim',
        'mean_reversion_score',
        'volume_penalty'
    ]

    features = [indicator_data.get(key, 0.0) for key in feature_order]
    return np.array([features])  # shape: (1, n_features)

def run_inference(indicator_data: dict) -> float:
    """Load model, prepare features, and return predicted probability (0.0 to 1.0)."""
    model = load_model()
    X = prepare_features(indicator_data)
    y_pred = model.predict_proba(X)[0][1]  # Class 1 = success
    return round(float(y_pred), 4)
