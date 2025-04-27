#!/usr/bin/env python3
import json
import logging
from pathlib import Path
from datetime import datetime
import time

# === Config ===
INPUT_FILE = Path("/home/signal/market6/output/fork_backtest_candidates.json")
TV_FILE = Path("/home/signal/market6/output/tv_screener_raw_dict.txt")
FORK_TV_OUTPUT = Path("/home/signal/market6/output/fork_tv_adjusted.jsonl")
TV_HISTORY_BASE = Path("/home/signal/market6/output/tv_history")

TV_SCORE_WEIGHTS = {
    "strong_buy": 0.30,
    "buy": 0.20,
    "neutral": 0.00,
    "sell": -0.20,
    "strong_sell": -0.30
}

MIN_PASS_SCORE = 0.73

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def load_candidates(path: Path):
    with open(path) as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == "[":
            try:
                data = json.load(f)
                return data
            except Exception as e:
                logging.error(f"[ERROR] Failed to parse JSON array: {e}")
                return []
        else:
            entries = []
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except Exception as e:
                    logging.warning("⚠️ Skipping bad line: %s", e)
            return entries

def load_tv_tags(path: Path):
    if not path.exists():
        logging.warning("⚠️ TV file not found: %s", path)
        return {}
    with open(path) as f:
        try:
            tv_data = json.load(f)
            return {k.upper(): v.get("15m", "neutral") for k, v in tv_data.items()}
        except Exception as e:
            logging.error("[TV] Failed to parse: %s", e)
            return {}

def main():
    logging.info("📡 Loading TV tags and fork candidates…")
    candidates = load_candidates(INPUT_FILE)
    tv_tags = load_tv_tags(TV_FILE)

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
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
            ts = int(time.time() * 1000)
            passed = adjusted_score >= MIN_PASS_SCORE

            entry = {
                "symbol": symbol,
                "prev_score": base_score,
                "tv_tag": tv_tag,
                "tv_kicker": tv_kicker,
                "adjusted_score": adjusted_score,
                "timestamp": ts,
                "pass": passed
            }

            if passed:
                f_out.write(json.dumps(entry) + "\n")
                count_passed += 1

            f_log.write(json.dumps(entry) + "\n")

            # CLI feedback
            if passed:
                icon = "✅"
            elif adjusted_score > base_score:
                icon = "🟢"
            elif adjusted_score < base_score:
                icon = "🔻"
            else:
                icon = "➖"

            logging.info("%s %s | %.4f → %.4f | TV: %s", icon, symbol, base_score, adjusted_score, tv_tag)

    logging.info("🟩 Saved %d trades to %s", count_passed, FORK_TV_OUTPUT)
    logging.info("📚 Persistent log: %s", history_file)

if __name__ == "__main__":
    main()
