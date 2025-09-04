from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging

from ta.momentum import StochRSIIndicator, RSIIndicator
from ta.trend import EMAIndicator, ADXIndicator, MACD, PSARIndicator
from ta.volatility import AverageTrueRange
import pandas as pd
import requests

    import argparse
import time
from utils.redis_manager import get_redis_manager, RedisKeyManager


#!/usr/bin/env python3
"""
rolling_indicators_with_lev.py
- Pulls klines from SPOT and/or FUTURES (USDT-M) depending on KLINE_SOURCE env or auto-detect.
- Computes indicators and saves snapshots to disk + Redis keys for quick reads.

Run examples:
  INDICATOR_KLINE_SOURCE=auto python3 rolling_indicators_with_lev.py
  INDICATOR_KLINE_SOURCE=futures python3 rolling_indicators_with_lev.py --once
  python3 rolling_indicators_with_lev.py --interval 120
"""
import
 os

# ------------------ Config ------------------
REFRESH_INTERVAL_DEFAULT = 60
KLINE_LIMIT = 210
TIMEFRAMES = ["15m", "1h", "4h"]
# where to pull klines from: "spot" | "futures" | "auto"
KLINE_SOURCE = os.getenv("INDICATOR_KLINE_SOURCE", "auto").lower()

PATHS = {
    "filtered_pairs": Path("/home/signal/market7/data/filtered_pairs.json"),
    "snapshots": Path("/home/signal/market7/data/snapshots"),
}

FILTERED_FILE = PATHS["filtered_pairs"]
SNAPSHOTS_BASE = PATHS["snapshots"]
FORK_METRICS_FILE = Path("/home/signal/market7/dashboard_backend/cache/fork_metrics.json")
# filtered perps (contract IDs like BTCUSDT)
PERP_FILTERED_IDS = Path("/home/signal/market7/lev/data/perps/filtered_perps.json")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("rolling_inds")

# ------------------ Helpers ------------------

def _read_json(path: Path, default):
    try:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        log.warning(f"⚠️ Failed reading {path}: {e}")
    return default

def _perp_bases_and_map() -> Any:
    """Return (set_of_bases, preferred_id_map) from filtered perps JSON.
    preferred_id_map chooses USDT contract if both USDT and USDC exist.
    """
    ids = _read_json(PERP_FILTERED_IDS, [])
    bases = set()
    by_base = {}
    for sym_id in ids:
        base = sym_id.removesuffix("USDT").removesuffix("USDC")
        bases.add(base)
        current = by_base.get(base)
        if (current is None) or (current.endswith("USDC") and sym_id.endswith("USDT")):
            by_base[base] = sym_id
    return bases, by_base

def pick_symbol_and_source(base: str):
    """Decide which market to pull klines from, and return (full_symbol, market)
    where market is one of {"spot","futures"}.
    """
    base_u = base.upper()
    perp_bases, perp_map = _perp_bases_and_map()

    if KLINE_SOURCE == "spot":
        return base_u + "USDT", "spot"
    if KLINE_SOURCE == "futures":
        return perp_map.get(base_u, base_u + "USDT"), "futures"

    # auto mode: prefer futures if base exists in perps, else spot
    if base_u in perp_bases:
        return perp_map.get(base_u, base_u + "USDT"), "futures"
    return base_u + "USDT", "spot"

def fetch_klines_spot(symbol: Any, interval: Any, limit: Any = 150) -> Any:
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        df = pd.DataFrame(
            resp.json(),
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "qav",
                "num_trades",
                "tb_base_vol",
                "tbqav",
                "ignore",
            ],
        )
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        return df
    except Exception as e:
        log.warning(f"Failed to fetch SPOT klines for {symbol} {interval}: {e}")
        return None

def fetch_klines_futures(symbol: Any, interval: Any, limit: Any = 150) -> Any:
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        df = pd.DataFrame(
            resp.json(),
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "qav",
                "num_trades",
                "tb_base_vol",
                "tbqav",
                "ignore",
            ],
        )
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        return df
    except Exception as e:
        log.warning(f"Failed to fetch FUTURES klines for {symbol} {interval}: {e}")
        return None

def fetch_klines_any(symbol: Any, market: Any, interval: Any, limit: Any = 150) -> Any:
    if market == "futures":
        return fetch_klines_futures(symbol, interval, limit)
    return fetch_klines_spot(symbol, interval, limit)

def compute_indicators(df: pd.DataFrame) -> dict:
    indicators = {}
    indicators["EMA50"] = EMAIndicator(df["close"], 50).ema_indicator().iloc[-1]
    indicators["EMA200"] = EMAIndicator(df["close"], 200).ema_indicator().iloc[-1]
    indicators["RSI14"] = RSIIndicator(df["close"]).rsi().iloc[-1]
    indicators["ADX14"] = ADXIndicator(df["high"], df["low"], df["close"]).adx().iloc[-1]

    rsi_series = RSIIndicator(df["close"]).rsi()
    smoothed_rsi = rsi_series.ewm(alpha=1 / 14, adjust=False).mean()
    atr_rsi = (rsi_series - smoothed_rsi).abs().ewm(alpha=1 / 14, adjust=False).mean()
    indicators["QQE"] = smoothed_rsi.iloc[-1] + 4.236 * atr_rsi.iloc[-1]

    indicators["PSAR"] = PSARIndicator(df["high"], df["low"], df["close"]).psar().iloc[-1]
    indicators["ATR"] = AverageTrueRange(df["high"], df["low"], df["close"]).average_true_range().iloc[-1]

    stoch_rsi = StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
    indicators["StochRSI_K"] = stoch_rsi.stochrsi_k().iloc[-1]
    indicators["StochRSI_D"] = stoch_rsi.stochrsi_d().iloc[-1]

    macd = MACD(df["close"])  # default fast=12, slow=26, signal=9
    indicators["MACD"] = macd.macd().iloc[-1]
    indicators["MACD_signal"] = macd.macd_signal().iloc[-1]
    indicators["MACD_diff"] = macd.macd_diff().iloc[-1]
    indicators["MACD_Histogram"] = macd.macd_diff().iloc[-1]
    indicators["MACD_Histogram_Prev"] = macd.macd_diff().iloc[-2]
    indicators["MACD_lift"] = macd.macd().iloc[-1] - macd.macd().iloc[-2]

    indicators["latest_close"] = df["close"].iloc[-1]
    indicators["timestamp"] = int(time.time())
    return indicators

# ---------- symbol loading ----------

def load_symbols() -> Any:
    filtered = set()
    active = set()

    if FILTERED_FILE.exists():
        try:
            with open(FILTERED_FILE, "r") as f:
                filtered = set(json.load(f))  # spot bases
        except Exception as e:
            log.warning(f"⚠️ Failed reading filtered spot list: {e}")

    if FORK_METRICS_FILE.exists():
        try:
            with open(FORK_METRICS_FILE, "r") as f:
                fork_metrics = json.load(f)
                active = set([
                    d["pair"].replace("USDT_", "")
                    for d in fork_metrics.get("metrics", {}).get("active_deals", [])
                ])
        except Exception as e:
            log.warning(f"⚠️ Failed to load active forks from fork_metrics.json: {e}")

    if KLINE_SOURCE in ("futures", "auto"):
        perp_bases, _ = _perp_bases_and_map()
        filtered = filtered.union(perp_bases)

    symbols = sorted(filtered.union(active))
    if not symbols:
        log.warning("⚠️ No symbols found from filtered spot/perp lists or fork metrics.")
    return symbols

# ---------- snapshot I/O ----------

def get_snapshot_dir() -> Path:
    path = SNAPSHOTS_BASE / datetime.utcnow().strftime("%Y-%m-%d")
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_to_disk(base: str, tf: str, indicators: dict):
    snapshot_dir = get_snapshot_dir()
    filename = snapshot_dir / f"{base.upper()}_{tf}.json"
    try:
        with open(filename, "w") as f:
            json.dump(indicators, f, indent=2)
        log.info(f"📂 {base.upper()}_{tf} indicators saved to disk")
    except Exception as e:
        log.error(f"❌ Failed to save {base.upper()}_{tf} to disk: {e}")

    jsonl_filename = snapshot_dir / f"{base.upper()}_{tf}.jsonl"
    try:
        with open(jsonl_filename, "a") as f_jsonl:
            f_jsonl.write(json.dumps(indicators) + "\n")
        log.debug(f"📄 Appended to {base.upper()}_{tf}.jsonl")
    except Exception as e:
        log.warning(f"⚠️ Failed to append to JSONL for {base.upper()}_{tf}: {e}")

# ------------------ Main loop ------------------

def run_once() -> Any:
    symbols = load_symbols()
    for base in symbols:
        full_symbol, market = pick_symbol_and_source(base)
        for tf in TIMEFRAMES:
            df = fetch_klines_any(full_symbol, market, tf, limit=KLINE_LIMIT)
            if df is None or len(df) < 100:
                continue
            indicators = compute_indicators(df)
            key = f"{base.upper()}_{tf}"
            r.store_indicators(key, indicators)
            try:
                r.set_cache(f"{base.upper()}_{tf}_RSI14", indicators["RSI14"])
                r.set_cache(f"{base.upper()}_{tf}_StochRSI_K", indicators["StochRSI_K"])
                r.set_cache(f"{base.upper()}_{tf}_StochRSI_D", indicators["StochRSI_D"])
            except Exception as e:
                log.warning(f"⚠️ Failed to write individual indicators for {base}: {e}")
            save_to_disk(base, tf, indicators)
            log.info(f"✅ {key} ({market}) indicators written")

def main() -> Any:

    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="Run a single pass and exit")
    ap.add_argument("--interval", type=int, default=int(os.getenv("INDICATOR_INTERVAL", REFRESH_INTERVAL_DEFAULT)), help="Refresh seconds for loop mode")
    args = ap.parse_args()

    log.info(f"📊 Starting indicator updater... (kline_source={KLINE_SOURCE})")
    if args.once:
        run_once()
        return

    while True:
        run_once()
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
