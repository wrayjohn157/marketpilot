#!/usr/bin/env python3
import json
import logging
from pathlib import Path
from datetime import datetime
import yaml
import sys
import argparse

# === Paths ===
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dca.utils.entry_utils import (
    get_live_3c_trades, get_latest_indicators, send_dca_signal,
    load_fork_entry_score, simulate_new_avg_price, get_rsi_slope,
    get_macd_lift, save_entry_score_to_redis, load_entry_score_from_redis
)
from dca.utils.fork_score_utils import compute_fork_score
from dca.modules.fork_safu_evaluator import get_safu_score
from dca.utils.btc_filter import get_btc_status
from dca.modules.dca_decision_engine import should_dca
from dca.utils.recovery_odds_utils import get_latest_snapshot, predict_recovery_odds
from dca.utils.recovery_confidence_utils import predict_confidence_score
from dca.utils.tv_utils import load_tv_kicker
from dca.utils.zombie_utils import is_zombie_trade
from dca.utils.spend_predictor import predict_spend_volume, adjust_volume
from live.strat.strategy_loader import load_strategy_config

CONFIG_PATH = Path("/home/signal/market6/dca/config/dca_config.yaml")
LOG_DIR = Path("/home/signal/market6/dca/logs")
SNAPSHOT_DIR = Path("/home/signal/market6/live/ml_dataset/recovery_snapshots")
DCA_TRACKING_PATH = LOG_DIR / "dca_tracking" / "dca_fired.jsonl"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
DCA_TRACKING_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_last_snapshot_values(symbol, deal_id):
    snap_path = SNAPSHOT_DIR / f"{symbol}_{deal_id}.jsonl"
    if not snap_path.exists():
        return 0.0, 0.0
    try:
        with open(snap_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return 0.0, 0.0
            last = json.loads(lines[-1])
            return last.get("confidence_score", 0.0), last.get("tp1_shift", 0.0)
    except:
        return 0.0, 0.0

def run(strategy_name):
    strategy = load_strategy_config(name=strategy_name)
    config.update(strategy)

    logging.info("📊 Evaluating active 3Commas trades")
    btc_status = get_btc_status(config.get("btc_indicators", {}))
    logging.info(f"🧠 BTC Market Status: {'✅ SAFE' if btc_status == 'SAFE' else '⚠️ UNSAFE'}")
    trades = get_live_3c_trades()
    logging.info(f"🧬 Strategy loaded: {strategy_name}")

    for trade in trades:
        symbol = trade["pair"]
        short_symbol = symbol.replace("USDT_", "")
        deal_id = trade.get("id")
        total_spent = float(trade.get("bought_volume") or 0)
        avg_entry_price = float(trade.get("bought_average_price") or 0)
        current_price = float(trade.get("current_price") or 0)

        created_at = trade.get("created_at")
        try:
            entry_ts = int(datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000)
        except:
            entry_ts = None

        deviation_pct = ((avg_entry_price - current_price) / avg_entry_price) * 100 if avg_entry_price else 0
        if deviation_pct < 0:
            logging.info(f"💰 {symbol} in profit ({deviation_pct:.2f}%), skipping.")
            continue

        indicators = get_latest_indicators(short_symbol)
        safu_score = get_safu_score(short_symbol, avg_entry_price, current_price)
        current_score = compute_fork_score(short_symbol)
        entry_score = load_entry_score_from_redis(deal_id) or load_fork_entry_score(short_symbol, entry_ts)

        new_avg = simulate_new_avg_price(avg_entry_price, 20, current_price)
        tp1_shift = ((1.015 * new_avg - current_price) / current_price) * 100
        be_improvement = ((avg_entry_price - new_avg) / avg_entry_price) * 100

        macd_lift = get_macd_lift(short_symbol)
        rsi_slope = get_rsi_slope(short_symbol)
        indicators.update({
            "macd_lift": macd_lift,
            "rsi_slope": rsi_slope,
            "drawdown_pct": deviation_pct
        })

        snapshot = get_latest_snapshot(symbol, deal_id)
        recovery_odds = predict_recovery_odds(snapshot)
        confidence_score = predict_confidence_score(snapshot)
        zombie = is_zombie_trade(indicators, recovery_odds, current_score)
        if zombie:
            logging.info(f"💀 {symbol} skipped due to zombie tag")
            continue

        tv_tag, tv_kicker = load_tv_kicker(short_symbol)
        should_fire, reason, _ = should_dca(
            trade=trade, config=config, indicators=indicators,
            btc_status=btc_status, entry_score=entry_score,
            current_score=current_score, safu_score=safu_score,
            tp1_sim_pct=tp1_shift
        )

        # Confidence override with safeguards
        override = config.get("confidence_dca_guard", {})
        last_conf, last_tp1 = get_last_snapshot_values(short_symbol, deal_id)
        conf_delta = confidence_score - last_conf
        tp1_delta = tp1_shift - last_tp1

        if (
            config.get("use_confidence_override", True)
            and not should_fire
            and confidence_score >= override.get("confidence_score_min", 0.7)
            and conf_delta >= override.get("min_confidence_delta", 0.05)
            and tp1_delta >= override.get("min_tp1_shift_gain_pct", 0.25)
            and deviation_pct >= config.get("drawdown_trigger_pct", 0.9)
            and safu_score >= override.get("safu_score_min", 0.5)
            and macd_lift >= override.get("macd_lift_min", 0.00005)
            and rsi_slope >= override.get("rsi_slope_min", 1.0)
        ):
            logging.info(f"🚀 Confidence override triggered for {symbol}")
            should_fire = True
            reason = "confidence_override"

        logging.info(f"🧪 {symbol} | TP1 shift: {tp1_shift:.2f} | Confidence Δ: {conf_delta:.2f} | TP1 Δ: {tp1_delta:.2f}")

        # Final output log
        logging.info(json.dumps({
            "symbol": symbol,
            "entry_score": entry_score,
            "current_score": current_score,
            "confidence_score": confidence_score,
            "tp1_shift": tp1_shift,
            "should_fire": should_fire,
            "reason": reason
        }, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart DCA Signal Runner")
    parser.add_argument("--strategy", type=str, default="confidence_safeguard", help="Strategy YAML file (no .yaml)")
    args = parser.parse_args()
    run(args.strategy)
