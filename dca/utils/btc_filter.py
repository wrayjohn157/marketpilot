from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs
from config.unified_config_manager import get_config


#!/usr/bin/env python3

from
 pathlib import Path

# === Dynamic Paths ===
BASE_DIR = get_path("base")  # /home/signal/market7
BTC_SNAPSHOT_BASE = get_path("btc_logs") #BTC_SNAPSHOT_BASE = BASE_DIR / "dashboard_backend" / "snapshots" / "btc_"

# === BTC Snapshot Loader ===
def get_latest_btc_snapshot() -> Any:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filepath = BTC_SNAPSHOT_BASE / today / "btc_snapshots.jsonl"
    if not filepath.exists():
        logging.warning(f"[BTC] Snapshot file missing: {filepath}")
        return None

    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        if not lines:
            return None
        return json.loads(lines[-1])
    except Exception as e:
        logging.warning(f"[BTC] Failed to read snapshot: {e}")
        return None

# === BTC Safety Evaluator ===
def is_btc_unsafe(cfg: Any) -> Any:
    snapshot = get_latest_btc_snapshot()
    if not snapshot:
        logging.warning("[BTC] No snapshot available, skipping BTC filter")
        return False

    rsi = snapshot.get("rsi") #rsi = snapshot.get("RSI14")
    macd = snapshot.get("macd_histogram") #macd = snapshot.get("MACD_Histogram")
    adx = snapshot.get("adx") #adx = snapshot.get("ADX14")

    rsi_th = cfg.get("rsi", 35)
    macd_th = cfg.get("macd_histogram", -0.01)
    adx_th = cfg.get("adx", 20)

    if rsi is not None and rsi < rsi_th:
        return True
    if macd is not None and macd < macd_th:
        return True
    if adx is not None and adx < adx_th:
        return True
    return False

# === Status Returner ===
def get_btc_status(cfg: Any) -> Any:
    return "UNSAFE" if is_btc_unsafe(cfg) else "SAFE"
