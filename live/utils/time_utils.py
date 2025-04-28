# /home/signal/market6/live/utils/time_utils.py

def closest_candle(candles, target_ts):
    """
    Return the candle whose timestamp is closest to `target_ts` (unix).
    Assumes candle has a 'timestamp' field (unix).
    """
    return min(candles, key=lambda c: abs(c["timestamp"] - target_ts))
