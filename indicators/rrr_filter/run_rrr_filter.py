#!/usr/bin/env python3
import redis
import json
from .evaluate import evaluate_trade
from .time_to_profit import analyze_time_to_tp1
from .trend_slope import calculate_ema_slope

# Redis setup
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def run_rrr_filter(symbol, klines, atr, adx, ema_values):
    # TP1 vs ATR score
    tp1_target = 0.5
    tp1_score = min(max(tp1_target / atr, 0), 1) if atr else 0.0

    # EMA slope score
    ema_slope = calculate_ema_slope(ema_values)
    ema_score = min(max(ema_slope / 0.02, 0), 1)

    # ADX strength score
    adx_score = min(max((adx - 15) / 10, 0), 1) if adx else 0.0

    # Time-to-TP1 score
    ttp_score = analyze_time_to_tp1(klines)

    # Update Redis (merge Time_to_TP1 into existing data)
    redis_key = f"{symbol}_1h"
    existing_data = r.get(redis_key)
    if existing_data:
        try:
            existing_data = json.loads(existing_data)
        except json.JSONDecodeError:
            existing_data = {}
    else:
        existing_data = {}

    existing_data["Time_to_TP1"] = ttp_score
    r.set(redis_key, json.dumps(existing_data))
    print(f"✅ Saved Time_to_TP1 for {symbol}: {ttp_score}")

    # Evaluate
    passed, score, reasons = evaluate_trade(tp1_score, ema_score, adx_score, ttp_score)

    print(f"🔎 RRR Evaluation for {symbol}")
    print(f" - TP1 Score:  {tp1_score:.3f}")
    print(f" - EMA Score:  {ema_score:.3f}")
    print(f" - ADX Score:  {adx_score:.3f}")
    print(f" - TTP Score:  {ttp_score:.3f}")
    print(f" - Final Score: {score:.3f} → {'✅ PASS' if passed else '❌ FAIL'}")
    if not passed and reasons:
        for reason in reasons:
            print(f"    🪫 {reason}")

    return {
        "symbol": symbol,
        "score": round(score, 4),
        "passed": passed,
        "reasons": reasons,
        "details": {
            "tp1_score": round(tp1_score, 3),
            "ema_score": round(ema_score, 3),
            "adx_score": round(adx_score, 3),
            "ttp_score": round(ttp_score, 3),
            "ema_slope": round(ema_slope, 5),
            "adx_raw": round(adx, 2) if adx else None,
            "atr": round(atr, 5) if atr else None
        }
    }

# Optional CLI debug runner
if __name__ == "__main__":
    symbol = "ETH"

    # Load klines
    kline_key = f"{symbol}_15m_klines"
    klines_raw = r.lrange(kline_key, 0, -1)
    klines = [json.loads(k) for k in klines_raw] if klines_raw else []
    if not klines or len(klines) < 20:
        print(f"⚠️ Insufficient klines for {symbol}")
        exit()

    # Load indicators
    info_key = f"{symbol}_1h"
    info_raw = r.get(info_key)
    info = json.loads(info_raw) if info_raw else {}

    atr = info.get("ATR")
    adx = info.get("ADX14")
    ema_values = [info.get("EMA50"), info.get("EMA200")]

    print(f"\n⚙️ Running RRR filter for {symbol}")
    print(f" - ATR: {atr}")
    print(f" - ADX: {adx}")
    print(f" - EMA50: {ema_values[0]}")
    print(f" - EMA200: {ema_values[1]}")
    print("")

    run_rrr_filter(symbol, klines, atr, adx, ema_values)
