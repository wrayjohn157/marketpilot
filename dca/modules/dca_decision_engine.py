def should_dca(trade, config, indicators, btc_status, entry_score, current_score, safu_score, tp1_sim_pct):
    rejection_reason = None
    recovery_odds = 0  # Always computed now

    # === BTC Filter ===
    if config.get("use_btc_filter", True) and btc_status != "SAFE":
        return False, "btc_unsafe", recovery_odds

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

    # === SAFU ===
    if safu_score is None or safu_score < config.get("safu_score_threshold", 0.4):
        return False, "safu_low", recovery_odds

    # === Score Decay ===
    if current_score is not None and current_score < config.get("score_decay_min", 0.3):
        return False, "score_decay", recovery_odds

    # === Trajectory ===
    if config.get("use_trajectory_check", True):
        if indicators.get("macd_lift", 0) < config["trajectory_thresholds"].get("macd_lift_min", 0.00001):
            return False, "macd_flat", recovery_odds
        if indicators.get("rsi_slope", 0) < config["trajectory_thresholds"].get("rsi_slope_min", 0.1):
            return False, "rsi_flat", recovery_odds

    # === Drawdown Buffer ===
    deviation_pct = trade.get("drawdown_pct", 0)
    required_dd = (num_so + 2) * config.get("buffer_zone_pct", 0.3)
    if deviation_pct < max(config.get("drawdown_trigger_pct", 1.5), required_dd):
        return False, "drawdown_too_shallow", recovery_odds

    # === TP1 Feasibility ===
    if config.get("require_tp1_feasibility", True):
        if tp1_sim_pct > config.get("max_tp1_shift_pct", 2.0):
            return False, "tp1_not_feasible", recovery_odds

    # === Recovery Odds (Always calculated) ===
    recovery_odds = 0
    if indicators.get("macd_lift", 0) > config["trajectory_thresholds"].get("macd_lift_min", 0):
        recovery_odds += 0.3
    if indicators.get("rsi_slope", 0) > config["trajectory_thresholds"].get("rsi_slope_min", 0):
        recovery_odds += 0.3
    if safu_score and safu_score > 0.6:
        recovery_odds += 0.2
    if indicators.get("rsi", 0) > 45:
        recovery_odds += 0.2
    recovery_odds = min(recovery_odds, 1.0)

    if config.get("require_recovery_odds", True):
        if recovery_odds < config.get("min_recovery_probability", 0.5):
            return False, "recovery_odds_low", recovery_odds

    # === Confidence Override ===
    if config.get("use_confidence_override", False):
        conf = config.get("confidence_override", {})
        if (
            safu_score >= conf.get("safu_score_min", 0.5) and
            indicators.get("macd_lift", 0) > conf.get("macd_lift_min", 0.00005) and
            indicators.get("rsi_slope", 0) > conf.get("rsi_slope_min", 1.0) and
            deviation_pct >= config.get("drawdown_trigger_pct", 1.5)
        ):
            return True, "confidence_override", recovery_odds

    return True, None, recovery_odds

def how_much_to_dca(trade, config):
    num_so = trade.get("completed_safety_orders_count", 0)
    so_volume_table = config.get("so_volume_table", [])
    if num_so >= len(so_volume_table):
        return 0
    return so_volume_table[num_so]
