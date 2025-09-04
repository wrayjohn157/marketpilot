from typing import Dict, List, Optional, Any, Union, Tuple

import pandas as pd

import joblib

#!/usr/bin/env python3

from
 pathlib import Path

# === Model Path ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = Path("/home/signal/market7/ml/models/xgb_recovery_model.pkl")

# === Expected Features ===
EXPECTED_FEATURES = [
    "step", "entry_score", "current_score", "drawdown_pct", "safu_score",
    "macd_lift", "rsi", "rsi_slope", "adx", "confidence_score", "tp1_shift",
    "safu_good_but_zombie",
    "snapshot_score_trend", "snapshot_rsi_trend", "snapshot_max_drawdown",
    "snapshot_min_score", "snapshot_min_rsi", "snapshot_time_to_max_drawdown_min"
]

# === Load Model ===
try:
    MODEL = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"[ERROR] Could not load recovery model: {e}")
    MODEL = None

def sim_predict_recovery_odds(snapshot: dict, step: int = 1) -> float:
    """Simulate recovery odds from a snapshot dict."""
    if MODEL is None:
        print("[WARN] No model loaded")
        return 0.0

    try:
        row = snapshot.copy()
        row["step"] = step
        row["safu_good_but_zombie"] = 0.0  # Sim placeholder
        row["snapshot_score_trend"] = -0.1
        row["snapshot_rsi_trend"] = -0.1
        row["snapshot_max_drawdown"] = row.get("drawdown_pct", 0)
        row["snapshot_min_score"] = min(row.get("entry_score", 0.0), row.get("current_score", 0.0))
        row["snapshot_min_rsi"] = row.get("rsi", 50)
        row["snapshot_time_to_max_drawdown_min"] = 5

        # Fill missing with zeros
        for feat in EXPECTED_FEATURES:
            if feat not in row:
                row[feat] = 0.0

        df = pd.DataFrame([row], columns=EXPECTED_FEATURES)
        return round(float(MODEL.predict_proba(df)[0][1]), 4)

    except Exception as e:
        print(f"[ERROR] Failed recovery odds sim: {e}")
        return 0.0
