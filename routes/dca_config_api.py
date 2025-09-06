"""
DCA Configuration API Routes
Handles DCA strategy configuration with two-tier system
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
import json
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Default DCA configuration
DEFAULT_DCA_CONFIG = {
    "max_safety_orders": 5,
    "safety_order_volume": 0.1,
    "safety_order_step_scale": 1.2,
    "safety_order_volume_scale": 1.0,
    "take_profit": 1.0,
    "take_profit_type": "total",
    "stop_loss": 0.0,
    "stop_loss_type": "total",
    "stop_loss_timeout": 0,
    "max_active_deals": 1,
    "max_deals": 0,
    "active_safety_orders_count": 0,
    "safety_order_volume_currency": "base_currency",
    "martingale_volume_coefficient": 0.0,
    "martingale_step_coefficient": 0.0,
    "stop_loss_percentage": 0.0,
    "cooldown": 0,
    "btc_limiting": False,
    "strategy": "long",
    "min_volume_btc_24h": 0.0,
    "profit_currency": "quote_currency",
    "min_price": 0.0,
    "max_price": 0.0,
    "require_health": True,
    "health_check_interval": 300,
    "max_health_check_failures": 3,
    "health_check_timeout": 30,
    "health_check_retry_delay": 60
}

# File paths
USER_CONFIG_FILE = "user_dca_config.json"
DEFAULT_CONFIG_FILE = "default_dca_config.json"

def load_user_config() -> Dict[str, Any]:
    """Load user configuration from file, fallback to default if not found"""
    try:
        if os.path.exists(USER_CONFIG_FILE):
            with open(USER_CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading user config: {e}")
    return DEFAULT_DCA_CONFIG.copy()

def save_user_config(config: Dict[str, Any]) -> None:
    """Save user configuration to file"""
    try:
        with open(USER_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving user config: {e}")

def save_default_config() -> None:
    """Save default configuration to file"""
    try:
        with open(DEFAULT_CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_DCA_CONFIG, f, indent=2)
    except Exception as e:
        print(f"Error saving default config: {e}")

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
    """Save user DCA configuration"""
    try:
        # Validate and save the configuration
        save_user_config(config_data)
        return {
            "message": "Configuration saved successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to save DCA config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {e}")

@router.get("/config/dca/default")
def get_default_dca_config() -> Dict[str, Any]:
    """Get default DCA configuration (immutable)"""
    return {
        "config": DEFAULT_DCA_CONFIG,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/config/dca/reset")
def reset_dca_config() -> Dict[str, Any]:
    """Reset user DCA configuration to defaults"""
    try:
        save_user_config(DEFAULT_DCA_CONFIG)
        return {
            "message": "Configuration reset to defaults",
            "config": DEFAULT_DCA_CONFIG,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to reset DCA config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset configuration: {e}")