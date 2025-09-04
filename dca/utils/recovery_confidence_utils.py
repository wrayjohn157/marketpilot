from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging

import pandas as pd

import joblib
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs
from config.unified_config_manager import get_config


#!/usr/bin/env python3

from
 pathlib import Path

# === Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Dynamic Paths ===
BASE_DIR = get_path("base")  # /market7
MODEL_PATH = BASE_DIR / "ml" / "models" / "xgb_confidence_model.pkl"
SNAPSHOT_DIR = BASE_DIR / "ml" / "datasets" / "recovery_snapshots"

# === Finalized feature list matching model input ===
FEATURE_COLUMNS = [
    "step", "entry_score", "current_score", "tp1_shift", "safu_score",
    "rsi", "macd_histogram", "adx", "macd_lift", "rsi_slope", "drawdown_pct",
    "snapshot_score_trend", "snapshot_rsi_trend", "snapshot_max_drawdown",
    "snapshot_min_score", "snapshot_min_rsi", "snapshot_time_to_max_drawdown_min"
]

# === Load Model Once ===
try:
    MODEL = joblib.load(str(MODEL_PATH))
    logger.info(f"✅ Loaded confidence model from {MODEL_PATH}")
except Exception as e:
    logger.error(f"❌ Failed to load confidence model: {e}")
    MODEL = None

def predict_confidence_score(trade_snapshot: dict) -> float:
    """
    Predict a confidence score using the trained XGBoost regression model.
    Will auto-inject 'snapshot_*' features if available from recovery snapshots.
    """
    if not isinstance(trade_snapshot, dict):
        logger.warning("⚠️ Invalid trade_snapshot; returning 0.0")
        return 0.0

    # Extract deal and asset
    deal_id = trade_snapshot.get("deal_id")
    raw_symbol = trade_snapshot.get("symbol", "")
    asset = raw_symbol.split("_", 1)[1] if "_" in raw_symbol else raw_symbol.replace("USDT", "")

    snap_file = SNAPSHOT_DIR / f"{asset}_{deal_id}.jsonl"

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
            logger.warning(f"⚠️ Could not load snapshot {snap_file.name}: {e}")

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

    if MODEL is None:
        logger.error("❌ No confidence model loaded; prediction unavailable.")
        return 0.0

    try:
        return round(float(MODEL.predict(df)[0]), 4)
    except Exception as e:
        logger.error(f"❌ Confidence prediction failed: {e}")
        return 0.0
