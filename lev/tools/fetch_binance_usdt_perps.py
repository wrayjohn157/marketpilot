#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, csv
from pathlib import Path
from typing import Dict, Any
import ccxt

def build_exchange(testnet: bool) -> ccxt.binanceusdm:
    ex = ccxt.binanceusdm({
        "enableRateLimit": True,
        "options": {"defaultType": "future"},  # ok to leave; we'll filter by 'swap'
    })
    ex.set_sandbox_mode(testnet)
    ex.load_markets()
    return ex

def extract_perps(ex: ccxt.binanceusdm):
    markets = ex.markets  # loaded
    rows = []
    for sym, m in markets.items():
        # USDT-M PERPETUALS in CCXT: type == 'swap', linear == True
        if m.get("type") != "swap":
            continue
        if not m.get("linear"):  # exclude coin-M
            continue
        info: Dict[str, Any] = m.get("info", {}) or {}
        if info.get("contractType") != "PERPETUAL":
            continue
        if info.get("status") != "TRADING":
            continue

        # Precisions & limits
        price_prec = (m.get("precision") or {}).get("price")
        amt_prec   = (m.get("precision") or {}).get("amount")
        limits     = m.get("limits") or {}
        min_amt    = (limits.get("amount") or {}).get("min")
        min_cost   = (limits.get("cost") or {}).get("min")
        # Filters
        filters = {f.get("filterType"): f for f in info.get("filters", []) if isinstance(f, dict)}
        tick_size = float(filters.get("PRICE_FILTER", {}).get("tickSize", 0) or 0)
        step_size = float(filters.get("LOT_SIZE", {}).get("stepSize", 0) or 0)

        rows.append({
            "id": m.get("id"),               # e.g., BTCUSDT
            "symbol": sym,                   # ccxt unified e.g., BTC/USDT:USDT
            "base": m.get("base"),
            "quote": m.get("quote"),
            "status": info.get("status"),
            "contractType": info.get("contractType"),
            "linear": m.get("linear"),
            "pricePrecision": price_prec,
            "amountPrecision": amt_prec,
            "minQty": min_amt,
            "minNotional": min_cost,
            "tickSize": tick_size,
            "stepSize": step_size,
        })
    rows.sort(key=lambda r: (r["base"] or "", r["id"] or ""))
    return rows

def save_json(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2))

def save_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text(""); return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser(description="Fetch Binance USDT-M PERPETUAL (swap) contracts (TRADING).")
    ap.add_argument("--testnet", action="store_true", help="Use Binance Futures testnet")
    ap.add_argument("--outdir", default="data/perps", help="Output directory")
    ap.add_argument("--basename", default="binance_usdtm_perps", help="Output file base name")
    args = ap.parse_args()

    ex = build_exchange(testnet=args.testnet)
    rows = extract_perps(ex)

    outdir = Path(args.outdir)
    json_path = outdir / f"{args.basename}.json"
    csv_path  = outdir / f"{args.basename}.csv"
    save_json(rows, json_path)
    save_csv(rows, csv_path)

    print(f"Saved {len(rows)} USDT-M perps")
    print(f"JSON: {json_path.resolve()}")
    print(f"CSV : {csv_path.resolve()}")

if __name__ == "__main__":
    main()
