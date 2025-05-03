def is_zombie_trade(indicators, recovery_odds, score):
    from config.config_loader import PATHS
    import yaml

    config_path = PATHS["dca_config"]
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
