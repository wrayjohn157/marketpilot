from datetime import datetime

def should_reenter_after_safu(
    trade,
    config,
    indicators,
    safu_score,
    tp1_shift_pct,
    last_safu_time,
    btc_status
):
    """
    Determine whether a trade qualifies for reentry DCA after SAFU was triggered.

    Conditions:
    - Enabled in config
    - Cooldown period has passed
    - MACD lift and RSI slope improving
    - SAFU score back above threshold
    - TP1 shift is still recoverable
    - BTC market status is within allowed states
    """
    reentry_cfg = config.get("safu_reentry", {})
    if not reentry_cfg.get("enabled", False):
        return False

    # === BTC status gating ===
    status_requirement = reentry_cfg.get("require_btc_status", "not_bearish")
    allowed_statuses = {
        "any": ["SAFE", "NEUTRAL", "BEARISH", "BULLISH"],
        "not_bearish": ["SAFE", "NEUTRAL", "BULLISH"],
        "safe": ["SAFE"],
        "bullish_only": ["BULLISH"]
    }.get(status_requirement, ["SAFE"])

    if btc_status not in allowed_statuses:
        return False

    # === Cooldown check ===
    if last_safu_time:
        elapsed_minutes = (datetime.utcnow() - last_safu_time).total_seconds() / 60
        if elapsed_minutes < reentry_cfg.get("cooldown_minutes", 30):
            return False

    # === Indicator & health checks ===
    if indicators.get("macd_lift", 0) < reentry_cfg.get("min_macd_lift", 0.00005):
        return False
    if indicators.get("rsi_slope", 0) < reentry_cfg.get("min_rsi_slope", 1.0):
        return False
    if safu_score < reentry_cfg.get("min_safu_score", 0.4):
        return False
    if tp1_shift_pct > reentry_cfg.get("allow_if_tp1_shift_under_pct", 12.5):
        return False

    return True
