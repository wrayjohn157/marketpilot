from typing import Dict, Tuple

def _indicator_ok(ind, cfg) -> Tuple[bool, str]:
    th = cfg.get("indicator_thresholds", {})
    if cfg.get("require_indicator_health", True):
        if ind.get("rsi", 100) < th.get("rsi_min", 40): return False, "rsi_low"
        if ind.get("macd_histogram", 1) < th.get("macd_hist_min", 0): return False, "macd_bearish"
        if ind.get("adx", 0) < th.get("adx_min", 10): return False, "adx_weak"
    return True, ""

def _liquidation_buffer_ok(liq_price, last_price, buf_pct) -> bool:
    if not liq_price or not last_price: return True
    gap = abs((last_price - liq_price) / last_price) * 100
    return gap >= buf_pct

def _next_notional(cfg, position, step_index: int) -> float:
    table = cfg.get("so_notional_table", [])
    if step_index >= len(table): return 0.0
    return float(table[step_index])

def should_add_to_position(
    cfg: Dict, symbol: str, position: Dict, indicators: Dict, btc_status: str,
    recovery_odds: float, confidence: float, liquidation_price: float | None
) -> Tuple[bool, str, float]:
    # Account / per-position limits
    step = int(position.get("completed_safety_orders_count", 0))
    next_notional = _next_notional(cfg, position, step)
    if next_notional <= 0: return False, "max_so", 0.0

    if position.get("notional", 0.0) + next_notional > cfg.get("max_trade_notional", 10_000):
        return False, "exceeds_position_cap", 0.0

    ok, reason = _indicator_ok(indicators, cfg)
    if not ok: return False, reason, 0.0

    # Drawdown gate (reuse your spot trigger concept)
    dd = indicators.get("drawdown_pct", 0.0)
    if dd < cfg.get("drawdown_trigger_pct", 1.0):
        return False, "drawdown_too_shallow", 0.0

    # Trajectory / odds
    if cfg.get("use_trajectory_check", True):
        if indicators.get("macd_lift", 0) < cfg["trajectory_thresholds"].get("macd_lift_min", 0):
            return False, "macd_flat", 0.0
        if indicators.get("rsi_slope", 0) < cfg["trajectory_thresholds"].get("rsi_slope_min", 0):
            return False, "rsi_flat", 0.0

    if cfg.get("require_recovery_odds", True) and recovery_odds < cfg.get("min_recovery_probability", 0.5):
        return False, "recovery_odds_low", 0.0

    # Liquidation buffer
    last_price = indicators.get("latest_close")
    if not _liquidation_buffer_ok(liquidation_price, last_price, cfg.get("liquidation_buffer_pct", 5.0)):
        return False, "liq_buffer_too_close", 0.0

    return True, "ok", next_notional
