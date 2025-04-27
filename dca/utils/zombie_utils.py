#!/usr/bin/env python3
"""
Zombie Trade Tagging Utilities for Smart DCA.
"""

import yaml
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "dca" / "config" / "dca_config.yaml"

# === Config Loader ===
def load_zombie_config():
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        return config.get("zombie_tag", {})
    except Exception as e:
        print(f"[WARN] Failed to load zombie config: {e}")
        return {}

zombie_config = load_zombie_config()
ENABLED = zombie_config.get("enabled", False)

# === Zombie Detection ===
def is_zombie_trade(indicators, recovery_odds, current_score):
    """
    Determines if a trade should be tagged as a zombie trade based on drawdown, score, recovery odds, and indicator slopes.

    Args:
        indicators (dict): Current indicator values.
        recovery_odds (float): Current recovery odds prediction.
        current_score (float): Current fork score.

    Returns:
        bool: True if the trade is considered a zombie, False otherwise.
    """
    if not ENABLED:
        return False

    min_dd = zombie_config.get("min_drawdown_pct", 0.5)
    max_dd = zombie_config.get("max_drawdown_pct", 5)
    max_score = zombie_config.get("max_score", 0.3)
    require_zero_odds = zombie_config.get("require_zero_recovery_odds", True)
    max_macd_lift = zombie_config.get("max_macd_lift", 0.0)
    max_rsi_slope = zombie_config.get("max_rsi_slope", 0.0)

    dd = indicators.get("drawdown_pct", 0)
    macd_lift = indicators.get("macd_lift", 0)
    rsi_slope = indicators.get("rsi_slope", 0)

    if not (min_dd <= dd <= max_dd):
        return False
    if current_score > max_score:
        return False
    if require_zero_odds and recovery_odds > 0:
        return False
    if macd_lift > max_macd_lift:
        return False
    if rsi_slope > max_rsi_slope:
        return False

    return True
