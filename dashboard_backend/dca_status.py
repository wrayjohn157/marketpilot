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
    # Load live trades from 3Commas
    active_trades = get_live_3c_trades()
    symbol_map = {}

    for t in active_trades:
        pair = t.get("pair", "")
        symbol = pair.replace("USDT_", "")
        deal_id = t.get("id")
        symbol_map[symbol] = {
            "deal_id": deal_id,
            "symbol": pair,
            "step": t.get("completed_safety_orders_count", 0),
            "current_price": t.get("current_price"),
            "avg_entry_price": t.get("average_enter_price"),
        }

    # Enrich with local DCA logs if available
    if DCA_LOG_PATH.exists():
        with open(DCA_LOG_PATH, "r") as f:
            for line in f:
                try:
                    log = json.loads(line)
                    symbol = log.get("short_symbol") or log.get("symbol", "").replace("USDT_", "")
                    if symbol in symbol_map:
                        symbol_map[symbol].update(log)
                        symbol_map[symbol]["sparkline_data"] = get_sparkline_data(symbol)
                except Exception:
                    continue

    return {
        "count": len(symbol_map),
        "dca_trades": list(symbol_map.values())
    }
