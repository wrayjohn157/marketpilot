#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, logging, requests
from datetime import datetime
from pathlib import Path

# --- Paths resolved relative to this file ---
# this file lives at: <repo>/lev/tools/perp_volume_filter.py
CURRENT_FILE = Path(__file__).resolve()
LEV_DIR      = CURRENT_FILE.parents[1]          # <repo>/lev
REPO_ROOT    = LEV_DIR.parent                   # <repo>
PERPS_FILE   = REPO_ROOT / "lev" / "data" / "perps" / "binance_usdtm_perps.json"
OUT_FILE     = REPO_ROOT / "lev" / "data" / "perps" / "filtered_perps.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# Optional Redis (for “we have klines cached” gating)
try:
    import redis
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

def fetch_futures_24h() -> dict[str, float]:
    """
    Map of { 'BTCUSDT': 24h_quote_volume_float, ... } from Binance USDT-M futures.
    """
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    r = requests.get(url, timeout=12)
    r.raise_for_status()
    data = r.json()
    out: dict[str, float] = {}
    for row in data:
        sym = row.get("symbol")
        if not sym:
            continue
        try:
            qv = float(row.get("quoteVolume", 0.0))
        except Exception:
            qv = 0.0
        out[sym] = qv
    return out

def main():
    ap = argparse.ArgumentParser(description="Filter Binance USDT-M PERPETUALs by 24h quote volume (and optional Redis klines gate).")
    ap.add_argument("--min-volume", type=float, default=3_000_000, help="Minimum 24h quote volume in USDT (default: 3,000,000)")
    ap.add_argument("--no-redis", action="store_true", help="Disable Redis gating even if redis is installed")
    ap.add_argument("--redis-host", default="localhost")
    ap.add_argument("--redis-port", type=int, default=6379)
    ap.add_argument("--redis-db", type=int, default=0)
    ap.add_argument("--redis-key-fmt", default="{symbol}_15m_futures_klines",
                    help="Format for Redis key; {symbol} will be replaced with perp id (e.g., BTCUSDT)")
    args = ap.parse_args()

    if not PERPS_FILE.exists():
        logging.error(f"❌ Missing perps list: {PERPS_FILE}")
        raise SystemExit(1)

    perps = json.loads(PERPS_FILE.read_text())
    vol_map = fetch_futures_24h()

    use_redis = REDIS_AVAILABLE and (not args.no_redis)
    r = None
    if use_redis:
        try:
            r = redis.Redis(host=args.redis_host, port=args.redis_port, db=args.redis_db, decode_responses=True)
            # quick ping
            r.ping()
        except Exception as e:
            logging.warning(f"⚠️ Redis not available ({e}); continuing without Redis gate")
            use_redis = False

    qualified = []
    skipped = 0

    # Filter only USDT-quoted, TRADING, PERPETUAL, linear swaps
    candidates = [
        p for p in perps
        if p.get("quote") == "USDT"
        and p.get("status") == "TRADING"
        and p.get("contractType") == "PERPETUAL"
        and p.get("linear")
    ]

    for p in candidates:
        pid  = p.get("id")     # e.g., 'WIFUSDT'
        base = p.get("base")   # e.g., 'WIF'
        if not pid:
            continue

        qv = vol_map.get(pid)  # use exact id as key
        if not qv or qv < args.min_volume:
            logging.warning(f"⛔ Skipping {pid}: volume {qv} below threshold {args.min_volume}")
            skipped += 1
            continue

        if use_redis:
            key = args.redis_key_fmt.format(symbol=pid)
            if not r.exists(key):
                logging.info(f"⛔ Skipping {pid}: Redis key '{key}' not found.")
                skipped += 1
                continue

        qualified.append({
            "id": pid,
            "base": base,
            "quote": "USDT",
            "quoteVolume": qv,
            "minQty": p.get("minQty"),
            "stepSize": p.get("stepSize"),
            "tickSize": p.get("tickSize"),
        })

    qualified.sort(key=lambda row: (-row["quoteVolume"], row["id"]))
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps({
        "generated_at": datetime.utcnow().isoformat(),
        "min_quote_volume_usdt": args.min_volume,
        "count": len(qualified),
        "symbols": qualified,
    }, indent=2))

    logging.info(f"✅ Perps qualified: {len(qualified)} (skipped {skipped})")
    logging.info(f"💾 Saved to: {OUT_FILE.resolve()}")

if __name__ == "__main__":
    main()
