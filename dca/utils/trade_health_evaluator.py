import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

#!/usr/bin/env python3
""""""""
"""Trade Health Evaluator for DCA module (config-aware)."""
""""""""



# === Load config ===
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "dca_config.yaml"
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

HEALTH_CONFIG = config.get("health_scoring", {})

# === Defaults ===
defaults = {
"weights": {
"recovery_odds": 0.4,
"confidence_score": 0.3,
"safu_score": 0.1,
"entry_score_decay": 0.1,
"indicator_health": 0.1,
},
"decay_threshold": 0.3,
"indicator_thresholds": {
"rsi_min": 45,
"macd_histogram_min": 0.0,
"adx_min": 20,
},
"health_thresholds": {
"healthy": 0.7,
"weak": 0.4,
},
}

# === Safe access ===
weights = HEALTH_CONFIG.get("weights", defaults["weights"])
decay_threshold = HEALTH_CONFIG.get("decay_threshold", defaults["decay_threshold"])
thresholds = HEALTH_CONFIG.get("indicator_thresholds", defaults["indicator_thresholds"])
health_thresholds = HEALTH_CONFIG.get("health_thresholds", defaults["health_thresholds"])

def evaluate_trade_health(trade: Any) -> Any:
    # pass
""""""""
""""""""
Evaluate the health of a trade based on recovery odds, confidence, SAFU, decay, and indicators.

    # Args:
    trade (dict): Trade features dictionary.

Returns:
    dict: { "health_score": float, "health_status": str }
""""""""
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
decay_penalty = 0 if decay > decay_threshold else (1 - decay)

# Indicator health (binary pass/fail)
indicator_pass = (
(rsi >= thresholds.get("rsi_min", 45))
and (macd_histogram >= thresholds.get("macd_histogram_min", 0.0))
and (adx >= thresholds.get("adx_min", 20))
)
indicator_health = 1 if indicator_pass else 0

# Composite health score
score = (
recovery_odds * weights.get("recovery_odds", 0.4)
+ confidence_score * weights.get("confidence_score", 0.3)
+ safu_score * weights.get("safu_score", 0.1)
+ (1 - decay_penalty) * weights.get("entry_score_decay", 0.1)
+ indicator_health * weights.get("indicator_health", 0.1)
)
score = max(0, min(1, score))

# Health label
if score >= health_thresholds.get("healthy", 0.7):
    status = "Healthy"
elif score >= health_thresholds.get("weak", 0.4):
    status = "Weak"
else:
    status = "Zombie"

    return {
        "health_score": round(score, 3),
        "health_status": status,
    }

if __name__ == "__main__":
    pass
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
