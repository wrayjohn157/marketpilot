#!/usr/bin/env python3
import joblib
import pandas as pd
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to your trained XGBRegressor
MODEL_PATH = Path("/home/signal/market6/live/models/xgb_confidence_model.pkl")

# Finalized feature list matching model input
FEATURE_COLUMNS = [
    "step", "entry_score", "current_score", "tp1_shift", "safu_score",
    "rsi", "macd_histogram", "adx", "macd_lift", "rsi_slope", "drawdown_pct",
    "snapshot_score_trend", "snapshot_rsi_trend", "snapshot_max_drawdown",
    "snapshot_min_score", "snapshot_min_rsi", "snapshot_time_to_max_drawdown_min"
]

# Base folder for snapshots
SNAPSHOT_DIR = Path("/home/signal/market6/live/ml_dataset/recovery_snapshots")

# Load model once
try:
    MODEL = joblib.load(str(MODEL_PATH))
    logger.debug(f"Loaded confidence model from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load confidence model: {e}")
    MODEL = None


def predict_confidence_score(trade_snapshot: dict) -> float:
    """
    Predict a confidence score using the trained XGBoost regression model.
    Automatically injects all 'snapshot_*' features from the last snapshot file.
    """
    logger.debug(f">>> recovery_confidence_utils loaded from {__file__}")

    if not isinstance(trade_snapshot, dict):
        logger.warning("Invalid trade_snapshot; returning 0.0")
        return 0.0

    # Extract deal + symbol
    deal_id    = trade_snapshot.get("deal_id")
    raw_symbol = trade_snapshot.get("symbol", "")
    logger.debug(f"🔍 attempt inject → deal_id={deal_id!r}, symbol={raw_symbol!r}")

    # Parse asset name
    if "_" in raw_symbol:
        asset = raw_symbol.split("_", 1)[1]
    elif raw_symbol.endswith("USDT"):
        asset = raw_symbol[:-4]
    else:
        asset = raw_symbol

    # Load snapshot file
    snap_file = SNAPSHOT_DIR / f"{asset}_{deal_id}.jsonl"
    logger.debug(f"   looking for snapshot file at {snap_file} (exists={snap_file.exists()})")

    if deal_id and asset and snap_file.exists():
        try:
            lines = snap_file.read_text().splitlines()
            if lines:
                last = json.loads(lines[-1])
                if isinstance(last.get("snapshot_meta"), dict):
                    for k, v in last["snapshot_meta"].items():
                        trade_snapshot[f"snapshot_{k}"] = v
                else:
                    for feat in FEATURE_COLUMNS:
                        if feat.startswith("snapshot_") and feat in last:
                            trade_snapshot[feat] = last[feat]
                logger.debug(f"✅ Injected snapshot features from {snap_file.name}")
        except Exception as e:
            logger.warning(f"Could not load snapshot {snap_file.name}: {e}")

    # Build model input row
    row = {}
    for feat in FEATURE_COLUMNS:
        val = trade_snapshot.get(feat, 0.0)
        if isinstance(val, bool):
            val = float(val)
        try:
            row[feat] = float(val)
        except Exception:
            row[feat] = 0.0

    df = pd.DataFrame([row], columns=FEATURE_COLUMNS)

    logger.debug(f"Input features ➔ {list(df.columns)}")
    if MODEL is not None:
        logger.debug(f"Model expects ➔ {list(MODEL.feature_names_in_)}")

    if MODEL is None:
        logger.error("No model loaded; cannot predict confidence.")
        return 0.0

    try:
        return round(float(MODEL.predict(df)[0]), 4)
    except Exception as e:
        logger.error(f"Confidence prediction failed: {e}")
        return 0.0
