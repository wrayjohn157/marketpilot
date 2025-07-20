from .base_adapter import BaseExchangeAdapter
from binance.client import Client

class BinanceAdapter(BaseExchangeAdapter):
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        super().__init__(api_key, api_secret)
        self.client = Client(api_key, api_secret)

    def get_balance(self, asset: str) -> float:
        balance = self.client.get_asset_balance(asset)
        return float(balance['free']) if balance else 0.0

    def place_order(self, symbol: str, side: str, quantity: float,
                    order_type: str = "market", price: float = None) -> dict:
        if order_type == "market":
            if side.lower() == "buy":
                return self.client.order_market_buy(symbol=symbol, quantity=quantity)
            else:
                return self.client.order_market_sell(symbol=symbol, quantity=quantity)
        elif order_type == "limit" and price:
            if side.lower() == "buy":
                return self.client.order_limit_buy(symbol=symbol, quantity=quantity, price=str(price))
            else:
                return self.client.order_limit_sell(symbol=symbol, quantity=quantity, price=str(price))
        else:
            raise ValueError("Unsupported order type or missing price")

    def get_order_status(self, order_id: str) -> dict:
        return self.client.get_order(orderId=order_id)

    def cancel_order(self, order_id: str) -> dict:
        return self.client.cancel_order(orderId=order_id)
