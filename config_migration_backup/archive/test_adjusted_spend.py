import sys
from pathlib import Path

# Add parent dir to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dca.utils.spend_predictor import predict_spend_volume, adjust_volume

# === Sample input with high prediction but small initial spend
test_input = {
    "entry_score": 0.7664,
    "current_score": 0.2815,
    "drawdown_pct": 2.5,
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
    "btc_status": "bullish"  # or "bullish", "bearish" #"btc_status": 1
}

# Simulate small trade
total_spent = 50.00
max_budget = 2000

# Run prediction
predicted = predict_spend_volume(test_input)
adjusted = adjust_volume(predicted, total_spent, max_budget=max_budget,
                         drawdown_pct=test_input["drawdown_pct"],
                         tp1_shift_pct=test_input["tp1_shift"])

print(f"📦 Raw Prediction: {predicted:.2f} USDT")
print(f"🎯 Adjusted Volume: {adjusted:.2f} USDT")
