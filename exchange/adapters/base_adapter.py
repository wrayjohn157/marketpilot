from abc import ABC, abstractmethod

class BaseExchangeAdapter(ABC):
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret

    @abstractmethod
    def get_balance(self, asset: str) -> float:
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: float,
                    order_type: str = "market", price: float = None) -> dict:
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> dict:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> dict:
        pass
