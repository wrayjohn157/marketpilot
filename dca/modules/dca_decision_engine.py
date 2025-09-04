def should_dca(trade: Any, config: Any, indicators: Any, btc_status: Any, entry_score: Any, current_score: Any, safu_score: Any, tp1_sim_pct: Any, recovery_odds: Any, : Any) -> Any:
    # === BTC Filter ===
    if config.get("use_btc_filter", True) and btc_status != "SAFE":
        return False, "btc_unsafe", recovery_odds

    # === Zombie / Hard Abandon ===
    if current_score is not None and current_score < 0.2:
        return False, "abandon_low_score", recovery_odds
    if safu_score is not None and safu_score < 0.4:
        return False, "abandon_safu", recovery_odds
    if recovery_odds is not None and recovery_odds < 0.4:
        return False, "abandon_recovery", recovery_odds

    # === Max Allocation ===
    total_spent = float(trade.get("bought_volume") or 0)
    num_so = trade.get("completed_safety_orders_count", 0)
    so_volume_table = config.get("so_volume_table", [])
    if num_so >= len(so_volume_table):
        return False, "max_so", recovery_odds
    next_so_cost = so_volume_table[num_so]
    if total_spent + next_so_cost > float(config.get("max_trade_usdt", 2000)):
        return False, "exceeds_max", recovery_odds

    # === Indicator Health ===
    if config.get("require_indicator_health", True):
        thresholds = config.get("indicator_thresholds", {})
        if indicators.get("rsi", 100) < thresholds.get("rsi", 45):
            return False, "rsi_low", recovery_odds
        if indicators.get("macd_histogram", 1) < thresholds.get("macd_histogram", 0):
            return False, "macd_bearish", recovery_odds
        if indicators.get("adx", 0) < thresholds.get("adx", 20):
            return False, "adx_weak", recovery_odds

    # === Score Decay ===
    if current_score is not None and current_score < config.get("score_decay_min", 0.3):
        return False, "score_decay", recovery_odds

    # === Trajectory ===
    if config.get("use_trajectory_check", True):
        if indicators.get("macd_lift", 0) < config["trajectory_thresholds"].get("macd_lift_min", 0.00001):
            return False, "macd_flat", recovery_odds
        if indicators.get("rsi_slope", 0) < config["trajectory_thresholds"].get("rsi_slope_min", 0.1):
            return False, "rsi_flat", recovery_odds

    # === Drawdown Trigger ===
    deviation_pct = indicators.get("drawdown_pct", 0)
    required_dd = (num_so + 2) * config.get("buffer_zone_pct", 0.0)
    if deviation_pct < max(config.get("drawdown_trigger_pct", 1.5), required_dd):
        return False, "drawdown_too_shallow", recovery_odds

    # === TP1 Feasibility ===
    if config.get("require_tp1_feasibility", True):
        if tp1_sim_pct > config.get("max_tp1_shift_pct", 25):
            return False, "tp1_not_feasible", recovery_odds
        if tp1_sim_pct < 0:
            return False, "tp1_shift_negative", recovery_odds

    # === Recovery Odds ===
    if config.get("require_recovery_odds", True):
        if recovery_odds < config.get("min_recovery_probability", 0.6):
            return False, "recovery_odds_low", recovery_odds

    return True, None, recovery_odds
