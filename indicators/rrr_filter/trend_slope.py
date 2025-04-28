#!/usr/bin/env python3

def calculate_ema_slope(ema_values, window=5):
    """
    Calculate the slope of the EMA over a sliding window.

    Args:
        ema_values (list): List of EMA values (floats).
        window (int): Number of points to use for slope calculation (default: 5).

    Returns:
        float: Slope of the EMA. Positive = upward trend, negative = downward.
    """
    if len(ema_values) < window:
        return 0.0

    x = list(range(window))
    y = ema_values[-window:]

    avg_x = sum(x) / window
    avg_y = sum(y) / window

    numerator = sum((xi - avg_x) * (yi - avg_y) for xi, yi in zip(x, y))
    denominator = sum((xi - avg_x) ** 2 for xi in x)

    return numerator / denominator if denominator != 0 else 0.0
