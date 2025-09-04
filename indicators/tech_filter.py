import json
import logging
import sys
from datetime import datetime

#!/usr/bin/env python3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config.config_loader import PATHS  # ✅ Use the loader
from config.unified_config_manager import (
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
)

# ✅ Inject base path so config/ can be imported when run via systemd
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
sys.path.append(str(PROJECT_ROOT))

# === Setup ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
from config.unified_config_manager import get_config
from utils.redis_manager import get_redis_manager

r = get_redis_manager()

# === Load paths dynamically ===
OUTPUT_FILE = get_path("final_fork_rrr_trades")
FORK_FILE = get_path("fork_candidates")
VOLUME_PASSED_SET = "queues:volume_passed_tokens"

# Load BTC condition
try:
    market_condition = r.get_cache("cache:btc_condition") or "neutral"
    logging.info(f"📈 BTC Market Condition: {market_condition}")
except Exception as e:
    market_condition = "neutral"
    logging.warning(f"⚠️ Failed to fetch btc_condition from Redis, using default: {e}")

# === Thresholds ===
thresholds = {
    "neutral": {
        "15m": {
            "qqe_min": 20,
            "qqe_max": 50,
            "rsi_range": [35, 65],
            "stoch_max": 0.8,
            "stoch_oversold": 0.3,
        },
        "1h": {
            "qqe_min": 30,
            "qqe_max": 50,
            "stoch_confirmation": 0.25,
            "stoch_oversold": 0.25,
        },
        "4h": {
            "qqe_min": 30,
            "qqe_max": 50,
            "stoch_confirmation": 0.3,
            "stoch_oversold": 0.2,
        },
    },
    "bullish": {
        "15m": {"adx_min": 20, "rsi_max": 75, "use_psar": True},
        "1h": {"qqe_min": 55, "qqe_max": 80, "use_psar": True},
        "4h": {"qqe_min": 55, "qqe_max": 80, "use_psar": True},
    },
    "bearish": {
        "15m": {"rsi_max": 45, "use_psar": True},
        "1h": {"qqe_max": 50, "use_psar": True},
        "4h": {"qqe_max": 50, "use_psar": True},
    },
}

# === Functions (your originals) ===


def evaluate(symbol: Any, tf: Any, ind: Any) -> Any:
    t = thresholds.get(market_condition, thresholds["neutral"]).get(tf, {})
    passed = True
    reasons = []

    macd = ind.get("MACD")
    signal = ind.get("MACD_signal")
    hist = ind.get("MACD_Histogram")
    hist_prev = ind.get("MACD_Histogram_Prev")

    if macd is not None and signal is not None and macd < signal:
        reasons.append(f"{tf} MACD below Signal ({macd:.6f} < {signal:.6f})")
        passed = False

    if hist is not None and hist_prev is not None:
        if market_condition == "bullish":
            if hist < hist_prev:
                reasons.append(
                    f"{tf} MACD Histogram not rising ({hist:.4f} < {hist_prev:.4f})"
                )
                passed = False
        else:
            if hist < hist_prev and hist < 0:
                reasons.append(
                    f"{tf} MACD Histogram declining ({hist:.4f} < {hist_prev:.4f})"
                )
                passed = False

    if tf == "15m":
        if market_condition == "neutral":
            if not (t["qqe_min"] <= ind["QQE"] <= t["qqe_max"]):
                reasons.append(f"QQE {ind['QQE']} not in {t['qqe_min']}–{t['qqe_max']}")
                passed = False
            if not (t["rsi_range"][0] <= ind["RSI14"] <= t["rsi_range"][1]):
                reasons.append(f"RSI {ind['RSI14']} not in {t['rsi_range']}")
                passed = False
            if ind["StochRSI_K"] > t["stoch_max"]:
                reasons.append(f"Stoch_K {ind['StochRSI_K']} > {t['stoch_max']}")
                passed = False
            if ind["StochRSI_K"] > t["stoch_oversold"]:
                reasons.append(
                    f"Stoch_K {ind['StochRSI_K']} > oversold {t['stoch_oversold']}"
                )
                passed = False
        elif market_condition == "bullish":
            if ind.get("ADX14", 0) < t.get("adx_min", 20):
                reasons.append(f"ADX {ind.get('ADX14', 0)} < {t.get('adx_min', 20)}")
                passed = False
            if ind.get("RSI14", 0) > t.get("rsi_max", 75):
                reasons.append(f"RSI {ind.get('RSI14', 0)} > {t.get('rsi_max', 75)}")
                passed = False
        elif market_condition == "bearish":
            if ind.get("RSI14", 0) > t.get("rsi_max", 45):
                reasons.append(f"RSI {ind.get('RSI14', 0)} > {t.get('rsi_max', 45)}")
                passed = False
            if t.get("use_psar", False) and ind.get("PSAR", 0) <= ind.get(
                "latest_close", 0
            ):
                reasons.append(
                    f"PSAR {ind.get('PSAR', 0)} not above close {ind.get('latest_close', 0)}"
                )
                passed = False

    elif tf in ["1h", "4h"]:
        if market_condition == "neutral":
            if ind["QQE"] < t["qqe_min"]:
                reasons.append(f"QQE {ind['QQE']} < {t['qqe_min']}")
                passed = False
            if ind["StochRSI_K"] < t["stoch_confirmation"]:
                reasons.append(
                    f"Stoch_K {ind['StochRSI_K']} < confirm {t['stoch_confirmation']}"
                )
                passed = False
            if ind["StochRSI_K"] > t["stoch_oversold"]:
                reasons.append(
                    f"Stoch_K {ind['StochRSI_K']} > oversold {t['stoch_oversold']}"
                )
                passed = False
        elif market_condition == "bullish":
            if not (t.get("qqe_min", 55) <= ind.get("QQE", 0) <= t.get("qqe_max", 80)):
                reasons.append(
                    f"QQE {ind.get('QQE', 0)} not in {t.get('qqe_min', 55)}–{t.get('qqe_max', 80)}"
                )
                passed = False
        elif market_condition == "bearish":
            if ind.get("QQE", 0) > t.get("qqe_max", 50):
                reasons.append(f"QQE {ind.get('QQE', 0)} > {t.get('qqe_max', 50)}")
                passed = False
            if t.get("use_psar", False) and ind.get("PSAR", 0) <= ind.get(
                "latest_close", 0
            ):
                reasons.append(
                    f"PSAR {ind.get('PSAR', 0)} not above close {ind.get('latest_close', 0)}"
                )
                passed = False

    return passed, reasons


def check_fork_criteria(ind: Any) -> Any:
    score = 0
    reasons = []

    macd = ind.get("MACD")
    signal = ind.get("MACD_signal")
    hist = ind.get("MACD_Histogram")
    hist_prev = ind.get("MACD_Histogram_Prev")
    stoch_k = ind.get("StochRSI_K", 0)
    rsi = ind.get("RSI14", 0)

    if macd is not None and signal is not None and abs(macd - signal) < 0.0005:
        score += 1
        reasons.append("MACD near signal")

    if hist is not None and hist_prev is not None and hist > hist_prev:
        score += 1
        reasons.append("MACD Histogram rising")

    if 30 <= rsi <= 45:
        score += 1
        reasons.append(f"RSI recovery ({rsi:.2f})")

    if stoch_k < 0.25:
        score += 1
        reasons.append(f"Stoch_K oversold ({stoch_k:.2f})")

    return score >= 2, reasons


# === main() ===
def main() -> Any:
    approved = {}
    fork_queue = {}
    symbols = r.get_trade_data()
    logging.info(f"📊 Evaluating {len(symbols)} symbols...")

    for symbol in symbols:
        symbol_clean = (
            symbol.replace("USDT_", "").replace("_USDT", "").replace("USDT", "")
        )
        logging.info(f"🔎 {symbol_clean}")

        tf_passed = []
        tf_debug = []
        fork_reasons = {}

        for tf in ["15m", "1h", "4h"]:
            redis_key = f"{symbol_clean}_{tf}"
            raw = r.get_cache(redis_key)
            if not raw:
                continue
            ind = json.loads(raw)

            passed, reasons = evaluate(symbol_clean, tf, ind)
            if passed:
                tf_passed.append(tf)
            else:
                tf_debug.append((tf, reasons))

                is_fork, flags = check_fork_criteria(ind)
                if is_fork:
                    fork_reasons[tf] = flags

        if len(tf_passed) == 2:
            approved[symbol_clean] = {
                "timeframes": tf_passed,
                "indicator_data": {
                    "1h": json.loads(r.get_cache(f"{symbol_clean}_1h") or "{}")
                },
            }
            logging.info(f"✅ PASSED: {symbol_clean}")
        elif fork_reasons:
            fork_queue[symbol_clean] = {
                "timeframes_failed": [x[0] for x in tf_debug],
                "reasons": fork_reasons,
                "indicator_data": {
                    "1h": json.loads(r.get_cache(f"{symbol_clean}_1h") or "{}")
                },
            }
            logging.info(f"🌀 FORKED: {symbol_clean}")
            for tf, flags in fork_reasons.items():
                for reason in flags:
                    logging.info(f"    {tf}: {reason}")
        else:
            logging.info(f"❌ FAILED: {symbol_clean}")
            for tf, reasons in tf_debug:
                for reason in reasons:
                    logging.info(f"    {tf.upper()}: {reason}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(approved, f, indent=2)

    with open(FORK_FILE, "w") as f:
        json.dump(fork_queue, f, indent=2)

    r.set_cache("counters:tech_filter_count_in", len(symbols))
    r.set_cache("counters:tech_filter_count_out", len(approved))
    r.set_cache("last_scan_tech", datetime.utcnow().isoformat())

    logging.info(
        f"💾 Saved {len(approved)} approved | 🌀 Saved {len(fork_queue)} fork candidates"
    )


if __name__ == "__main__":
    main()

sys.exit(0)
