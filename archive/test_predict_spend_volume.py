import sys
from pathlib import Path

# Add the root of the project to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dca.utils.spend_predictor import predict_spend_volume

# ✅ All 16 required model features
test_input = {
    "entry_score": 0.7664,
    "current_score": 0.2815,
    "drawdown_pct": 2.4924,
    "safu_score": 0.6,
    "macd_lift": 0.00005,
    "rsi": 50.95,
    "rsi_slope": -3.0827,
    "adx": 19.09,
    "tp1_shift": 2.8,
    "recovery_odds": 0.96,
    "confidence_score": 0.82,
    "zombie_tagged": False,
    "btc_rsi": 48.43,
    "btc_macd_histogram": 5.632,
    "btc_adx": 8.17,
    "btc_status": "neutral"  # or "bullish", "bearish" #"btc_status": 1  # 1 = SAFE, 0 = UNSAFE
}

# 🔮 Run prediction
volume = predict_spend_volume(test_input)

# 🖨️ Show result
print(f"📦 Predicted DCA Volume: {volume:.2f} USDT")
