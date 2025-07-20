from .base_adapter import BaseExchangeAdapter
import random
import time

class MockAdapter(BaseExchangeAdapter):
    def __init__(self, api_key="mock", api_secret="mock", **kwargs):
        pass

    def get_balance(self, asset: str) -> float:
        return 10000.0  # Simulate always available balance

    def place_order(self, symbol: str, side: str, quantity: float,
                    order_type: str = "market", price: float = None) -> dict:
        return {
            "order_id": f"MOCK-{random.randint(1000, 9999)}",
            "symbol": symbol,
            "side": side,
            "status": "filled",
            "price": price or "market",
            "quantity": quantity,
            "timestamp": int(time.time())
        }

    def get_order_status(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "filled"}

    def cancel_order(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "canceled"}
