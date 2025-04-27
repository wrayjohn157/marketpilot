# /market7/dashboard_backend/dca_status.py

from fastapi import APIRouter
from pathlib import Path
import json
from datetime import datetime

from dca.utils.entry_utils import get_live_3c_trades
from config.config_loader import PATHS

# === Paths ===
today = datetime.utcnow().strftime("%Y-%m-%d")
DCA_LOG_PATH = PATHS["live_logs"] / today / "dca_log.jsonl"
SNAPSHOT_BASE = PATHS["snapshots"]

# === Sparkline loader ===
def get_sparkline_data(symbol: str, date: str = None) -> list:
    try:
        date = date or datetime.utcnow().strftime("%Y-%m-%d")
        path = SNAPSHOT_BASE / date / f"{symbol}_15m_klines.json"
        if not path.exists():
            return []
        with open(path) as f:
            klines = json.load(f)
        return [float(k[4]) for k in klines[-30:]]  # last 30 closes
    except Exception as e:
        print(f"[sparkline] Error loading {symbol}: {e}")
        return []

# === FastAPI router ===
router = APIRouter()

@router.get("/dca-trades-active")
def get_dca_trades_active():
    # Load active trades from 3Commas
    active_trades = get_live_3c_trades()
    active_deal_map = {}
    for t in active_trades:
        pair = t.get("pair", "")
        symbol = pair.replace("USDT_", "")
        deal_id = t.get("id")
        active_deal_map[symbol] = deal_id

    # Load local DCA log entries
    if not DCA_LOG_PATH.exists():
        return {"count": 0, "dca_trades": []}

    latest_by_symbol = {}
    with open(DCA_LOG_PATH, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                symbol = data.get("short_symbol") or data.get("symbol", "").replace("USDT_", "")
                ts = data.get("timestamp")

                if symbol in active_deal_map:
                    existing = latest_by_symbol.get(symbol)
                    if not existing or ts > existing.get("timestamp", ""):
                        data["deal_id"] = active_deal_map[symbol]
                        data["sparkline_data"] = get_sparkline_data(symbol)
                        latest_by_symbol[symbol] = data
            except Exception:
                continue

    results = list(latest_by_symbol.values())
    return {"count": len(results), "dca_trades": results}
