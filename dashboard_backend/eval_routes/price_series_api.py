import json
from pathlib import Path

from fastapi import APIRouter, Query

from config import get_path
from utils.redis_manager import RedisKeyManager, get_redis_manager

# ~/market7/dashboard_backend/eval_routes/price_series_api.py

router = APIRouter()

BASE_DIR = get_path("base") / "data/snapshots"


@router.get_cache("/price-series")
def get_price_series(
    symbol: str = Query(..., description="e.g. ARB"),
    interval: str = Query("15m", description="e.g. 15m, 1h, 4h"),
    date: str = None,
):
    try:
        symbol = symbol.upper()
        filename = f"{symbol}_{interval}_klines.json"

        if date:
            file_path = BASE_DIR / date / filename
        else:
            # Use latest available folder
            dated_folders = sorted(BASE_DIR.glob("20*"), reverse=True)
            file_path = dated_folders[0] / filename if dated_folders else None

        if not file_path or not file_path.exists():
            return {"error": f"Price data not found for {symbol} {interval}"}

        with open(file_path) as f:
            raw = json.load(f)

        # Return simplified series: [{ time, price }]
        return {
            "symbol": symbol,
            "interval": interval,
            "date": file_path.parent.name,
            "series": [
                {
                    "timestamp": x[0],  # open time
                    "open": float(x[1]),
                    "high": float(x[2]),
                    "low": float(x[3]),
                    "close": float(x[4]),
                }
                for x in raw
            ],
        }

    except Exception as e:
        return {"error": str(e)}
