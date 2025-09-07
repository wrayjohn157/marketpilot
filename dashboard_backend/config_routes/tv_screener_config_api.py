from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from config.unified_config_manager import get_path

# /dashboard_backend/config_routes/tv_screener_config_api.py

CONFIG_PATH = get_path("tv_screener_config")

router = APIRouter()

# Default configuration
DEFAULT_CONFIG = {
    "enabled": False,
    "disable_if_btc_unhealthy": False,
    "weights": {
        "macd_histogram": 0.2,
        "rsi_recovery": 0.2,
        "stoch_rsi_cross": 0.2,
        "adx_rising": 0.15,
        "ema_price_reclaim": 0.15,
        "mean_reversion_score": 0.2,
    },
    "score_threshold": 0.7,
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
@router.get("/tv_screener")
def read_tv_screener_config():
    return load_config()


@router.post("/tv_screener")
def update_tv_screener_config(patch: dict):
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


@router.get("/tv_screener/default")
def get_default_tv_screener_config():
    """Get default TV screener configuration"""
    return DEFAULT_CONFIG
