#!/usr/bin/env python3
"""
Trade Health Evaluator for DCA module.
"""

import json
import math
from pathlib import Path

# === Health Scoring Configuration ===
HEALTH_CONFIG = {
    "weights": {
        "recovery_odds": 0.4,
        "confidence_score": 0.3,
        "safu_score": 0.1,
        "entry_score_decay": 0.1,
        "indicator_health": 0.1,
    },
    "decay_threshold": 0.3,
    "rsi_min": 45,
    "macd_histogram_min": 0.0,
    "adx_min": 20,
    "health_thresholds": {
        "healthy": 0.7,
        "weak": 0.4,
    },
}

# TODO: Externalize HEALTH_CONFIG to /config/dca_config.yaml for dynamic tuning.


def evaluate_trade_health(trade):
    """
    Evaluate the health of a trade based on recovery odds, confidence, SAFU, decay, and indicators.

    Args:
        trade (dict): Trade features dictionary.

    Returns:
        dict: { "health_score": float, "health_status": str }
    """
    recovery_odds = trade.get("recovery_odds", 0)
    confidence_score = trade.get("confidence_score", 0)
    safu_score = trade.get("safu_score", 0)
    entry_score = trade.get("entry_score", 0)
    current_score = trade.get("current_score", 0)

    rsi = trade.get("rsi", 50)
    macd_histogram = trade.get("macd_histogram", 0)
    adx = trade.get("adx", 20)

    # Entry score decay penalty
    decay = current_score / entry_score if entry_score else 1
    decay_penalty = 0 if decay > HEALTH_CONFIG["decay_threshold"] else (1 - decay)

    # Indicator health (binary pass/fail)
    indicator_pass = (
        (rsi >= HEALTH_CONFIG["rsi_min"])
        and (macd_histogram >= HEALTH_CONFIG["macd_histogram_min"])
        and (adx >= HEALTH_CONFIG["adx_min"])
    )
    indicator_health = 1 if indicator_pass else 0

    # Composite health score
    score = (
        recovery_odds * HEALTH_CONFIG["weights"]["recovery_odds"]
        + confidence_score * HEALTH_CONFIG["weights"]["confidence_score"]
        + safu_score * HEALTH_CONFIG["weights"]["safu_score"]
        + (1 - decay_penalty) * HEALTH_CONFIG["weights"]["entry_score_decay"]
        + indicator_health * HEALTH_CONFIG["weights"]["indicator_health"]
    )
    score = max(0, min(1, score))  # Clamp score to [0,1]

    # Health label
    if score >= HEALTH_CONFIG["health_thresholds"]["healthy"]:
        status = "Healthy"
    elif score >= HEALTH_CONFIG["health_thresholds"]["weak"]:
        status = "Weak"
    else:
        status = "Zombie"

    return {
        "health_score": round(score, 3),
        "health_status": status,
    }


if __name__ == "__main__":
    # Example demo
    trade = {
        "symbol": "USDT_XRP",
        "recovery_odds": 0.82,
        "confidence_score": 0.78,
        "safu_score": 0.7,
        "entry_score": 0.75,
        "current_score": 0.45,
        "rsi": 53,
        "macd_histogram": 0.002,
        "adx": 24,
    }

    health = evaluate_trade_health(trade)
    print(f"{trade['symbol']}: {health['health_status']} ({health['health_score']})")
