"""
DCA Configuration API endpoints
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any
import json
import os

router = APIRouter()

# Default DCA configuration (immutable, safe fallback)
DEFAULT_DCA_CONFIG = {
    "max_trade_usdt": 2000,
    "base_order_usdt": 200,
    "drawdown_trigger_pct": 1.2,
    "safu_score_threshold": 0.5,
    "score_decay_min": 0.2,
    "buffer_zone_pct": 0.0,
    "require_indicator_health": True,
    "indicator_thresholds": {
        "rsi": 30.0,
        "macd_histogram": -0.001,
        "adx": 25.0
    },
    "use_btc_filter": False,
    "btc_indicators": {
        "rsi_max": 70.0,
        "macd_histogram_max": 0.001,
        "adx_max": 50.0
    },
    "so_volume_table": [100, 150, 200, 300, 500],
    "tp1_targets": [1.0, 2.0, 3.0, 5.0],
    "zombie_tag": 0.1,
    "min_drawdown_pct": 0.5,
    "max_drawdown_pct": 10.0,
    "max_score": 1.0,
    "require_zero_recovery_odds": False,
    "max_macd_lift": 0.01,
    "max_rsi_slope": 5.0,
    "use_ml_spend_model": False,
    "spend_adjustment_rules": {
        "min_volume": 0.5,
        "max_multiplier": 2.0
    },
    "tp1_shift_soft_cap": 0.8,
    "low_dd_pct_limit": 2.0,
    "log_verbose": False,
    "enforce_price_below_last_step": True,
    "trailing_step_guard": True,
    "min_pct_gap_from_last_dca": 0.5,
    "adaptive_step_spacing": True,
    "require_macd_cross": False,
    "macd_cross_lookback": 5,
    "bottom_reversal_filter": {
        "local_price_reversal_window": 10,
        "lookback_bars": 20,
        "rsi_floor": 25.0,
        "candles_required": 5
    }
}

# File paths for configuration storage
USER_CONFIG_FILE = "/home/signal/marketpilot/config/user_dca_config.json"
DEFAULT_CONFIG_FILE = "/home/signal/marketpilot/config/default_dca_config.json"

def load_user_config() -> Dict[str, Any]:
    """Load user configuration from file, fallback to default if not found"""
    try:
        if os.path.exists(USER_CONFIG_FILE):
            with open(USER_CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading user config: {e}")
    return DEFAULT_DCA_CONFIG.copy()

def save_user_config(config_data: Dict[str, Any]) -> bool:
    """Save user configuration to file"""
    try:
        os.makedirs(os.path.dirname(USER_CONFIG_FILE), exist_ok=True)
        with open(USER_CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving user config: {e}")
        return False

def save_default_config() -> bool:
    """Save default configuration to file (for reference)"""
    try:
        os.makedirs(os.path.dirname(DEFAULT_CONFIG_FILE), exist_ok=True)
        with open(DEFAULT_CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_DCA_CONFIG, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving default config: {e}")
        return False

@router.get("/config/dca")
def get_dca_config() -> Dict[str, Any]:
    """Get current user DCA configuration (modifiable)"""
    user_config = load_user_config()
    return {
        "config": user_config,
        "is_default": user_config == DEFAULT_DCA_CONFIG,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/config/dca")
def save_dca_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save user DCA configuration (modifiable)"""
    if save_user_config(config_data):
        return {
            "success": True,
            "message": "User configuration saved successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "success": False,
            "message": "Failed to save user configuration",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/config/dca/default")
def get_default_dca_config() -> Dict[str, Any]:
    """Get default DCA configuration (immutable, safe fallback)"""
    # Save default config to file for reference
    save_default_config()
    return {
        "config": DEFAULT_DCA_CONFIG,
        "is_default": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/config/dca/reset")
def reset_dca_config() -> Dict[str, Any]:
    """Reset user DCA configuration to match default (overwrites user config)"""
    if save_user_config(DEFAULT_DCA_CONFIG):
        return {
            "success": True,
            "message": "User configuration reset to defaults",
            "config": DEFAULT_DCA_CONFIG,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "success": False,
            "message": "Failed to reset user configuration",
            "timestamp": datetime.utcnow().isoformat()
        }
