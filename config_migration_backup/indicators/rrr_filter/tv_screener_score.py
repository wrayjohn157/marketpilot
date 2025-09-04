from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging

import yaml

#!/usr/bin/env python3
from
 pathlib import Path

# === Load path config ===
CONFIG_FILE = Path(__file__).resolve().parents[2] / "config" / "paths_config.yaml"
with open(CONFIG_FILE) as f:
    paths = yaml.safe_load(f)

TV_CONFIG_PATH = Path(paths.get("tv_screener_config_path", "/home/signal/market7/config/tv_screener_config.yaml"))
RAW_FILE = Path(paths.get("tv_history_path", "/home/signal/market7/output/tv_history")) / "tv_screener_raw_dict.txt"

def get_tv_rating(symbol: str, screener_data: dict) -> tuple[float, bool]:
    symbol = symbol.upper()
    rating = screener_data.get(symbol, {}).get("15m", "").lower()

    if rating in ["buy", "strong_buy"]:
        return 0.5, True
    return 0.0, False

def load_config() -> dict:
    try:
        full = yaml.safe_load(TV_CONFIG_PATH.read_text())
        return full.get("tv_screener", {})
    except Exception as e:
        logging.warning(f"[TV] Could not load TV screener config: {e}")
        return {}

def tv_screener_score(symbol: str, timeframe: str = "15m") -> float:
    cfg = load_config()
    if not cfg.get("enabled", False):
        return 0.0

    weights = cfg.get("weights", {})
    strong_w = weights.get("strong_buy", 1.0)
    buy_w = weights.get("buy", 0.5)
    threshold = cfg.get("score_threshold", 0.6)

    if not RAW_FILE.exists():
        logging.warning("[TV] Screener file missing, skipping TV score")
        return 0.0

    try:
        data = json.loads(RAW_FILE.read_text())
    except Exception as e:
        logging.warning(f"[TV] Failed to parse raw screener file: {e}")
        return 0.0

    entry = data.get(symbol.upper(), {})
    rating = entry.get(timeframe, "").lower()

    if "strong" in rating:
        return strong_w
    if "buy" in rating:
        return buy_w
    return 0.0
