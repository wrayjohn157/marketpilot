#!/usr/bin/env python3

def score_trade(tp1_score: Any, ema_score: Any, adx_score: Any, ttp_score: Any, weights: Any = None) -> Any:
    """
    Calculates the weighted RRR (Risk Reward Ratio) score for a trade.

    Args:
        tp1_score (float): Normalized score for TP1 vs ATR.
        ema_score (float): Normalized EMA slope strength.
        adx_score (float): Normalized ADX strength.
        ttp_score (float): Normalized Time-to-TP1 score.
        weights (dict, optional): Custom weightings for each component.

    Returns:
        float: Final weighted score, rounded to 4 decimals.
    """
    if weights is None:
        weights = {
            "tp1_vs_atr": 0.30,    # Default weighting
            "ema_slope": 0.25,
            "adx_strength": 0.25,
            "time_to_tp1": 0.20
        }

    score = (
        tp1_score * weights.get("tp1_vs_atr", 0) +
        ema_score * weights.get("ema_slope", 0) +
        adx_score * weights.get("adx_strength", 0) +
        ttp_score * weights.get("time_to_tp1", 0)
    )

    return round(score, 4)
