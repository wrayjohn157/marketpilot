from typing import Dict, Tuple, Optional

from __future__ import annotations

def _indicator_ok(ind: Dict, cfg: Dict, side: str) -> Tuple[bool, str]:
    th = cfg.get("indicator_thresholds", {})
    rsi = ind.get("rsi")
    macd_hist = ind.get("macd_histogram")
    adx = ind.get("adx")
    if cfg.get("require_indicator_health", True):
        if side == "long":
            if rsi is not None and rsi < th.get("rsi_min", 40): return False, "rsi_low"
            if macd_hist is not None and macd_hist < th.get("macd_hist_min", 0): return False, "macd_bearish"
            if adx is not None and adx < th.get("adx_min", 10): return False, "adx_weak"
        else:  # short
            # mirror: want bearish momentum / overbought rejection
            if rsi is not None and rsi > cfg.get("short_entry", {}).get("rsi_max", 60): return False, "rsi_not_high"
            if macd_hist is not None and macd_hist > cfg.get("short_entry", {}).get("macd_hist_max", 0): return False, "macd_not_bearish"
            if adx is not None and adx < th.get("adx_min", 10): return False, "adx_weak"
    return True, ""

def _trajectory_ok(ind: Dict, cfg: Dict, side: str) -> Tuple[bool, str]:
    if not cfg.get("use_trajectory_check", True):
        return True, ""
    tt = cfg.get("trajectory_thresholds", {})
    if side == "long":
        if ind.get("macd_lift", 0) < tt.get("macd_lift_min", 0): return False, "macd_flat"
        if ind.get("rsi_slope", 0) < tt.get("rsi_slope_min", 0): return False, "rsi_flat"
    else:
        # inverse slopes for shorts
        if ind.get("macd_lift", 0) > -abs(tt.get("macd_lift_min", 0)): return False, "macd_not_falling"
        if ind.get("rsi_slope", 0) > -abs(tt.get("rsi_slope_min", 0)): return False, "rsi_not_falling"
    return True, ""

def _liq_buffer_ok(liq_price: Optional[float], last_price: Optional[float], buf_pct: float, side: str) -> bool:
    if not liq_price or not last_price:
        return True
    dist = abs((last_price - liq_price) / last_price) * 100.0
    return dist >= buf_pct

def _next_notional(cfg: Dict, position: Dict, step_idx: int) -> float:
    table = cfg.get("so_notional_table", [])
    if step_idx >= len(table):
        return 0.0
    return float(table[step_idx])

def should_add_to_position(
    cfg: Dict,
    side: str,
    symbol: str,
    position: Dict,
    indicators: Dict,
    btc_status: str,
    recovery_odds: float,
    confidence: float,
    liquidation_price: Optional[float],
) -> Tuple[bool, str, float]:
    # per-position cap
    step = int(position.get("completed_safety_orders_count", 0))
    next_notional = _next_notional(cfg, position, step)
    if next_notional <= 0:
        return False, "max_so", 0.0

    if position.get("notional", 0.0) + next_notional > cfg.get("max_trade_notional", 10_000):
        return False, "exceeds_position_cap", 0.0

    # indicator health
    ok, reason = _indicator_ok(indicators, cfg, side)
    if not ok:
        return False, reason, 0.0

    # trajectory / odds
    ok, reason = _trajectory_ok(indicators, cfg, side)
    if not ok:
        return False, reason, 0.0

    if cfg.get("require_recovery_odds", True) and recovery_odds < cfg.get("min_recovery_probability", 0.5):
        return False, "recovery_odds_low", 0.0

    # liquidation buffer
    last_price = indicators.get("latest_close")
    if not _liq_buffer_ok(liquidation_price, last_price, cfg.get("liquidation_buffer_pct", 5.0), side):
        return False, "liq_buffer_too_close", 0.0

    # BTC filter (simple example—tune to your status values)
    if side == "long" and str(btc_status).lower().startswith("unsafe"):
        return False, "btc_filter_block", 0.0
    if side == "short" and str(btc_status).lower().startswith("safe"):
        return False, "btc_filter_block", 0.0

    return True, "ok", next_notional
