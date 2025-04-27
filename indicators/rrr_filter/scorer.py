def score_trade(tp1_score, ema_score, adx_score, ttp_score, weights=None):
    if weights is None:
        weights = {
            "tp1_vs_atr": 0.30, #was 0.25
            "ema_slope": 0.25, #was 0.20
            "adx_strength": 0.25, #was 0.15
            "time_to_tp1": 0.20 #was 0.40
        }
    score = (
        tp1_score * weights["tp1_vs_atr"] +
        ema_score * weights["ema_slope"] +
        adx_score * weights["adx_strength"] +
        ttp_score * weights["time_to_tp1"]
    )
    return round(score, 4)
