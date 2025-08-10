from typing import Any, Dict

# TODO: wire to your real exchange (ccxt or native SDK)
def init_exchange(cfg: Dict[str, Any]):
    # return an exchange client
    return object()

def set_symbol_leverage(ex, symbol: str, lev: int): ...
def get_positions(ex, symbol: str) -> Dict[str, Any]:
    # return dict with keys: qty, entry_price, notional, margin_mode, leverage
    return {"qty": 0.0, "entry_price": None, "notional": 0.0, "leverage": None, "margin_mode": "isolated"}

def get_liquidation_price(ex, symbol: str, position: Dict[str, Any]) -> float | None:
    # implement exchange-specific liq calc or read from API
    return None

def account_notional_exposure(ex) -> float:
    # sum open positions' notional
    return 0.0

def place_order(ex, symbol: str, target_notional: float):
    # compute qty from target_notional and market price; submit order
    pass
