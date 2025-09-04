from typing import Dict, Any

import math

# /market7/core/fork_scorer.py

def score_fork(symbol: str, timestamp: int, indicators: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes fork score for a given symbol and indicator snapshot.

    Args:
        symbol (str): Symbol being scored (e.g., "USDT_XRP").
        timestamp (int): Timestamp of fork candidate.
        indicators (dict): Snapshot of indicators (MACD, RSI, etc).
        config (dict): Scoring config (from fork_score_config.yaml or strategy).

    Returns:
        dict: {
            "symbol": str,
            "timestamp": int,
            "score": float,
            "score_components": dict,
            "passed": bool,
            "reason": str
        }
    """
    score_components = {}
    total_score = 0.0

    for key, weight in config.get("weights", {}).items():
        value = indicators.get(key, 0)
        component_score = value * weight
        score_components[key] = round(component_score, 4)
        total_score += component_score

    passed = total_score >= config.get("min_score", 0.7)
    reason = "passed" if passed else "below threshold"

    return {
        "symbol": symbol,
        "timestamp": timestamp,
        "score": round(total_score, 4),
        "score_components": score_components,
        "passed": passed,
        "reason": reason
    }

def score_fork_with_strategy(symbol: str, timestamp: int, indicators: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
    result = score_fork(symbol, timestamp, indicators, strategy)
    result["btc_multiplier"] = strategy.get("btc_multiplier", 1.0)
    result["source"] = strategy.get("name", "unknown")
    return result

if __name__ == "__main__":
    example_indicators = {
        "macd_histogram": 0.02,
        "rsi_recovery": 0.7,
        "ema_price_reclaim": 1,
    }

    example_config = {
        "weights": {
            "macd_histogram": 0.3,
            "rsi_recovery": 0.4,
            "ema_price_reclaim": 0.3,
        },
        "min_score": 0.7
    }

    result = score_fork("USDT_ABC", 1714678900000, example_indicators, example_config)
    print(result)
