from pathlib import Path
from typing import List
import json

import numpy as np

from utils.sim_snapshot_loader import sim_generate_snapshot_series
import joblib
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


#!/usr/bin/env python3

BASE_DIR = get_path("base").parent
MODEL_PATH = BASE_DIR / "ml" / "models" / "xgb_confidence_model.pkl"
SNAPSHOT_DIR = BASE_DIR / "sim" / "sandbox3" / "snapshots"

FEATURE_COLUMNS = [
    "trade_price",
    "trade_qty",
    "bid_price",
    "bid_qty",
    "ask_price",
    "ask_qty",
    "mid_price",
    "spread",
    "imbalance",
    "trade_count",
    "volume",
    "snapshot_score_trend",
    "snapshot_rsi_trend",
    "snapshot_max_drawdown",
    "snapshot_min_score",
    "snapshot_min_rsi",
    "snapshot_time_to_max_drawdown_min",
]

def load_model() -> Any:
    return joblib.load(MODEL_PATH)

def extract_features(trade_snapshot: dict) -> List[float]:
    features = []
    for col in FEATURE_COLUMNS:
        features.append(trade_snapshot.get(col, 0.0))
    return features

def predict_sim_confidence_score(trade_snapshot: dict) -> float:
    model = load_model()
    features = extract_features(trade_snapshot)
    features_array = np.array(features).reshape(1, -1)
    confidence_score = float(model.predict(features_array)[0])
    return confidence_score

def inject_snapshot(symbol: str, entry_time: int, step: int) -> dict:
    """
    Generate a simulated snapshot using internal simulator.
    """
    snapshots = sim_generate_snapshot_series(symbol, entry_time)
    if isinstance(snapshots, list):
        if step <= len(snapshots):
            return snapshots[step - 1]
        return snapshots[-1]
    return snapshots
