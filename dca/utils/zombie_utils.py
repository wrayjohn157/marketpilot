from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs
from config.unified_config_manager import get_config

    import yaml

    
def is_zombie_trade(indicators: Any, recovery_odds: Any, score: Any) -> Any:

    config_path = get_path("dca_config")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    cfg = config.get("zombie_tag", {})
    if not cfg.get("enabled", True):
        return False

    # === Basic threshold checks ===
    if not (
        cfg["min_drawdown_pct"] <= indicators.get("drawdown_pct", 0) <= cfg["max_drawdown_pct"]
        and score <= cfg["max_score"]
        and indicators.get("macd_lift", 1) <= cfg["max_macd_lift"]
        and indicators.get("rsi_slope", 1) <= cfg["max_rsi_slope"]
    ):
        return False

    # === Optional strict check ===
    if cfg.get("require_zero_recovery_odds", False) and recovery_odds > 0:
        return False

    return True
