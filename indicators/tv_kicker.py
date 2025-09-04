from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
import sys

import yaml

from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


#!/usr/bin/env python3
 Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# === Setup Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Paths ===
INPUT_FILE = get_path("fork_backtest_candidates")
FORK_TV_OUTPUT = get_path("fork_tv_adjusted")
TV_HISTORY_BASE = get_path("tv_history")

today_str = datetime.utcnow().strftime("%Y-%m-%d")
TV_FILE = TV_HISTORY_BASE / today_str / "tv_screener_raw_dict.txt"
CONFIG_PATH = get_path("tv_screener_config")

# === Load Config ===
try:
    config = yaml.safe_load(CONFIG_PATH.read_text())["tv_screener"]
    TV_SCORE_WEIGHTS = config["weights"]
    MIN_PASS_SCORE = config["score_threshold"]
except Exception as e:
    logging.warning(f"[TV_KICKER] Failed to load config, using defaults: {e}")
    TV_SCORE_WEIGHTS = {
        "strong_buy": 0.30,
        "buy": 0.20,
        "neutral": 0.00,
        "sell": -0.20,
        "strong_sell": -0.30
    }
    MIN_PASS_SCORE = 0.73

# === Loaders ===
def load_candidates(path: Path):
    if not path.exists():
        logging.error(f"[ERROR] Missing input file: {path}")
        return []
    with open(path) as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == "[":
            try:
                return json.load(f)
            except Exception as e:
                logging.error(f"[ERROR] Failed to parse JSON array: {e}")
                return []
        else:
            entries = []
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except Exception as e:
                    logging.warning(f"⚠️ Skipping bad line: {e}")
            return entries

def load_tv_tags(path: Path):
    if not path.exists():
        logging.warning(f"⚠️ TV screener file not found: {path}")
        return {}
    try:
        with open(path) as f:
            tv_data = json.load(f)
            return {k.upper(): v.get("15m", "neutral") for k, v in tv_data.items()}
    except Exception as e:
        logging.error(f"[TV] Failed to parse TV file: {e}")
        return {}

# === Main Logic ===
def main() -> Any:
    logging.info("📡 Loading TV tags and fork candidates...")
    candidates = load_candidates(INPUT_FILE)
    tv_tags = load_tv_tags(TV_FILE)

    history_dir = TV_HISTORY_BASE / today_str
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / "tv_kicker.jsonl"

    count_passed = 0

    with open(FORK_TV_OUTPUT, "w") as f_out, open(history_file, "a") as f_log:
        for item in candidates:
            symbol = item.get("symbol", "").upper()
            base_score = item.get("score", 0)
            tv_tag = tv_tags.get(symbol, "neutral")
            tv_kicker = TV_SCORE_WEIGHTS.get(tv_tag, 0.0)
            adjusted_score = round(base_score + tv_kicker, 4)
            now = datetime.utcnow()
            ts = int(now.timestamp() * 1000)
            ts_iso = now.isoformat() + "Z"
            passed = adjusted_score >= MIN_PASS_SCORE

            entry = {
                "symbol": symbol,
                "prev_score": base_score,
                "tv_tag": tv_tag,
                "tv_kicker": tv_kicker,
                "adjusted_score": adjusted_score,
                "timestamp": ts,
                "ts_iso": ts_iso,
                "pass": passed
            }

            if passed:
                f_out.write(json.dumps(entry) + "\n")
                count_passed += 1

            f_log.write(json.dumps(entry) + "\n")

            icon = "✅" if passed else ("🟢" if adjusted_score > base_score else "🔻" if adjusted_score < base_score else "➖")
            logging.info(f"{icon} {symbol} | {base_score:.4f} → {adjusted_score:.4f} | TV: {tv_tag}")

    logging.info(f"🟩 Saved {count_passed} trades to {FORK_TV_OUTPUT}")
    logging.info(f"📚 Persistent log written to {history_file}")

if __name__ == "__main__":
    main()
