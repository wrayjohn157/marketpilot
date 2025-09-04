# /dashboard_backend/config_routes/dca_config_api.py

from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from config.unified_config_manager import (
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
)
from utils.redis_manager import RedisKeyManager, get_redis_manager

CONFIG_PATH = get_path("dca_config")

router = APIRouter()


# === Helpers ===
def load_config():
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="dca_config.yaml not found")
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(data, f, sort_keys=False)


# === Routes ===


@router.get_cache("/dca")
def read_dca_config():
    return load_config()


@router.post("/dca")
def update_dca_config(patch: dict):
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


@router.get("/dca/default")
def get_default_dca_config():
    """Get default DCA configuration"""
    default_config = {
        "max_trade_usdt": 2000,
        "base_order_usdt": 200,
        "drawdown_trigger_pct": 1.2,
        "safu_score_threshold": 0.5,
        "score_decay_min": 0.2,
        "buffer_zone_pct": 0,
        "require_indicator_health": True,
        "indicator_thresholds": {
            "rsi": 42,
            "macd_histogram": 0.0001,
            "adx": 12,
        },
        "use_btc_filter": False,
        "btc_indicators": {
            "rsi_max": 35,
            "macd_histogram_max": 0,
            "adx_max": 15,
        },
        "use_trajectory_check": True,
        "trajectory_thresholds": {
            "macd_lift_min": 0.0001,
            "rsi_slope_min": 1.0,
        },
        "require_tp1_feasibility": True,
        "max_tp1_shift_pct": 25,
        "require_recovery_odds": True,
        "min_recovery_probability": 0.5,
        "min_confidence_odds": 0.65,
        "use_confidence_override": True,
        "confidence_dca_guard": {
            "safu_score_min": 0.5,
            "macd_lift_min": 0.00005,
            "rsi_slope_min": 1.0,
            "confidence_score_min": 0.75,
            "min_confidence_delta": 0.1,
            "min_tp1_shift_gain_pct": 1.5,
        },
        "soft_confidence_override": {
            "enabled": False,
        },
        "min_be_improvement_pct": 2.0,
        "step_repeat_guard": {
            "enabled": True,
            "min_conf_delta": 0.1,
            "min_tp1_delta": 1.5,
        },
        "so_volume_table": [20, 15, 25, 40, 65, 90, 150, 250],
        "tp1_targets": [0.4, 1.1, 1.7, 2.4, 3.0, 3.9, 5.2, 7.1, 10.0],
        "zombie_tag": {
            "enabled": True,
            "min_drawdown_pct": 0.5,
            "max_drawdown_pct": 5,
            "max_score": 0.3,
            "require_zero_recovery_odds": True,
            "max_macd_lift": 0.0,
            "max_rsi_slope": 0.0,
        },
        "use_ml_spend_model": True,
        "spend_adjustment_rules": {
            "min_volume": 20,
            "max_multiplier": 3.0,
            "tp1_shift_soft_cap": 2.5,
            "low_dd_pct_limit": 1.0,
        },
        "log_verbose": True,
        "enforce_price_below_last_step": True,
        "trailing_step_guard": {
            "enabled": True,
            "min_pct_gap_from_last_dca": 2.0,
        },
        "adaptive_step_spacing": {
            "enabled": False,
        },
        "require_macd_cross": False,
        "macd_cross_lookback": 1,
        "bottom_reversal_filter": {
            "enabled": True,
            "macd_lift_min": 0.0003,
            "rsi_slope_min": 0.6,
            "local_price_reversal_window": 3,
        },
    }
    return default_config
