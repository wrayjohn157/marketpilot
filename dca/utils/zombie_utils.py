import yaml
from pathlib import Path

CONFIG_PATH = Path("/home/signal/market6/dca/config/dca_config.yaml")

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

zombie_config = config.get("zombie_tag", {})
ENABLED = zombie_config.get("enabled", False)

def is_zombie_trade(indicators, recovery_odds, current_score):
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
