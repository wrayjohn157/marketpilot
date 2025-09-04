from typing import List


def detect_local_reversal(prices: List[float]) -> bool:
    """Detect local bottom reversal (V-shape) from price data."""
    if len(prices) < 5:
        return False
    return prices[-4] > prices[-3] > prices[-2] and prices[-2] < prices[-1]


#!/usr/bin/env python3
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml
from modules.fork_safu_evaluator import get_safu_exit_decision, load_safu_exit_model

safu_exit_model = load_safu_exit_model()

# === Paths ===
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.unified_config_manager import (
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
)
from dca.modules.dca_decision_engine import should_dca
from dca.modules.fork_safu_evaluator import get_safu_score
from dca.utils.btc_filter import get_btc_status
from dca.utils.entry_utils import (
    get_latest_indicators,
    get_live_3c_trades,
    get_macd_lift,
    get_rsi_slope,
    load_entry_score_from_redis,
    load_fork_entry_score,
    save_entry_score_to_redis,
    send_dca_signal,
    simulate_new_avg_price,
)
from dca.utils.fork_score_utils import compute_fork_score
from dca.utils.recovery_confidence_utils import predict_confidence_score
from dca.utils.recovery_odds_utils import (
    SNAPSHOT_PATH,
    get_latest_snapshot,
    predict_recovery_odds,
)
from dca.utils.spend_predictor import adjust_volume, predict_spend_volume
from dca.utils.trade_health_evaluator import evaluate_trade_health
from dca.utils.tv_utils import load_tv_kicker
from dca.utils.zombie_utils import is_zombie_trade
from utils.redis_manager import RedisKeyManager, get_redis_manager

CONFIG_PATH = PATHS[
    "dca_config"
]  # CONFIG_PATH = get_path("dca_config") #CONFIG_PATH = get_path("base") / "dca" / "config" / "dca_config.yaml"
LOG_DIR = get_path("base") / "dca" / "logs"
SNAPSHOT_DIR = SNAPSHOT_PATH
DCA_TRACKING_PATH = LOG_DIR / "dca_tracking" / "dca_fired.jsonl"

SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
DCA_TRACKING_PATH.parent.mkdir(parents=True, exist_ok=True)


with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    except (json.JSONDecodeError, IOError, KeyError) as e:
        logger.warning(f"Failed to read snapshot for {symbol}_{deal_id}: {e}")
        return 0.0, 0.0


def get_last_logged_snapshot(deal_id):
    if not DCA_TRACKING_PATH.exists():
        return None
    try:
        with open(DCA_TRACKING_PATH, "r") as f:
            entries = [
                json.loads(line) for line in f if f'"deal_id": {deal_id}' in line
            ]
        if not entries:
            return None
        return entries[-1]
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read tracking data for deal {deal_id}: {e}")
        return None


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
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Failed to parse tracking line: {e}")
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
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Failed to parse tracking line: {e}")
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
        step = None  # Ensure step is always defined before use
        # print("[INFO] Pulled trade keys:", list(trade.keys()))
        trigger_pct = config.get("drawdown_trigger_pct", 1.5)
    so_table = config["so_volume_table"]

    for trade in trades:
        symbol = trade["pair"]
        short_symbol = symbol.replace("USDT_", "")
        deal_id = trade.get("id")
        # --- Calculate spent_so_far using 3Commas trade fields ---
        base_order_volume = float(trade.get("bought_volume", 0))
        current_funds = float(trade.get("current_funds", 0))
        spent_so_far = float(current_funds - base_order_volume)
        total_spent = base_order_volume

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
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse entry timestamp: {e}")
            entry_ts = None

        if avg_entry_price == 0:
            print(f"⚠️ {symbol} missing avg_entry_price, skipping")
            continue

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
                "spent": total_spent,
            }
            write_log(log_entry)
            continue

        indicators = get_latest_indicators(short_symbol)
        # === MACD Cross Guard ===
        if config.get("require_macd_cross", False):
            lookback = config.get("macd_cross_lookback", 1)
            macd_vals = get_latest_indicators(short_symbol).get(
                "macd_cross_history", []
            )
            if len(macd_vals) < lookback + 1:
                print(f"⚠️ Not enough MACD history to check cross for {symbol}")
                reason = "insufficient_macd_data"
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
                    "spent": total_spent,
                }
                write_log(log_entry)
                continue
            macd_prev, signal_prev = macd_vals[-2]
            macd_curr, signal_curr = macd_vals[-1]
            if not (macd_prev < signal_prev and macd_curr > signal_curr):
                print(f"⛔ Skipping {symbol} — no recent MACD cross")
                reason = "no_macd_cross"
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
                    "spent": total_spent,
                }
                write_log(log_entry)
                continue
        safu_score = get_safu_score(short_symbol, avg_entry_price, current_price)

        entry_score = load_entry_score_from_redis(deal_id)
        if entry_score is None and entry_ts:
            entry_score = load_fork_entry_score(short_symbol, entry_ts)
            if entry_score is not None:
                save_entry_score_to_redis(deal_id, entry_score)
        if entry_score is None:
            print(f"⚠️ {symbol} missing entry_score — setting to 0.0")
            entry_score = 0.0

        current_score = compute_fork_score(short_symbol)
        new_avg_price = simulate_new_avg_price(
            avg_entry_price, so_table[0], current_price
        )
        tp1_shift = (
            ((1.006 * new_avg_price - current_price) / current_price) * 100
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

        # === Local Bottom Reversal Detection ===
        allow_dca = True
        rejection_reason = None
        # Attempt to load klines for price action (assume 1h TF from indicators if available)
        klines = indicators.get("klines", [])
        if not klines:
            # If not present, skip reversal check
            recent_prices = []
            reversal_signal = False
        else:
            recent_prices = [k["close"] for k in klines[-6:]]
            reversal_signal = detect_local_reversal(recent_prices)
        # Check YAML bottom reversal filter
        br_filter = config.get("bottom_reversal_filter", {})
        # Standard bottom reversal filter logic
        if br_filter.get_cache("enabled", False):
            if not reversal_signal:
                rejection_reason = "no_bottom_reversal"
                allow_dca = False
            elif indicators["macd_lift"] < br_filter.get_cache("min_macd_lift", 0.0):
                rejection_reason = "macd_lift_too_weak"
                allow_dca = False
            elif indicators["rsi_slope"] < br_filter.get_cache("min_rsi_slope", 0.0):
                rejection_reason = "rsi_slope_too_flat"
                allow_dca = False
        # --- Bottom Reversal alternate filter (from improved) ---
        # If bottom_reversal_filter.enabled, allow DCA if MACD lift, RSI slope, and RSI exceed thresholds
        allow_bottom_dca = False
        if br_filter.get_cache("enabled", False):
            min_macd = br_filter.get_cache("min_macd_lift", 0.0)
            min_slope = br_filter.get_cache("min_rsi_slope", 0.0)
            rsi_floor = br_filter.get_cache("rsi_floor", 0)
            rsi = indicators.get("rsi", 0)
            if (
                indicators["macd_lift"] > min_macd
                and indicators["rsi_slope"] > min_slope
                and rsi > rsi_floor
            ):
                allow_bottom_dca = True

        snapshot = get_latest_snapshot(symbol, deal_id)
        recovery_odds = predict_recovery_odds(snapshot)
        confidence_score = predict_confidence_score(snapshot)
        zombie_tagged = is_zombie_trade(indicators, recovery_odds, current_score)

        if zombie_tagged:
            print(f"💀 Skipping {symbol} due to zombie tag")
            continue

        # === ML-powered SAFU Exit Check ===
        should_exit, exit_reason, ml_exit_prob = get_safu_exit_decision(
            trade,
            config.get("safu_reentry", {}),
            model=safu_exit_model,
        )

        if should_exit:
            logger.info(
                f"🛑 [SAFU Decision] Exit triggered for {symbol}: {exit_reason} | ML={ml_exit_prob:.2f}"
                if ml_exit_prob is not None
                else f"🛑 [SAFU Decision] Exit triggered for {symbol}: {exit_reason}"
            )
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "deal_id": deal_id,
                "symbol": symbol,
                "step": get_last_fired_step(deal_id) + 1,
                "current_price": current_price,
                "avg_entry_price": avg_entry_price,
                "entry_score": entry_score,
                "current_score": current_score,
                "open_pnl": (
                    (
                        (current_price - avg_entry_price)
                        * (total_spent / avg_entry_price)
                    )
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
                "decision": "exit",
                "rejection_reason": exit_reason,
                "ml_exit_prob": ml_exit_prob,
                "spent": total_spent,
            }
            write_log(log_entry)
            continue
        else:
            logger.info(
                f"✅ [SAFU Decision] Holding {symbol} | Reason: {exit_reason or 'healthy'} | ML={ml_exit_prob:.2f}"
                if ml_exit_prob is not None
                else f"✅ [SAFU Decision] Holding {symbol} | Reason: {exit_reason or 'healthy'}"
            )

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

        # === SAFU + ML-based exit decision logging ===
        should_exit, exit_reason, ml_exit_prob = get_safu_exit_decision(
            trade, config.get("safu_reentry", {}), model=safu_exit_model
        )

        if should_exit:
            logger.warning(
                f"🛑 [SAFU Decision] Exit triggered for {symbol}: {exit_reason} | ML={ml_exit_prob:.2f}"
                if ml_exit_prob is not None
                else f"🛑 [SAFU Decision] Exit triggered for {symbol}: {exit_reason}"
            )
            # Optional: apply trimming, abandon, or tagging logic here
        else:
            logger.info(
                f"✅ [SAFU Decision] Holding {symbol} | Reason: {exit_reason or 'healthy'} | ML={ml_exit_prob:.2f}"
                if ml_exit_prob is not None
                else f"✅ [SAFU Decision] Holding {symbol} | Reason: {exit_reason or 'healthy'}"
            )
        should_fire, reason, _ = should_dca(
            trade=trade,
            config=config,
            indicators=indicators,
            btc_status=btc_status,
            entry_score=entry_score,
            current_score=current_score,
            safu_score=safu_score,
            tp1_sim_pct=tp1_shift,
            recovery_odds=recovery_odds,
        )
        # --- Bottom reversal trigger (new logic, supports soft/hard mode) ---
        assist_reasons = []
        rejection_reasons = []
        br_cfg = config.get("bottom_reversal_trigger", {})

        def bottom_reversal_indicates_reversal(snapshot, br_cfg):
            # Simple proxy: use bottom_reversal_filter logic (for now)
            # In real code, this should invoke a utility for bottom reversal detection.
            min_macd = br_cfg.get("min_macd_lift", 0.0)
            min_slope = br_cfg.get("min_rsi_slope", 0.0)
            rsi_floor = br_cfg.get("rsi_floor", 0)
            rsi = indicators.get("rsi", 0)
            return (
                indicators.get("macd_lift", 0.0) > min_macd
                and indicators.get("rsi_slope", 0.0) > min_slope
                and rsi > rsi_floor
            )

        bottom_reversal_ok = False
        if br_cfg.get("enabled", False):
            if bottom_reversal_indicates_reversal(snapshot, br_cfg):
                bottom_reversal_ok = True
                assist_reasons.append("bottom_reversal_detected")
            elif br_cfg.get("mode") == "hard":
                rejection_reasons.append("bottom_reversal_not_confirmed")
        # In soft mode, bottom reversal only assists, does not block DCA
        # In hard mode, it blocks if not present
        if rejection_reasons:
            should_fire = False
            reason = rejection_reasons[0]

        # === Enforce RSI floor from bottom_reversal_filter before DCA trigger ===
        bottom_reversal_cfg = config.get("bottom_reversal_filter", {})
        rsi_floor = bottom_reversal_cfg.get("rsi_floor", 0)
        if indicators.get("rsi", 100) < rsi_floor:
            rejection_reason = f"RSI {indicators['rsi']:.2f} below floor {rsi_floor}"
            # step may not be set yet; set it to last_fired_step + 1 for logging
            if step is None:
                step = get_last_fired_step(deal_id) + 1
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
                    (
                        (current_price - avg_entry_price)
                        * (total_spent / avg_entry_price)
                    )
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
                "rejection_reason": rejection_reason,
                "spent": total_spent,
            }
            # Log and skip
            write_log(log_entry)
            continue

        last_conf_score, last_tp1_shift = get_last_snapshot_values(
            short_symbol, deal_id
        )
        conf_delta = confidence_score - last_conf_score
        tp1_gain = tp1_shift - last_tp1_shift

        # === Check step memory with YAML-configurable guard ===
        last_logged = get_last_logged_snapshot(deal_id)
        step_guard = config.get("step_repeat_guard", {})
        if step_guard.get("enabled", True) and last_logged:
            prev_step = last_logged.get("step", 0)
            prev_confidence = last_logged.get("confidence_score", 0)
            prev_tp1_shift = last_logged.get("tp1_shift", 0)
            same_step = prev_step == get_last_fired_step(deal_id)
            min_conf_delta = step_guard.get("min_conf_delta", 0.02)
            min_tp1_shift = step_guard.get("min_tp1_delta", 0.25)
            conf_delta_ok = (confidence_score - prev_confidence) >= min_conf_delta
            tp1_delta_ok = (tp1_shift - prev_tp1_shift) >= min_tp1_shift
            if same_step and not (conf_delta_ok or tp1_delta_ok):
                # Only allow re-fire if confidence or TP1 shift improved enough
                reason = "no_step_improvement"
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "deal_id": deal_id,
                    "symbol": symbol,
                    "step": prev_step,
                    "current_price": current_price,
                    "avg_entry_price": avg_entry_price,
                    "entry_score": entry_score,
                    "current_score": current_score,
                    "open_pnl": (
                        (
                            (current_price - avg_entry_price)
                            * (total_spent / avg_entry_price)
                        )
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
                    "spent": total_spent,
                }
                write_log(log_entry)
                continue

            # === Insert min_price_delta_pct guard after min_conf_delta/min_tp1_delta logic ===
            def log_reason(deal_id, symbol, reason, msg):
                # Helper for logging reasons (minimal, for patch completeness)
                print(msg)

            if config.get("step_repeat_guard", {}).get("enabled", False):
                last_price = last_logged.get("current_price")
                if last_price is not None and current_price is not None:
                    min_price_delta_pct = config["step_repeat_guard"].get(
                        "min_price_delta_pct", 0
                    )
                    price_delta_pct = (
                        abs((current_price - last_price) / last_price) * 100
                    )
                    if price_delta_pct < min_price_delta_pct:
                        log_msg = f"⛔️ Skipping due to step_repeat_guard.min_price_delta_pct ({price_delta_pct:.2f}% < {min_price_delta_pct}%)"
                        print(log_msg)
                        log_reason(deal_id, symbol, "step_repeat_guard_price", log_msg)
                        # Compose a log entry and skip
                        log_entry = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "deal_id": deal_id,
                            "symbol": symbol,
                            "step": prev_step,
                            "current_price": current_price,
                            "avg_entry_price": avg_entry_price,
                            "entry_score": entry_score,
                            "current_score": current_score,
                            "open_pnl": (
                                (
                                    (current_price - avg_entry_price)
                                    * (total_spent / avg_entry_price)
                                )
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
                            "rejection_reason": "step_repeat_guard_price",
                            "spent": total_spent,
                        }
                        write_log(log_entry)
                        continue

        # === Step Progression Guard (Prevents runaway steps at similar prices) ===
        progress_guard = config.get("step_progress_guard", {})
        if progress_guard.get("enabled", True) and last_logged:
            prev_price = last_logged.get("current_price", 0)
            prev_time = datetime.fromisoformat(last_logged["timestamp"])
            prev_be = last_logged.get("be_improvement", 0)

            price_change_pct = (
                abs(current_price - prev_price) / prev_price * 100 if prev_price else 0
            )
            time_elapsed = (datetime.utcnow() - prev_time).total_seconds()
            be_gain = be_improvement - prev_be

            if (
                price_change_pct < progress_guard.get("min_price_change_pct", 0.3)
                and time_elapsed < progress_guard.get("min_seconds_elapsed", 600)
                and be_gain < progress_guard.get("min_be_improvement_pct", 0.5)
            ):
                print(f"🛑 Step {step} blocked: no significant change from last DCA")
                log_entry["rejection_reason"] = "step_progress_insufficient"
                log_entry["decision"] = "skipped"
                write_log(log_entry)
                continue

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
        step = last_step + 1  # step is now set for DCA evaluation
        ladder_amount = so_table[step] if step < len(so_table) else so_table[-1]

        # --- Spend model volume adjustment ---
        if config.get("use_ml_spend_model", False):
            # Use ML spend model if enabled in config
            from dca.utils.spend_predictor import (
                predict_spend_volume as predict_spend_amount,
            )

            # Compose input features as expected by the model
            input_features = {
                "entry_score": entry_score,
                "current_score": current_score,
                "drawdown_pct": deviation_pct,
                "safu_score": safu_score,
                "macd_lift": indicators.get("macd_lift"),
                "rsi": indicators.get("rsi"),
                "rsi_slope": indicators.get("rsi_slope"),
                "adx": indicators.get("adx"),
                "tp1_shift": tp1_shift,
                "recovery_odds": recovery_odds,
                "confidence_score": confidence_score,
                "zombie_tagged": zombie_tagged,
                "btc_rsi": (
                    indicators.get("btc_context", {}).get("rsi")
                    if "btc_context" in indicators
                    else None
                ),
                "btc_macd_histogram": (
                    indicators.get("btc_context", {}).get("macd_histogram")
                    if "btc_context" in indicators
                    else None
                ),
                "btc_adx": (
                    indicators.get("btc_context", {}).get("adx")
                    if "btc_context" in indicators
                    else None
                ),
                "btc_status": (
                    indicators.get("btc_context", {}).get("status")
                    if "btc_context" in indicators
                    else btc_status
                ),
            }
            # If btc_context is not in indicators, try to get from btc_status context
            # fallback (for legacy): btc_context from get_btc_status
            if "btc_context" not in indicators:
                btc_context = {}
                try:
                    btc_context = get_btc_status(config.get("btc_indicators", {}))
                except Exception:
                    btc_context = {}
                input_features["btc_rsi"] = (
                    btc_context["rsi"] if isinstance(btc_context, dict) else None
                )
                input_features["btc_macd_histogram"] = (
                    btc_context["macd_histogram"]
                    if isinstance(btc_context, dict)
                    else None
                )
                input_features["btc_adx"] = (
                    btc_context["adx"] if isinstance(btc_context, dict) else None
                )
                input_features["btc_status"] = (
                    btc_context.get("status")
                    if isinstance(btc_context, dict)
                    else btc_status
                )

            # Ensure BTC context values are properly cast as floats
            btc_context = (
                indicators.get("btc_context")
                if "btc_context" in indicators
                else btc_context
                if "btc_context" in locals()
                else None
            )
            if btc_context and isinstance(btc_context, dict):
                input_features["btc_rsi"] = float(btc_context.get("rsi", 0.0))
                input_features["btc_macd_histogram"] = float(
                    btc_context.get("macd_histogram", 0.0)
                )
                input_features["btc_adx"] = float(btc_context.get("adx", 0.0))
            else:
                input_features["btc_rsi"] = 0.0
                input_features["btc_macd_histogram"] = 0.0
                input_features["btc_adx"] = 0.0

            volume = predict_spend_amount(input_features)
        else:
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
            volume = adjust_volume(
                predicted,
                total_spent,
                max_budget=config.get("max_trade_usdt", 2000),
                drawdown_pct=deviation_pct,
                tp1_shift_pct=tp1_shift,
            )
        predicted_volume = volume

        # === Spend Guard Logic ===
        if config.get("spend_guard", {}).get("enabled") and deviation_pct is not None:
            thresholds = config["spend_guard"].get("drawdown_thresholds", [])
            cap = config.get("max_trade_usdt", 2000)

            for threshold in sorted(thresholds, key=lambda x: x["dd_pct"]):
                if deviation_pct >= threshold["dd_pct"]:
                    cap = threshold["max_spend_usdt"]

            # Use spent_so_far as calculated above
            remaining_allowed = cap - spent_so_far
            # Stricter spend guard logic
            if remaining_allowed <= 0 or volume <= 0:
                print(
                    f"⛔ [Spend Guard] Blocked: Cap ${cap} reached or no volume allowed"
                )
                rejection_reason = "spend_guard_limit"
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
                        (
                            (current_price - avg_entry_price)
                            * (total_spent / avg_entry_price)
                        )
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
                    "rejection_reason": rejection_reason,
                    "spent": total_spent,
                }
                write_log(log_entry)
                continue
            else:
                if volume > remaining_allowed:
                    print(
                        f"💰 [Spend Guard] Trim: Drawdown {deviation_pct:.2f}% → Cap ${cap} → Remaining Allowed: ${remaining_allowed:.2f}"
                    )
                    volume = remaining_allowed

        # --- TP1 shift soft cap volume booster ---
        tp1_soft_cap = config.get("tp1_shift_soft_cap")
        if tp1_soft_cap is not None:
            if tp1_shift < tp1_soft_cap:
                volume *= 1.25

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
        log_entry["spent"] = total_spent

        # === Adaptive Step Spacing Logic ===
        adaptive_cfg = config.get("adaptive_step_spacing", {})
        if adaptive_cfg.get("enabled", False) and last_logged:
            base_spacing_pct = adaptive_cfg.get("base_spacing_pct", 5.0)
            adx = indicators.get("adx", 20)
            confidence = confidence_score

            adx_factor = max(1.0, (20 - adx) / 10)  # More spacing if ADX is weak
            conf_factor = 1.0 - min(
                confidence, 1.0
            )  # More spacing if confidence is low

            adjusted_spacing_pct = base_spacing_pct * adx_factor * conf_factor

            last_price = last_logged.get("current_price")
            if last_price:
                gap_pct = abs((last_price - current_price) / last_price) * 100
                if gap_pct < adjusted_spacing_pct:
                    print(
                        f"🛑 Adaptive spacing block: gap {gap_pct:.2f}% < {adjusted_spacing_pct:.2f}%"
                    )
                    log_entry["rejection_reason"] = "adaptive_spacing_block"
                    log_entry["decision"] = "skipped"
                    write_log(log_entry)
                    continue

        # === DCA Block: Price above last SO price ===
        last_so_price = trade.get("last_dca_price")
        if last_so_price:
            try:
                last_so_price = float(last_so_price)
            except Exception:
                last_so_price = None
        if last_so_price and current_price >= last_so_price:
            rejection_reason = "price_above_last_so"
            should_fire = False

        # === DCA Block: Budget Cap ===
        dca_cfg = config.get("dca", {}) if "dca" in config else config
        max_budget = dca_cfg.get("max_usdt_per_trade", 2000)
        if total_spent + predicted_volume > max_budget:
            rejection_reason = "budget_exceeded"
            should_fire = False

        # --- Ensure rejection_reason is reflected in CLI log block ---
        if not should_fire:
            print(f"[CHECK] Rejection reason: {rejection_reason or reason}")
            print(f"[CHECK] Indicators: {json.dumps(indicators, indent=2)}")
            log_entry["rejection_reason"] = rejection_reason or reason
            if assist_reasons:
                log_entry["assist_reasons"] = assist_reasons
            write_log(log_entry)
            continue

        # === Trailing Step Guard Enforcement ===
        trailing_cfg = config.get("trailing_step_guard", {})
        if trailing_cfg.get("enabled", False) and last_logged:
            last_price = last_logged.get("current_price")
            min_gap = trailing_cfg.get("min_pct_gap_from_last_dca", 2.0)
            allow_override_conf = trailing_cfg.get(
                "allow_override_if_confidence_gt", None
            )
            allow_override_time = trailing_cfg.get(
                "allow_override_if_time_elapsed_min", None
            )

            gap_pct = (
                abs((current_price - last_price) / last_price) * 100
                if last_price
                else 0.0
            )

            time_since_last = (
                (
                    datetime.utcnow() - datetime.fromisoformat(last_logged["timestamp"])
                ).total_seconds()
                / 60
                if last_logged.get("timestamp")
                else 999
            )

            allow_override = (
                allow_override_conf is not None
                and confidence_score >= allow_override_conf
            ) or (
                allow_override_time is not None
                and time_since_last >= allow_override_time
            )

            if gap_pct < min_gap and not allow_override:
                print(
                    f"⛔️ Trailing Step Guard blocked: gap {gap_pct:.2f}% < {min_gap}%"
                )
                log_entry["rejection_reason"] = "trailing_step_guard_block"
                log_entry["decision"] = "skipped"
                write_log(log_entry)
                continue

        if was_dca_fired_recently(deal_id, step):
            print("⏳ Already fired this step")
            log_entry["rejection_reason"] = "already_fired"
            log_entry["spent"] = total_spent
            write_log(log_entry)
            continue

        print(
            f"✅ Sending DCA signal for {symbol} | Volume: {volume:.2f} USDT (Step {step})"
        )
        send_dca_signal(symbol, volume=volume)
        update_dca_log(deal_id, step, short_symbol)
        log_entry["decision"] = "fired"
        log_entry["volume_sent"] = volume
        if assist_reasons:
            log_entry["assist_reasons"] = assist_reasons
        write_log(log_entry)


if __name__ == "__main__":
    run()
