from indicators.rrr_filter.scorer import score_trade

def evaluate_trade(tp1_score, ema_score, adx_score, ttp_score, threshold=0.65, return_reasons=False):
    """
    Evaluate a trade based on RRR sub-scores and return pass/fail and reasons.

    Args:
        tp1_score (float): Scaled TP1 vs ATR score
        ema_score (float): Scaled EMA slope score
        adx_score (float): Scaled ADX score
        ttp_score (float): Scaled time-to-TP1 score
        threshold (float): Score threshold to pass RRR
        return_reasons (bool): Whether to include rejection reasons

    Returns:
        (bool, float, list): Pass/fail, score, and reasons (empty if not requested)
    """
    score = score_trade(tp1_score, ema_score, adx_score, ttp_score)
    passed = score >= threshold

    reasons = []
    if not passed:
        if tp1_score < 0.5:
            reasons.append(f"🪫 TP1/ATR too low ({tp1_score:.2f})")
        if ema_score < 0.5:
            reasons.append(f"🪫 EMA slope too weak ({ema_score:.2f})")
        if adx_score < 0.5:
            reasons.append(f"🪫 ADX strength too low ({adx_score:.2f})")
        if ttp_score < 0.5:
            reasons.append(f"🪫 Time-to-TP1 too slow ({ttp_score:.2f})")

    return passed, round(score, 4), reasons if return_reasons else []
