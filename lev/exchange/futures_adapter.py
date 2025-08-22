from __future__ import annotations
from typing import Any, Dict, Optional
import ccxt, json
from pathlib import Path
import time

# ---------- helpers ----------
def _load_creds() -> Dict[str, Any]:
    p = Path("config/binance_futures_testnet.json")
    return json.loads(p.read_text())

def _unified(symbol: str) -> str:
    # "BTCUSDT" -> "BTC/USDT:USDT" for ccxt USDT-M
    if "/" in symbol:
        return symbol
    base = symbol.replace("USDT", "")
    return f"{base}/USDT:USDT"

# ---------- init & modes ----------
def init_exchange(cfg: Dict[str, Any]):
    creds = _load_creds()
    ex = ccxt.binanceusdm({
        "apiKey": creds["api_key"],
        "secret": creds["api_secret"],
        "enableRateLimit": True,
        "options": {"defaultType": "future"},
    })
    ex.set_sandbox_mode(True)
    ex.load_markets()
    # Set position mode (hedged vs one-way)
    if cfg.get("hedged_mode", True):
        try:
            ex.set_position_mode(True)  # True = Hedge Mode
        except Exception:
            pass  # some ccxt versions require raw call; ignore if already set
    return ex

def set_symbol_leverage(ex, symbol: str, lev: int):
    ex.set_leverage(int(lev), _unified(symbol))

# ---------- positions & risk ----------
def get_positions(ex, symbol: str) -> Dict[str, Any]:
    ps = ex.fetch_positions([_unified(symbol)])
    qty = 0.0
    entry = None
    lev = None
    notional = 0.0
    for p in ps:
        amt = float(p.get("contracts") or 0)
        if amt == 0:
            continue
        qty += amt
        lev = int(p.get("leverage") or 0)
        entry_price = float(p.get("entryPrice") or 0) or None
        if entry is None and entry_price:
            entry = entry_price
        notional += abs(amt) * float(p.get("markPrice") or entry_price or 0)
    return {
        "qty": qty,
        "entry_price": entry,
        "notional": notional,
        "leverage": lev,
        "margin_mode": "isolated",      # ccxt doesn’t map cleanly
        "completed_safety_orders_count": 0,
    }

def get_liquidation_price(ex, symbol: str, position: Dict[str, Any]) -> Optional[float]:
    try:
        mkt = ex.market(_unified(symbol))
        raw = ex.fapiPrivate_get_positionrisk({"symbol": mkt["id"]})
        if raw and isinstance(raw, list):
            liq = raw[0].get("liquidationPrice")
            return float(liq) if liq not in (None, "", "0") else None
    except Exception:
        return None
    return None

def account_notional_exposure(ex) -> float:
    total = 0.0
    for p in ex.fetch_positions():
        amt = float(p.get("contracts") or 0)
        price = float(p.get("markPrice") or p.get("entryPrice") or 0)
        total += abs(amt) * price
    return total

# ---------- orders ----------
def _ticker_price(ex, symbol: str) -> float:
    return float(ex.fetch_ticker(_unified(symbol))["last"])

def _qty_from_notional(ex, symbol: str, target_notional: float) -> float:
    price = _ticker_price(ex, symbol)
    if price <= 0:
        raise RuntimeError("Bad price")
    qty = target_notional / price
    mkt = ex.market(_unified(symbol))
    min_qty = mkt.get("limits", {}).get("amount", {}).get("min", 0)
    if qty < min_qty:
        qty = float(min_qty)
    return float(ex.amount_to_precision(_unified(symbol), qty))

def place_order(
    ex,
    symbol: str,
    target_notional: float,
    side: str = "buy",                # "buy" long, "sell" short
    reduce_only: bool = False,
    dry_run: bool = False,
):
    unified = _unified(symbol)
    qty = _qty_from_notional(ex, symbol, target_notional)
    if dry_run:
        return {
            "dry_run": True, "symbol": unified, "side": side, "amount": qty,
            "note": "order skipped (dry_run)"
        }
    params = {}
    if reduce_only:
        params["reduceOnly"] = True
    return ex.create_order(symbol=unified, type="market", side=side.lower(), amount=qty, params=params)
