from typing import Dict, List, Optional, Any, Union, Tuple
import json

import pandas as pd

import joblib
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


#!/usr/bin/env python3

from
 pathlib import Path

# === Dynamic Paths ===
BASE_DIR = get_path("base")  # /market7
RECOVERY_MODEL_PATH = BASE_DIR / "ml" / "models" / "xgb_recovery_model.pkl"
SNAPSHOT_PATH = BASE_DIR / "ml" / "datasets" / "recovery_snapshots"

# === Feature List for the Model ===
EXPECTED_FEATURES = [
    "step", "entry_score", "current_score", "drawdown_pct", "safu_score",
    "macd_lift", "rsi", "rsi_slope", "adx", "confidence_score", "tp1_shift",
    "safu_good_but_zombie",
    "snapshot_score_trend", "snapshot_rsi_trend", "snapshot_max_drawdown",
    "snapshot_min_score", "snapshot_min_rsi", "snapshot_time_to_max_drawdown_min"
]

# === Load model once ===
try:
    MODEL = joblib.load(RECOVERY_MODEL_PATH)
except Exception as e:
    print(f"[ERROR] Failed to load recovery model: {e}")
    MODEL = None

def get_latest_snapshot(symbol: str, deal_id: int):
    """Load the latest row from the recovery snapshot for a trade."""
    file = SNAPSHOT_PATH / f"{symbol.replace('USDT_', '')}_{deal_id}.jsonl"
    if not file.exists():
        return None
    try:
        with open(file, "r") as f:
            lines = f.readlines()
        if lines:
            return json.loads(lines[-1])
    except Exception:
        return None
    return None

def predict_recovery_odds(snapshot_row: dict) -> float:
    """Predict recovery odds from the latest snapshot dict."""
    if not snapshot_row:
        return 0.0
    if MODEL is None:
        print("[WARN] No recovery model loaded; cannot predict odds.")
        return 0.0

    try:
        row = snapshot_row.copy()
        meta = row.pop("snapshot_meta", {})
        for k, v in meta.items():
            row[f"snapshot_{k}"] = v

        # Fill missing fields
        row = {k: v for k, v in row.items() if isinstance(v, (int, float, bool))}
        for feat in EXPECTED_FEATURES:
            if feat not in row:
                row[feat] = 0.0

        df = pd.DataFrame([row], columns=EXPECTED_FEATURES)
        proba = MODEL.predict_proba(df)[0][1]  # probability of "good recovery"
        return round(float(proba), 4)

    except Exception as e:
        print(f"[WARN] Recovery odds prediction failed: {e}")
        return 0.0
