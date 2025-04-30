# /home/signal/market7/dashboard_backend/dca_trades_api.py

from fastapi import APIRouter
from core.redis_utils import redis_client
from dca.utils.entry_utils import get_live_3c_trades
from pathlib import Path
import json

router = APIRouter()


# === Load confidence map from Redis ===
def load_confidence_map():
    try:
        raw = redis_client.get("confidence_list")
        if raw:
            return {item["symbol"]: item for item in json.loads(raw)}
    except:
        pass
    return {}


# === Load score from Redis by kind: entry, current, safu ===
def load_score_from_redis(symbol, deal_id, kind="entry"):
    key = f"score:{symbol}:{deal_id}:{kind}"
    val = redis_client.get(key)
    try:
        return round(float(val), 4) if val else None
    except:
        return None


# === Get sparkline data from saved files ===
def get_sparkline_data(symbol):
    file = Path(f"/home/signal/market7/data/rolling/{symbol}_sparkline.json")
    if file.exists():
        try:
            with open(file) as f:
                return json.load(f)
        except:
            return []
    return []


# === Main route: DCA trades with enrichment ===
@router.get("/dca-trades-enriched")
def get_dca_trades_active():
    trades = get_live_3c_trades()
    confidence_map = load_confidence_map()

    enriched = []

    for trade in trades:
        symbol = trade.get("symbol")
        deal_id = trade.get("deal_id")

        if not symbol or not deal_id:
            continue

        # Skip trades that haven't entered
        if not trade.get("avg_entry_price"):
            continue

        confidence = confidence_map.get(symbol, {})

        enriched_trade = {
            **trade,
            "confidence_score": confidence.get("confidence_score"),
            "rejection_reason": confidence.get("rejection_reason"),
            "entry_score": load_score_from_redis(symbol, deal_id, "entry"),
            "current_score": load_score_from_redis(symbol, deal_id, "current"),
            "safu_score": load_score_from_redis(symbol, deal_id, "safu"),
            "sparkline_data": get_sparkline_data(symbol),
        }

        enriched.append(enriched_trade)

    return enriched
