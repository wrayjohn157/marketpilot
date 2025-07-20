# sim_dca_engine.py

import argparse
import time
import json
from pathlib import Path
from utils.sim_kline_loader import load_klines_across_days
from utils.sim_entry_utils import compute_indicators_from_klines
from utils.sim_entry_utils import sim_build_snapshot_features
from utils.sim_recovery_confidence_utils import predict_confidence_and_recovery
from utils.sim_spend_predictor import predict_dca_spend
from utils.sim_btc_context import get_btc_context_for_sim
from utils.sim_safu_utils import get_safu_score

def simulate_dca_engine(klines, entry_price, entry_time, symbol, tf, config, override_config=None):
    results = {"steps": [], "exit_reason": None}
    if not klines:
        results["exit_reason"] = "no_klines"
        return results

    if override_config:
        config.update(override_config)

    trade = {"entry_price": entry_price, "spent_amount": 0}
    btc_context = get_btc_context_for_sim(entry_time)
    indicators_by_ts = compute_indicators_from_klines(klines)

    snapshot_features = sim_build_snapshot_features(indicators_by_ts, {"symbol": symbol, "entry_time": entry_time, "tf": tf}, klines)
    print("[DEBUG] Snapshot features:", json.dumps(snapshot_features, indent=2))

    # --- Guards before processing ---
    entry_score = snapshot_features.get("entry_score", 0)
    current_score = snapshot_features.get("current_score", 0)
    min_score_decay = config.get("min_score_decay", 0.1)
    if (entry_score - current_score) > min_score_decay:
        results["exit_reason"] = "score_decay_guard"
        return results

    if config.get("use_btc_filter", False):
        btc_status_score = snapshot_features.get("btc_status_score", 0)
        if btc_status_score <= 0:
            results["exit_reason"] = "btc_filter_block"
            return results

    # --- Step 3: Modular DCA logic based on config ---
    max_steps = config.get("max_steps", 5)
    base_order_usdt = config.get("base_order_usdt", 100)
    step_multiplier = config.get("step_multiplier", 1.5)
    max_drawdown_pct = config.get("max_drawdown_pct", 30)
    cooldown_bars = config.get("cooldown_bars", 1)

    last_step_ts = None
    step_num = 0

    for kline in klines:
        ts = kline[0]
        price = float(kline[4])
        indicators = indicators_by_ts[ts]

        # --- BTC Market Filter ---
        if config.get("use_btc_filter", False):
            btc_rsi = indicators.get("btc_rsi", 0)
            btc_macd = indicators.get("btc_macd_histogram", 0)
            btc_adx = indicators.get("btc_adx", 0)
            btc_ok = (
                btc_rsi <= config.get("btc_indicators", {}).get("rsi_max", 40) and
                btc_macd <= config.get("btc_indicators", {}).get("macd_histogram_max", 0) and
                btc_adx <= config.get("btc_indicators", {}).get("adx_max", 15)
            )
            if not btc_ok:
                continue

        # --- Trajectory Gating ---
        if config.get("use_trajectory_check", False):
            macd_lift = indicators.get("macd_lift", 0)
            rsi_slope = indicators.get("rsi_slope", 0)
            macd_min = config.get("trajectory_thresholds", {}).get("macd_lift_min", 0)
            rsi_min = config.get("trajectory_thresholds", {}).get("rsi_slope_min", 0)
            if macd_lift < macd_min or rsi_slope < rsi_min:
                continue

        confidence_score, recovery_odds = predict_confidence_and_recovery(snapshot_features, indicators)
        drawdown_pct = max(0, (entry_price - price) / entry_price * 100)
        safu_score = get_safu_score(lookback)
        health_score = confidence_score * safu_score

        # --- DCA eligibility checks ---
        should_dca = (
            drawdown_pct > 1 and
            confidence_score > 0.7 and
            recovery_odds > 0.7 and
            safu_score > 0.5 and
            drawdown_pct < max_drawdown_pct
        )

        if should_dca:
            # Cooldown logic
            if last_step_ts and (ts - last_step_ts) < cooldown_bars * 3600000:
                continue

            # Budget check
            next_volume = base_order_usdt * (step_multiplier ** step_num)
            if trade["spent_amount"] + next_volume > config.get("max_trade_usdt", 2000):
                continue

            volume = next_volume
            new_avg_price = (
                (trade["entry_price"] * trade["spent_amount"]) + (price * volume)
            ) / (trade["spent_amount"] + volume)
            tp1_shift = abs((new_avg_price - trade["entry_price"]) / trade["entry_price"] * 100)

            if tp1_shift > config.get("max_tp1_shift_pct", 50):
                continue

            trade["spent_amount"] += volume
            results["steps"].append({
                "timestamp": ts,
                "step_num": step_num,
                "price": price,
                "volume": volume,
                "tp1_shift": tp1_shift,
                "confidence": confidence_score,
                "recovery_odds": recovery_odds,
                "drawdown_pct": drawdown_pct,
                "safu_score": safu_score,
                "health_score": health_score,
                "entry_score": snapshot_features.get("entry_score", 0),
                "current_score": snapshot_features.get("current_score", 0),
                "btc_status_score": indicators.get("btc_status_score", 0),
                "rejection_reason": None
            })

            last_step_ts = ts
            step_num += 1

            if step_num >= max_steps:
                break
        else:
            results["steps"].append({
                "timestamp": ts,
                "step_num": step_num,
                "price": price,
                "volume": 0.0,
                "tp1_shift": 0.0,
                "confidence": confidence_score,
                "recovery_odds": recovery_odds,
                "drawdown_pct": drawdown_pct,
                "safu_score": safu_score,
                "health_score": health_score,
                "entry_score": snapshot_features.get("entry_score", 0),
                "current_score": snapshot_features.get("current_score", 0),
                "btc_status_score": indicators.get("btc_status_score", 0),
                "rejection_reason": "guard_block"
            })

    # Write results to file
    Path("sim_output").mkdir(exist_ok=True)
    with open(f"sim_output/sim_steps_{entry_time}.json", "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))  # CLI printout of results
    return results


# CLI support
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True, help="Token symbol (e.g., LTC)")
    parser.add_argument("--tf", default="1h", help="Timeframe (e.g., 1h)")
    parser.add_argument("--ts", type=int, required=True, help="Entry timestamp in ms")
    parser.add_argument("--entry_price", type=float, required=True, help="Entry price")
    parser.add_argument("--config", default="/home/signal/market7/sim/config/dca_config.yaml", help="Path to YAML config")

    args = parser.parse_args()

    from utils.sim_kline_loader import load_kline_data
    from utils.sim_config_loader import load_yaml_config

    # Load config
    config = load_yaml_config(args.config)

    # Load klines
    klines = load_kline_data(args.symbol, args.tf, args.ts)

    # Run sim
    simulate_dca_engine(
        klines=klines,
        entry_price=args.entry_price,
        entry_time=args.ts,
        symbol=args.symbol,
        tf=args.tf,
        config=config
    )
