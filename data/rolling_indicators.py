import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import requests
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import MACD, ADXIndicator, EMAIndicator, PSARIndicator
from ta.volatility import AverageTrueRange

from config.unified_config_manager import (  # !/usr/bin/env python3
    config.unified_config_manager,
    from,
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
    get_redis_manager,
    import,
    utils.redis_manager,
)

# get_path("base") / data/rolling_indicators.py


# === Patch sys.path to reach /market7 ===
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = get_path("base")
sys.path.append(str(PROJECT_ROOT))

# === Import central paths ===

# === Logging ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Configuration ===
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REFRESH_INTERVAL = 60
KLINE_LIMIT = 210
TIMEFRAMES = ["15m", "1h", "4h"]

# === Paths ===
FILTERED_FILE = get_path("filtered_pairs")
SNAPSHOTS_BASE = get_path("snapshots")
FORK_METRICS_FILE = Path(
    get_path("base") / "dashboard_backend/cache/fork_metrics.json"
)

# === Redis ===
r = get_redis_manager()


def get_snapshot_dir() -> Any:
    path = SNAPSHOTS_BASE / datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_klines(symbol: Any, interval: Any, limit: Any = 150) -> Any:
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
        df = df.astype(
            {
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
            }
        )
        return df
    except Exception as e:
        logging.warning(f"Failed to fetch klines for {symbol} {interval}: {e}")
        return None


def compute_indicators(df: Any) -> Any:
    indicators = {}
    indicators["EMA50"] = EMAIndicator(df["close"], 50).ema_indicator().iloc[-1]
    indicators["EMA200"] = EMAIndicator(df["close"], 200).ema_indicator().iloc[-1]
    indicators["RSI14"] = RSIIndicator(df["close"]).rsi().iloc[-1]
    indicators["ADX14"] = (
        ADXIndicator(df["high"], df["low"], df["close"]).adx().iloc[-1]
    )

    rsi_series = RSIIndicator(df["close"]).rsi()
    smoothed_rsi = rsi_series.ewm(alpha=1 / 14, adjust=False).mean()
    atr_rsi = abs(rsi_series - smoothed_rsi).ewm(alpha=1 / 14, adjust=False).mean()
    indicators["QQE"] = smoothed_rsi.iloc[-1] + 4.236 * atr_rsi.iloc[-1]

    indicators["PSAR"] = (
        PSARIndicator(df["high"], df["low"], df["close"]).psar().iloc[-1]
    )
    indicators["ATR"] = (
        AverageTrueRange(df["high"], df["low"], df["close"])
        .average_true_range()
        .iloc[-1]
    )

    stoch_rsi = StochRSIIndicator(df["close"], window=14, smooth1=3, smooth2=3)
    indicators["StochRSI_K"] = stoch_rsi.stochrsi_k().iloc[-1]
    indicators["StochRSI_D"] = stoch_rsi.stochrsi_d().iloc[-1]

    macd = MACD(df["close"])
    indicators["MACD"] = macd.macd().iloc[-1]
    indicators["MACD_signal"] = macd.macd_signal().iloc[-1]
    indicators["MACD_diff"] = macd.macd_diff().iloc[-1]
    indicators["MACD_Histogram"] = macd.macd_diff().iloc[-1]
    indicators["MACD_Histogram_Prev"] = macd.macd_diff().iloc[-2]
    indicators["MACD_lift"] = macd.macd().iloc[-1] - macd.macd().iloc[-2]

    indicators["latest_close"] = df["close"].iloc[-1]
    indicators["timestamp"] = int(time.time())

    return indicators


def load_symbols() -> Any:
    filtered = set()
    active = set()

    if FILTERED_FILE.exists():
        with open(FILTERED_FILE, "r") as f:
            filtered = set(json.load(f))

    if FORK_METRICS_FILE.exists():
        try:
            with open(FORK_METRICS_FILE, "r") as f:
                fork_metrics = json.load(f)
                active = set(
                    [
                        d["pair"].replace("USDT_", "")
                        for d in fork_metrics.get("metrics", {}).get("active_deals", [])
                    ]
                )
        except Exception as e:
            logging.warning(
                f"⚠️ Failed to load active forks from fork_metrics.json: {e}"
            )

    symbols = sorted(filtered.union(active))

    if not symbols:
        logging.warning(
            "⚠️ No symbols found from filtered_pairs.json or fork_metrics.json."
        )

    return symbols


def save_to_disk(symbol: Any, tf: Any, indicators: Any) -> Any:
    snapshot_dir = get_snapshot_dir()
    filename = snapshot_dir / f"{symbol.upper()}_{tf}.json"
    try:
        with open(filename, "w") as f:
            json.dump(indicators, f, indent=2)
        logging.info(f"📂 {symbol.upper()}_{tf} indicators saved to disk")
    except Exception as e:
        logging.error(f"❌ Failed to save {symbol.upper()}_{tf} to disk: {e}")

    # Also append to JSONL version for rolling snapshot
    jsonl_filename = snapshot_dir / f"{symbol.upper()}_{tf}.jsonl"
    try:
        with open(jsonl_filename, "a") as f_jsonl:
            f_jsonl.write(json.dumps(indicators) + "\n")
        logging.info(f"📄 Appended to {symbol.upper()}_{tf}.jsonl")
    except Exception as e:
        logging.warning(f"⚠️ Failed to append to JSONL for {symbol.upper()}_{tf}: {e}")


def main() -> Any:
    logging.info("📊 Starting indicator updater...")
    while True:
        symbols = load_symbols()
        for symbol in symbols:
            full_symbol = symbol.upper() + "USDT"
            for tf in TIMEFRAMES:
                df = fetch_klines(full_symbol, tf, limit=KLINE_LIMIT)
                if df is None or len(df) < 100:
                    continue
                indicators = compute_indicators(df)
                key = RedisKeyManager.indicator(symbol, tf)
                r.store_indicators(key, indicators)

                try:
                    r.set_cache(
                        f"indicators:{symbol.upper()}:{tf}:RSI14", indicators["RSI14"]
                    )
                    r.set_cache(
                        f"indicators:{symbol.upper()}:{tf}:StochRSI_K",
                        indicators["StochRSI_K"],
                    )
                    r.set_cache(
                        f"indicators:{symbol.upper()}:{tf}:StochRSI_D",
                        indicators["StochRSI_D"],
                    )
                except Exception as e:
                    logging.warning(
                        f"⚠️ Failed to write individual indicators for {symbol}: {e}"
                    )

                save_to_disk(symbol, tf, indicators)
                logging.info(f"✅ {key} indicators written to Redis")
        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
