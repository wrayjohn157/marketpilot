"""
Fork SAFU Evaluator - Simplified version for MarketPilot
"""


def get_safu_exit_decision(symbol, current_price, entry_price, volume):
    """Get SAFU exit decision for a trade"""
    # Simplified SAFU logic
    if current_price > entry_price * 1.02:  # 2% profit
        return "HOLD"
    elif current_price < entry_price * 0.98:  # 2% loss
        return "EXIT"
    else:
        return "HOLD"


def load_safu_exit_model():
    """Load SAFU exit model"""
    return {"model_loaded": True, "version": "1.0"}
