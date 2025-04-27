def calculate_ema_slope(ema_values, window=5):
    if len(ema_values) < window:
        return 0.0
    x = list(range(window))
    y = ema_values[-window:]
    avg_x = sum(x) / window
    avg_y = sum(y) / window
    numerator = sum((x[i] - avg_x) * (y[i] - avg_y) for i in range(window))
    denominator = sum((x[i] - avg_x) ** 2 for i in range(window))
    slope = numerator / denominator if denominator != 0 else 0.0
    return slope
