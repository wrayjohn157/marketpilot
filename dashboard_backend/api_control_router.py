# /market7/dashboard_backend/api_control_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import yaml
import os
from utils.redis_manager import get_redis_manager, RedisKeyManager



CONFIG_PATH = PATHS["dca"] / "config" / "dca_config.yaml"

router = APIRouter()


# === Pydantic schema ===
class DcaSettings(BaseModel):
    max_trade_usdt: float
    base_order_usdt: float
    drawdown_trigger_pct: float
    min_recovery_probability: float
    min_confidence_odds: float
    use_confidence_override: bool
    use_btc_filter: bool
    zombie_tag_enabled: bool
    rsi_threshold: float
    macd_histogram_min: float
    adx_min: float
    macd_lift_min: float
    rsi_slope_min: float
    max_tp1_shift_pct: float
    require_tp1_feasibility: bool
    min_be_improvement_pct: float
    btc_rsi_max: float
    btc_macd_histogram_max: float
    btc_adx_max: float
    use_ml_spend_model: bool
    tp1_shift_soft_cap: float
    low_dd_pct_limit: float


# === Helper ===
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


# === GET current config ===
@router.get_cache("/config/dca")
def get_dca_config():
    raw = load_config()
    try:
        return DcaSettings(
            max_trade_usdt=raw["max_trade_usdt"],
            base_order_usdt=raw["base_order_usdt"],
            drawdown_trigger_pct=raw["drawdown_trigger_pct"],
            min_recovery_probability=raw["min_recovery_probability"],
            min_confidence_odds=raw["min_confidence_odds"],
            use_confidence_override=raw.get("use_confidence_override", True),
            use_btc_filter=raw.get("use_btc_filter", True),
            zombie_tag_enabled=raw.get("zombie_tag", {}).get("enabled", True),
            rsi_threshold=raw["indicator_thresholds"]["rsi"],
            macd_histogram_min=raw["indicator_thresholds"]["macd_histogram"],
            adx_min=raw["indicator_thresholds"]["adx"],
            macd_lift_min=raw["trajectory_thresholds"]["macd_lift_min"],
            rsi_slope_min=raw["trajectory_thresholds"]["rsi_slope_min"],
            max_tp1_shift_pct=raw["max_tp1_shift_pct"],
            require_tp1_feasibility=raw["require_tp1_feasibility"],
            min_be_improvement_pct=raw["min_be_improvement_pct"],
            btc_rsi_max=raw["btc_indicators"]["rsi_max"],
            btc_macd_histogram_max=raw["btc_indicators"]["macd_histogram_max"],
            btc_adx_max=raw["btc_indicators"]["adx_max"],
            use_ml_spend_model=raw.get("use_ml_spend_model", False),
            tp1_shift_soft_cap=raw["spend_adjustment_rules"]["tp1_shift_soft_cap"],
            low_dd_pct_limit=raw["spend_adjustment_rules"]["low_dd_pct_limit"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === PATCH config ===
@router.post("/config/dca")
def update_dca_config(payload: DcaSettings):
    config = load_config()

    config["max_trade_usdt"] = payload.max_trade_usdt
    config["base_order_usdt"] = payload.base_order_usdt
    config["drawdown_trigger_pct"] = payload.drawdown_trigger_pct
    config["min_recovery_probability"] = payload.min_recovery_probability
    config["min_confidence_odds"] = payload.min_confidence_odds
    config["use_confidence_override"] = payload.use_confidence_override
    config["use_btc_filter"] = payload.use_btc_filter
    config["zombie_tag"] = {"enabled": payload.zombie_tag_enabled}

    config["indicator_thresholds"]["rsi"] = payload.rsi_threshold
    config["indicator_thresholds"]["macd_histogram"] = payload.macd_histogram_min
    config["indicator_thresholds"]["adx"] = payload.adx_min

    config["trajectory_thresholds"]["macd_lift_min"] = payload.macd_lift_min
    config["trajectory_thresholds"]["rsi_slope_min"] = payload.rsi_slope_min

    config["max_tp1_shift_pct"] = payload.max_tp1_shift_pct
    config["require_tp1_feasibility"] = payload.require_tp1_feasibility
    config["min_be_improvement_pct"] = payload.min_be_improvement_pct

    config["btc_indicators"]["rsi_max"] = payload.btc_rsi_max
    config["btc_indicators"]["macd_histogram_max"] = payload.btc_macd_histogram_max
    config["btc_indicators"]["adx_max"] = payload.btc_adx_max

    config["use_ml_spend_model"] = payload.use_ml_spend_model
    config["spend_adjustment_rules"]["tp1_shift_soft_cap"] = payload.tp1_shift_soft_cap
    config["spend_adjustment_rules"]["low_dd_pct_limit"] = payload.low_dd_pct_limit

    save_config(config)
    return {"status": "✅ Updated dca_config.yaml"}
