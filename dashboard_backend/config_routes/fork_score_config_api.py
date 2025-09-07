from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from config.unified_config_manager import get_path

# /dashboard_backend/config_routes/fork_score_config_api.py

CONFIG_PATH = get_path("fork_score_config")

router = APIRouter()

# Default configuration
DEFAULT_CONFIG = {
    "min_score": 0.73,
    "weights": {
        "macd_histogram": 0.2,
        "macd_bearish_cross": -0.25,
        "rsi_recovery": 0.2,
        "stoch_rsi_cross": 0.2,
        "stoch_overbought_penalty": -0.15,
        "adx_rising": 0.15,
        "ema_price_reclaim": 0.15,
        "mean_reversion_score": 0.2,
        "volume_penalty": -0.25,
        "stoch_rsi_slope": 0.2,
    },
    "options": {
        "use_stoch_ob_penalty": True,
        "use_volume_penalty": True,
        "use_macd_bearish_check": False,
    },
}


# === Helpers ===
def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, sort_keys=False)


# === Routes ===
@router.get("/fork_score")
def read_fork_score_config():
    return load_config()


@router.post("/fork_score")
def update_fork_score_config(patch: dict):
    config = load_config()

    # Update config with patch
    for key, val in patch.items():
        if key in config:
            if isinstance(val, dict) and isinstance(config[key], dict):
                config[key].update(val)
            else:
                config[key] = val
        else:
            raise HTTPException(status_code=400, detail=f"Invalid config key: {key}")

    save_config(config)
    return {"status": "success", "updated": patch}


@router.get("/fork_score/default")
def get_default_fork_score_config():
    """Get default fork score configuration"""
    return DEFAULT_CONFIG
