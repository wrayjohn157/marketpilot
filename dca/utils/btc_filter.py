#!/usr/bin/env python3

import json
import logging
from datetime import datetime
from pathlib import Path

# === Dynamic Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /market7
BTC_SNAPSHOT_BASE = BASE_DIR / "live" / "btc_logs"

# === BTC Snapshot Loader ===
def get_latest_btc_snapshot():
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
def is_btc_unsafe(cfg):
    snapshot = get_latest_btc_snapshot()
    if not snapshot:
        logging.warning("[BTC] No snapshot available, skipping BTC filter")
        return False

    rsi = snapshot.get("RSI14")
    macd = snapshot.get("MACD_Histogram")
    adx = snapshot.get("ADX14")

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

def get_btc_status(cfg):
    """
    Returns a readable BTC market status string: 'SAFE' or 'UNSAFE'
    """
    return "UNSAFE" if is_btc_unsafe(cfg) else "SAFE"
