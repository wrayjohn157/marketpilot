# /market7/dashboard_backend/dca_status.py

from fastapi import APIRouter
from pathlib import Path
import json
from datetime import datetime

from dca.utils.entry_utils import get_live_3c_trades
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


# === Paths ===
today = datetime.utcnow().strftime("%Y-%m-%d")
DCA_LOG_PATH = get_path("live_logs") / today / "dca_log.jsonl"
SNAPSHOT_BASE = PATHS["kline_snapshots"]
RECOVERY_SNAPSHOT_PATH = Path("/home/signal/market7/ml/datasets/recovery_snapshots")

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

# === Load latest snapshot by deal_id ===
def load_latest_snapshot(deal_id):
    try:
        files = list(RECOVERY_SNAPSHOT_PATH.glob(f"*_{deal_id}.jsonl"))
        if not files:
            return None
        latest_lines = []
        for file in files:
            with open(file) as f:
                lines = f.readlines()
                if lines:
                    latest_lines.append(json.loads(lines[-1]))
        return latest_lines[-1] if latest_lines else None
    except Exception as e:
        print(f"[snapshot] Error loading {deal_id}: {e}")
        return None

# === FastAPI router ===
router = APIRouter()

@router.get("/dca-trades-active")
def get_dca_trades_active():
    active_trades = get_live_3c_trades()
    symbol_map = {}

    for t in active_trades:
        pair = t.get("pair", "")
        symbol = pair.replace("USDT_", "")
        deal_id = t.get("id")

        avg_price = float(t.get("average_enter_price") or t.get("bought_average_price") or t.get("base_order_average_price") or 0)
        curr_price = float(t.get("current_price") or 0)
        spent = float(t.get("bought_volume") or 0)

        qty = spent / avg_price if avg_price > 0 else 0
        open_pnl = (curr_price - avg_price) * qty if qty > 0 else 0

        symbol_map[symbol] = {
            "deal_id": deal_id,
            "symbol": pair,
            "step": t.get("completed_safety_orders_count", 0),
            "current_price": curr_price,
            "avg_entry_price": round(avg_price, 8),
            "open_pnl": round(open_pnl, 2),
        }

    # Enrich with local DCA logs
    if DCA_LOG_PATH.exists():
        with open(DCA_LOG_PATH, "r") as f:
            for line in f:
                try:
                    log = json.loads(line)
                    symbol = log.get("short_symbol") or log.get("symbol", "").replace("USDT_", "")
                    if symbol in symbol_map:
                        symbol_map[symbol].update(log)
                except Exception:
                    continue

    # Enrich with sparkline + snapshot metrics
    for symbol, trade in symbol_map.items():
        deal_id = trade.get("deal_id")
        trade["sparkline_data"] = get_sparkline_data(symbol.upper())

        snap = load_latest_snapshot(deal_id)
        if snap:
            trade.update({
                "entry_score": snap.get("entry_score"),
                "current_score": snap.get("current_score"),
                "confidence_score": snap.get("confidence_score"),
                "recovery_odds": snap.get("recovery_odds"),
                "safu_score": snap.get("safu_score"),
                "tp1_shift": snap.get("tp1_shift"),
                "drawdown_pct": snap.get("drawdown_pct"),
            })

    return {
        "count": len(symbol_map),
        "dca_trades": list(symbol_map.values())
    }
