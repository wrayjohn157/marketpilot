import json
import logging
import os
from pathlib import Path
from datetime import datetime
import redis

# ===== CONFIG =====
INDICATOR_WEIGHTS = {
    "MACD_Histogram": 0.2,
    "RSI14": 0.2,
    "StochRSI_K": 0.15,
    "ADX14": 0.25,
    "EMA50": 0.2
}
MIN_SCORE = 0.65

FORK_INPUT_FILE = "/home/signal/market6/output/fork_candidates.json"
FINAL_OUTPUT_FILE = "/home/signal/market6/output/final_fork_rrr_trades.json"
BACKTEST_CANDIDATES_FILE = "/home/signal/market6/output/fork_backtest_candidates.json"
FORK_HISTORY_BASE = Path("/home/signal/market6/output/fork_history")
SNAPSHOT_BASE = Path("/home/signal/market6/data/snapshots")

REDIS_SET = "fork_score:approved"
REDIS_FINAL_TRADES = "fork_score:final"
r = redis.Redis()

# ===== FUNCTIONS =====
def score_from_indicators(indicators):
    score = 0
    total_weight = 0
    for key, weight in INDICATOR_WEIGHTS.items():
        val = indicators.get(key)
        if val is not None:
            score += float(val) * weight
            total_weight += weight
    return round(score / total_weight, 4) if total_weight > 0 else 0

def load_snapshot_indicators(symbol, date_str):
    filename = f"{symbol.upper()}_15m.json"
    path = SNAPSHOT_BASE / date_str / filename
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return None

def write_to_history_log(entry, date_str):
    out_dir = FORK_HISTORY_BASE / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "fork_scores.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ===== MAIN =====
def main():
    logging.basicConfig(level=logging.INFO)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    now_ts = int(datetime.utcnow().timestamp() * 1000)
    now_iso = datetime.utcnow().isoformat() + "Z"

    if not os.path.exists(FORK_INPUT_FILE):
        logging.error(f"Missing fork input file: {FORK_INPUT_FILE}")
        return

    with open(FORK_INPUT_FILE) as f:
        symbols = json.load(f)

    r.delete(REDIS_SET)
    r.delete(REDIS_FINAL_TRADES)

    results = []
    all_backtest_candidates = []

    for symbol in symbols:
        indicators = load_snapshot_indicators(symbol, today_str)
        if not indicators:
            logging.warning(f"⚠️ No indicator snapshot found for {symbol}")
            continue

        score = score_from_indicators(indicators)

        # Build score_hash
        hash_parts = []
        try:
            macd_hist = indicators.get("MACD_Histogram", 0)
            macd_prev = indicators.get("MACD_Histogram_Prev", 0)
            rsi = indicators.get("RSI14", 0)
            k = indicators.get("StochRSI_K", 0)
            d = indicators.get("StochRSI_D", 0)
            adx = indicators.get("ADX14", 0)
            price = indicators.get("latest_close", 0)
            ema50 = indicators.get("EMA50", 0)

            subscores = {
                "macd_histogram": 1.0 if macd_hist > macd_prev and macd_hist > 0 else 0.0,
                "rsi_recovery": 1.0 if rsi > 35 else 0.0,
                "stoch_rsi_cross": 1.0 if (k > d and k < 50) else 0.0,
                "adx_rising": min(adx / 20, 1.0) if adx > 10 else 0.0,
                "ema_price_reclaim": 1.0 if price > ema50 else 0.0
            }

            hash_parts = [f"{k}:{v}" for k, v in subscores.items()]
        except Exception:
            hash_parts = []

        score_hash = "_".join(hash_parts)

        passed = (
            score >= MIN_SCORE and
            (subscores.get("rsi_recovery") == 1.0 or subscores.get("stoch_rsi_cross") == 1.0)
        )

        # Log for backtesting
        trade_entry = {
            "symbol": symbol.upper(),
            "score": score,
            "timestamp": now_ts,
            "indicators": subscores
        }
        all_backtest_candidates.append(trade_entry)

        if passed:
            trade = {
                "symbol": symbol.upper(),
                "pair": f"{symbol.upper()}_USDT",
                "score": score,
                "meta": subscores,
                "score_hash": score_hash,
                "timestamp": now_ts
            }
            r.sadd(REDIS_SET, symbol)
            r.rpush(REDIS_FINAL_TRADES, json.dumps(trade))
            results.append(trade)
            logging.info(f"✅ {symbol.upper()} | Score: {score:.3f} | {subscores}")
        else:
            logging.info(f"❌ {symbol.upper()} | Score: {score:.3f} | {subscores}")

        # Always write to fork_history
        persistent_log = {
            "symbol": symbol.upper(),
            "timestamp": datetime.utcnow().isoformat(),
            "entry_price": indicators.get("latest_close"),
            "score": score,
            "score_hash": score_hash,
            "score_components": {k: indicators.get(k) for k in INDICATOR_WEIGHTS},
            "indicators": indicators,
            "passed": passed,
            "source": "fork_score_filter",
            "scored_at": now_iso
        }
        write_to_history_log(persistent_log, today_str)

    # Save output files
    with open(FINAL_OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    with open(BACKTEST_CANDIDATES_FILE, "w") as f:
        json.dump(all_backtest_candidates, f, indent=2)

    logging.info(f"💾 Saved {len(results)} trades to {FINAL_OUTPUT_FILE}")
    logging.info(f"📊 Backtest candidates saved to {BACKTEST_CANDIDATES_FILE}")

if __name__ == "__main__":
    main()
