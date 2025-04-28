import numpy as np
import ta

def compute_indicators(candles):
    """
    Accepts a list of candle dicts (each with keys: "open", "high", "low", "close", "volume").
    Returns a single dict of indicators computed from the last candle.
    (This function always returns a dict—never a list.)
    """
    if not candles or len(candles) == 0:
        return {}
    
    try:
        # We only use the last candle for indicators.
        c = candles[-1]

        # Create single-element numpy arrays from the candle values.
        close = np.array([c["close"]], dtype=np.float64)
        high = np.array([c["high"]], dtype=np.float64)
        low = np.array([c["low"]], dtype=np.float64)
        volume = np.array([c["volume"]], dtype=np.float64)

        # Calculate indicators using the ta library. For a one-element array, we use the last value.
        rsi = ta.momentum.RSIIndicator(close).rsi()[-1]
        macd = ta.trend.MACD(close)
        adx = ta.trend.ADXIndicator(high, low, close)
        ema_50 = ta.trend.EMAIndicator(close, window=50).ema_indicator()[-1]
        ema_200 = ta.trend.EMAIndicator(close, window=200).ema_indicator()[-1]

        return {
            "RSI14": float(rsi),
            "MACD": float(macd.macd()[-1]),
            "MACD_signal": float(macd.macd_signal()[-1]),
            "MACD_diff": float(macd.macd_diff()[-1]),
            "ADX14": float(adx.adx()[-1]),
            "EMA50": float(ema_50),
            "EMA200": float(ema_200)
        }
        
    except Exception as e:
        print(f"[ERROR] Indicator calc failed: {e}")
        return {}
