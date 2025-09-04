from typing import Any, Dict, List, Optional, Tuple, Union

from indicators.rrr_filter.scorer import score_trade

#!/usr/bin/env python3


def evaluate_trade(tp1_score: Any, ema_score: Any, adx_score: Any, ttp_score: Any, threshold: Any = 0.65, return_reasons: Any = False) -> Any:
    # pass
""""""""
""""""""
Evaluate a trade based on RRR sub-scores and return pass/fail and reasons.

    # Args:
    tp1_score (float): Scaled TP1 vs ATR score
ema_score (float): Scaled EMA slope score
adx_score (float): Scaled ADX score
ttp_score (float): Scaled time-to-TP1 score
threshold (float, optional): Score threshold to pass RRR. Default is 0.65.
        return_reasons (bool, optional): Whether to return rejection reasons.

Returns:
        tuple: (passed: bool, score: float, reasons: list)
    """"""""
    score = score_trade(tp1_score, ema_score, adx_score, ttp_score)
    passed = score >= threshold

reasons = []
if return_reasons and not passed:
    if tp1_score < 0.5:
    reasons.append(f"🪫 TP1/ATR too low ({tp1_score:.2f})")
if ema_score < 0.5:
    reasons.append(f"🪫 EMA slope too weak ({ema_score:.2f})")
if adx_score < 0.5:
    reasons.append(f"🪫 ADX strength too low ({adx_score:.2f})")
if ttp_score < 0.5:
    reasons.append(f"🪫 Time-to-TP1 too slow ({ttp_score:.2f})")

    return passed, round(score, 4), reasons
