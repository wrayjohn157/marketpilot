from .binance_adapter import BinanceAdapter
from .mock_adapter import MockAdapter

def get_adapter(name: str, api_key: str, api_secret: str, **kwargs):
    if name == "binance":
        return BinanceAdapter(api_key, api_secret, **kwargs)
    elif name == "mock":
        return MockAdapter()
    else:
        raise ValueError(f"Unknown adapter: {name}")
