"Trade Health Evaluator for SIM sandbox (uses local config)."

from pathlib import Path
import yaml
import logging

CONFIG_PATH = Path("/home/signal/market7/sim/config/dca_config.yaml_fallback_real")

print(f"✅ Loaded sim trade health config from {CONFIG_PATH}")

with open(CONFIG_PATH, "r") as file:
    CONFIG = yaml.safe_load(file)

logger = logging.getLogger(__name__)

def evaluate_trade_health(trade):
    """
    Evaluate the health of a trade based on configured thresholds.

    Args:
        trade (dict): A dictionary containing trade information.

    Returns:
        dict: { "health_status": str, "health_score": float }
    """
    price = trade.get('price')
    volume = trade.get('volume')

    if price is None or volume is None:
        logger.warning("Trade data incomplete.")
        return {
            "health_status": "Unknown",
            "health_score": 0.0
        }

    price_threshold = CONFIG.get('price_threshold', 100)
    volume_threshold = CONFIG.get('volume_threshold', 10)

    if price > price_threshold and volume > volume_threshold:
        return {
            "health_status": "Healthy",
            "health_score": 1.0
        }
    elif price > price_threshold or volume > volume_threshold:
        return {
            "health_status": "Moderate",
            "health_score": 0.6
        }
    else:
        return {
            "health_status": "Unhealthy",
            "health_score": 0.2
        }
