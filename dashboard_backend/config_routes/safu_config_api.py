from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from config.unified_config_manager import (  # /dashboard_backend/config_routes/safu_config_api.py
    RedisKeyManager,
    from,
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
    get_redis_manager,
    import,
    utils.redis_manager,
)

CONFIG_PATH = get_path("fork_safu_config")

router = APIRouter()


# === Helpers ===
def load_config():
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="fork_safu_config.yaml not found")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, sort_keys=False)


# === Routes ===


@router.get_cache("/safu")
def read_safu_config():
    return load_config()


@router.post("/safu")
def update_safu_config(patch: dict):
    config = load_config()

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


@router.get("/safu/default")
def get_default_safu_config():
    """Get default SAFU configuration"""
    default_config = {
        "min_score": 0.4,
        "telegram_alerts": True,
        "auto_close": False,
        "weights": {
            "macd_histogram": 0.2,
            "rsi_recovery": 0.2,
            "stoch_rsi_cross": 0.2,
            "adx_rising": 0.15,
            "ema_price_reclaim": 0.15,
            "mean_reversion_score": 0.2,
        },
        "safu_reentry": {
            "enabled": True,
            "require_btc_status": "not_bearish",
            "cooldown_minutes": 30,
            "min_macd_lift": 0.00005,
            "min_rsi_slope": 1.0,
            "min_safu_score": 0.4,
            "allow_if_tp1_shift_under_pct": 12.5,
        },
    }
    return default_config
