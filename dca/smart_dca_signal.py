#!/usr/bin/env python3
import json
import logging
from pathlib import Path
from datetime import datetime
import yaml
import sys

# === Paths ===
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dca.utils.entry_utils import (
    get_live_3c_trades,
    get_latest_indicators,
    send_dca_signal,
    load_fork_entry_score,
    simulate_new_avg_price,
    get_rsi_slope,
    get_macd_lift,
    save_entry_score_to_redis,
    load_entry_score_from_redis,
)


from dca.utils.fork_score_utils import compute_fork_score
from dca.modules.fork_safu_evaluator import get_safu_score
from dca.utils.btc_filter import get_btc_status
from dca.modules.dca_decision_engine import should_dca
from dca.utils.recovery_odds_utils import (
    get_latest_snapshot,
    predict_recovery_odds,
    SNAPSHOT_PATH,
)
from dca.utils.recovery_confidence_utils import predict_confidence_score
from dca.utils.tv_utils import load_tv_kicker
from dca.utils.zombie_utils import is_zombie_trade
from dca.utils.spend_predictor import predict_spend_volume, adjust_volume
from dca.utils.trade_health_evaluator import evaluate_trade_health
from config.config_loader import PATHS

CONFIG_PATH = PATHS["base"] / "dca" / "config" / "dca_config.yaml"
LOG_DIR = PATHS["base"] / "dca" / "logs"
SNAPSHOT_DIR = SNAPSHOT_PATH
DCA_TRACKING_PATH = LOG_DIR / "dca_tracking" / "dca_fired.jsonl"

SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
DCA_TRACKING_PATH.parent.mkdir(parents=True, exist_ok=True)


with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


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


def get_last_fired_step(deal_id):
    if not DCA_TRACKING_PATH.exists():
        return 0
    last = 0
    with open(DCA_TRACKING_PATH, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj["deal_id"] == deal_id and obj.get("step", 0) > last:
                    last = obj["step"]
            except:
                continue
    return last


def was_dca_fired_recently(deal_id, step):
    if not DCA_TRACKING_PATH.exists():
        return False
    with open(DCA_TRACKING_PATH, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj["deal_id"] == deal_id and obj["step"] == step:
                    return True
            except:
                continue
    return False


def update_dca_log(deal_id, step, symbol):
    with open(DCA_TRACKING_PATH, "a") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "deal_id": deal_id,
                    "step": step,
                    "symbol": symbol,
                }
            )
            + "\n"
        )


def write_log(entry):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_path = LOG_DIR / today
    log_path.mkdir(parents=True, exist_ok=True)
    file_path = log_path / "dca_log.jsonl"
    with open(file_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_ml_snapshot(
    symbol,
    deal_id,
    indicators,
    recovery_odds,
    entry_score,
    current_score,
    tp1_shift,
    be_improvement,
    safu_score,
    btc_status,
    confidence_score,
):
    snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "deal_id": deal_id,
        "entry_score": entry_score,
        "current_score": current_score,
        "btc_status": btc_status,
        "safu_score": safu_score,
        "tp1_shift": round(tp1_shift, 2),
        "be_improvement": round(be_improvement, 2),
        "recovery_odds": round(recovery_odds, 2),
        "confidence_score": round(confidence_score, 2),
        **indicators,
    }
    snap_path = SNAPSHOT_DIR / f"{symbol}_{deal_id}.jsonl"
    with open(snap_path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")


def run():
    logging.info("📊 Evaluating active 3Commas trades")
    btc_status = get_btc_status(config.get("btc_indicators", {}))
    logging.info(
        f"🧐 BTC Market Status: {'✅ SAFE' if btc_status == 'SAFE' else '⚠️ UNSAFE'}"
    )

    trades = get_live_3c_trades()
    # print(f"[INFO] Pulled {len(trades)} active trades")
    for trade in trades:
        # print("[INFO] Pulled trade keys:", list(trade.keys()))
        trigger_pct = config.get("drawdown_trigger_pct", 1.5)
    so_table = config["so_volume_table"]

    for trade in trades:
        symbol = trade["pair"]
        short_symbol = symbol.replace("USDT_", "")
        total_spent = float(trade.get("bought_volume") or 0)
        deal_id = trade.get("id")

        avg_entry_price = float(
            trade.get("bought_average_price")
            or trade.get("average_buy_price")
            or trade.get("base_order_average_price")
            or 0
        )
        current_price = float(trade.get("current_price") or 0)
        created_at = trade.get("created_at")
        try:
            entry_ts = int(
                datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
                * 1000
            )
        except:
            entry_ts = None

        deviation_pct = (
            ((avg_entry_price - current_price) / avg_entry_price) * 100
            if avg_entry_price
            else 0.0
        )
        if deviation_pct < 0:
            print(f"💰 Skipping {symbol} — already in profit ({deviation_pct:.2f}%)")
            reason = "in_profit"
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "deal_id": deal_id,
                "symbol": symbol,
                "step": 0,
                "current_price": current_price,
                "avg_entry_price": avg_entry_price,
                "entry_score": None,
                "current_score": None,
                "open_pnl": (
                    (
                        (current_price - avg_entry_price)
                        * (total_spent / avg_entry_price)
                    )
                    if avg_entry_price
                    else 0.0
                ),
                "tp1_shift": None,
                "be_improvement": None,
                "recovery_odds": None,
                "confidence_score": None,
                "safu_score": None,
                "btc_status": btc_status,
                "tv_tag": None,
                "tv_kicker": None,
                "zombie_tagged": False,
                "decision": "skipped",
                "rejection_reason": reason,
            }
            write_log(log_entry)
            continue

        indicators = get_latest_indicators(short_symbol)
        safu_score = get_safu_score(short_symbol, avg_entry_price, current_price)

        entry_score = load_entry_score_from_redis(deal_id)
        if entry_score is None and entry_ts:
            entry_score = load_fork_entry_score(short_symbol, entry_ts)
            if entry_score is not None:
                save_entry_score_to_redis(deal_id, entry_score)

        current_score = compute_fork_score(short_symbol)
        new_avg_price = simulate_new_avg_price(
            avg_entry_price, so_table[0], current_price
        )
        tp1_shift = (
            ((1.015 * new_avg_price - current_price) / current_price) * 100
            if current_price
            else 0.0
        )
        be_improvement = (
            ((avg_entry_price - new_avg_price) / avg_entry_price) * 100
            if avg_entry_price
            else 0.0
        )

        macd_lift = get_macd_lift(short_symbol) or 0.0
        rsi_slope = get_rsi_slope(short_symbol) or 0.0
        indicators.update(
            {
                "macd_lift": macd_lift,
                "rsi_slope": rsi_slope,
                "drawdown_pct": deviation_pct,
            }
        )

        snapshot = get_latest_snapshot(symbol, deal_id)
        recovery_odds = predict_recovery_odds(snapshot)
        confidence_score = predict_confidence_score(snapshot)
        zombie_tagged = is_zombie_trade(indicators, recovery_odds, current_score)

        if zombie_tagged:
            print(f"💀 Skipping {symbol} due to zombie tag")
            continue

        trade_features = {
            "recovery_odds": recovery_odds,
            "confidence_score": confidence_score,
            "safu_score": safu_score,
            "entry_score": entry_score or 0,
            "current_score": current_score or 0,
            "rsi": indicators.get("rsi", 50),
            "macd_histogram": indicators.get("macd_histogram", 0),
            "adx": indicators.get("adx", 20),
        }

        health = evaluate_trade_health(trade_features)
        health_score = health["health_score"]
        health_status = health["health_status"]

        tv_tag, tv_kicker = load_tv_kicker(short_symbol)
        should_fire, reason, _ = should_dca(
            trade=trade,
            config=config,
            indicators=indicators,
            btc_status=btc_status,
            entry_score=entry_score,
            current_score=current_score,
            safu_score=safu_score,
            tp1_sim_pct=tp1_shift,
        )

        last_conf_score, last_tp1_shift = get_last_snapshot_values(
            short_symbol, deal_id
        )
        conf_delta = confidence_score - last_conf_score
        tp1_gain = tp1_shift - last_tp1_shift

        override_conf = config.get("confidence_dca_guard", {})
        if (
            config.get("use_confidence_override", True)
            and not should_fire
            and confidence_score >= config.get("min_confidence_odds", 0.65)
            and conf_delta >= override_conf.get("min_confidence_delta", 0.05)
            and tp1_gain >= override_conf.get("min_tp1_shift_gain_pct", 0.25)
            and deviation_pct >= trigger_pct
            and safu_score >= override_conf.get("safu_score_min", 0.5)
            and indicators.get("macd_lift", 0.0)
            >= override_conf.get("macd_lift_min", 0.00005)
            and indicators.get("rsi_slope", 0.0)
            >= override_conf.get("rsi_slope_min", 1.0)
        ):
            print("🚀 Confidence override triggered")
            reason = "confidence_override"
            should_fire = True

        # === Smart Soft Confidence Rescue (new logic) ===
        soft_conf_override = config.get("soft_confidence_override", {})

        if (
            config.get("use_soft_confidence_override", True)
            and not should_fire
            and confidence_score >= soft_conf_override.get("min_confidence", 0.75)
            and recovery_odds >= soft_conf_override.get("min_recovery_odds", 0.8)
            and safu_score >= soft_conf_override.get("min_safu_score", 0.7)
            and health_score >= soft_conf_override.get("min_health_score", 0.6)
            and deviation_pct >= soft_conf_override.get("min_drawdown_pct", 2.0)
            and conf_delta >= soft_conf_override.get("min_confidence_delta", 0.05)
            and tp1_shift >= soft_conf_override.get("min_tp1_shift_pct", 2.0)
        ):

            print("🔓 Smart Soft Rescue Triggered (confidence & health aligned)")
            reason = "smart_soft_rescue"
            should_fire = True

        # --- Soft backup: allow ML rescue if recovery odds + confidence are good, even if indicators fail ---
        # if (
        #            config.get("use_confidence_override", True) and
        #            not should_fire and
        #            confidence_score >= 0.72 and    # require strong confidence
        #            recovery_odds >= 0.8 and        # require acceptable recovery probability
        #            safu_score >= 0.75 and            # require safu still safe
        #            deviation_pct >= trigger_pct     # still need drawdown
        # ):
        #            print("🔓 Soft ML rescue triggered: Recovery Odds + Confidence good despite indicators")
        #            reason = "soft_ml_rescue"
        #            should_fire = True

        last_step = get_last_fired_step(deal_id)
        step = last_step + 1
        ladder_amount = so_table[step] if step < len(so_table) else so_table[-1]

        predicted = predict_spend_volume(
            {
                **indicators,
                "entry_score": entry_score,
                "current_score": current_score,
                "tp1_shift": tp1_shift,
                "recovery_odds": recovery_odds,
                "confidence_score": confidence_score,
                "zombie_tagged": zombie_tagged,
                "btc_status": 1 if btc_status == "SAFE" else 0,
            }
        )

        desired_volume = adjust_volume(
            predicted,
            total_spent,
            max_budget=config.get("max_trade_usdt", 2000),
            drawdown_pct=deviation_pct,
            tp1_shift_pct=tp1_shift,
        )

        # === Health Emoji Mapping ===
        health_emoji = {"Healthy": "❤️", "Weak": "⚠️", "Zombie": "☠️"}.get(
            health_status, "❓"
        )

        print(
            f"\n🔍 Checking {symbol} | SOs: {trade.get('completed_manual_safety_orders_count', 0)} | Spent: ${total_spent:.2f}"
        )
        print(
            f"📉 Drawdown: {deviation_pct:.2f}% | SAFU: {safu_score} | {health_emoji} Health: {health_status} ({health_score:.2f})"
        )
        print(
            f"📊 Entry Score: {entry_score} → Now: {current_score} | BE ↓ {be_improvement:.2f}%"
        )
        print(
            f"🧪 Sim BE: ${new_avg_price:.5f} | TP1 Shift: {tp1_shift:.2f}% | Recovery Odds: {recovery_odds:.2f} | Confidence: {confidence_score:.2f}"
        )

        log_ml_snapshot(
            short_symbol,
            deal_id,
            indicators,
            recovery_odds,
            entry_score,
            current_score,
            tp1_shift,
            be_improvement,
            safu_score,
            btc_status,
            confidence_score,
        )

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "deal_id": deal_id,
            "symbol": symbol,
            "step": step,
            "current_price": current_price,
            "avg_entry_price": avg_entry_price,
            "entry_score": entry_score,
            "current_score": current_score,
            "open_pnl": (
                ((current_price - avg_entry_price) * (total_spent / avg_entry_price))
                if avg_entry_price
                else 0.0
            ),
            "tp1_shift": tp1_shift,
            "be_improvement": be_improvement,
            "recovery_odds": recovery_odds,
            "confidence_score": confidence_score,
            "safu_score": safu_score,
            "btc_status": btc_status,
            "tv_tag": tv_tag,
            "tv_kicker": tv_kicker,
            "health_score": health_score,
            "health_status": health_status,
            "zombie_tagged": zombie_tagged,
            "decision": "skipped",
            "rejection_reason": reason,
        }

        if not should_fire:
            print(f"[CHECK] Rejection reason: {reason}")
            print(f"[CHECK] Indicators: {json.dumps(indicators, indent=2)}")
            write_log(log_entry)
            continue

        if was_dca_fired_recently(deal_id, step):
            print("⏳ Already fired this step")
            log_entry["rejection_reason"] = "already_fired"
            write_log(log_entry)
            continue

        print(
            f"✅ Sending DCA signal for {symbol} | Volume: {desired_volume:.2f} USDT (Step {step})"
        )
        send_dca_signal(symbol, volume=desired_volume)
        update_dca_log(deal_id, step, short_symbol)
        log_entry["decision"] = "fired"
        log_entry["volume_sent"] = desired_volume
        write_log(log_entry)


if __name__ == "__main__":
    run()
