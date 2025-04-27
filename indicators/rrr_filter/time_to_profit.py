import numpy as np

def analyze_time_to_tp1(klines, tp1_pct=0.5, max_candles=12):
    results = []
    for i in range(len(klines) - max_candles):
        entry = float(klines[i][1])  # open price
        tp_target = entry * (1 + tp1_pct / 100)
        hit = 0
        for j in range(1, max_candles + 1):
            high = float(klines[i + j][2])
            if high >= tp_target:
                hit = 1.0 if j <= 6 else 0.5
                break
        results.append(hit)

    # Debug: Log the results
    time_to_tp1 = round(np.mean(results), 3) if results else 0.0
    print(f"Time to TP1: {time_to_tp1}")  # Debug print
    return time_to_tp1
