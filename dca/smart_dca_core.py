#!/usr/bin/env python3
"""
Smart DCA Core Engine - Streamlined for Profitable Trade Rescue
Focus: Intelligent trade rescue with ML-powered decision making
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.unified_config_manager import (
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
)
from dca.modules.fork_safu_evaluator import get_safu_score
from dca.utils.btc_filter import get_btc_status
from dca.utils.entry_utils import (
    get_latest_indicators,
    get_live_3c_trades,
    load_entry_score_from_redis,
    load_fork_entry_score,
    save_entry_score_to_redis,
    send_dca_signal,
    simulate_new_avg_price,
)
from dca.utils.fork_score_utils import compute_fork_score
from dca.utils.recovery_confidence_utils import predict_confidence_score
from dca.utils.recovery_odds_utils import get_latest_snapshot, predict_recovery_odds
from dca.utils.spend_predictor import adjust_volume, predict_spend_volume
from dca.utils.trade_health_evaluator import evaluate_trade_health
from dca.utils.zombie_utils import is_zombie_trade

# === Configuration ===
CONFIG_PATH = get_path("dca_config")
LOG_DIR = get_path("base") / "dca" / "logs"
SNAPSHOT_DIR = get_path("base") / "data" / "snapshots"
DCA_TRACKING_PATH = LOG_DIR / "dca_tracking" / "dca_fired.jsonl"

# Ensure directories exist
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
DCA_TRACKING_PATH.parent.mkdir(parents=True, exist_ok=True)

# Load configuration
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class SmartDCACore:
    """
    Streamlined DCA engine focused on profitable trade rescue
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.so_table = config.get(
            "so_volume_table", [20, 15, 25, 40, 65, 90, 150, 250, 400]
        )
        self.max_trade_usdt = config.get("max_trade_usdt", 2000)
        self.trigger_pct = config.get("drawdown_trigger_pct", 1.5)

    def calculate_trade_metrics(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all trade metrics in one place"""
        symbol = trade["pair"]
        short_symbol = symbol.replace("USDT_", "")
        deal_id = trade.get("id")

        # Basic trade data
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

        # Calculate drawdown
        deviation_pct = (
            ((avg_entry_price - current_price) / avg_entry_price) * 100
            if avg_entry_price
            else 0.0
        )

        # Get indicators
        indicators = get_latest_indicators(short_symbol)

        # Calculate scores
        entry_score = self._get_entry_score(deal_id, trade)
        current_score = compute_fork_score(short_symbol)
        safu_score = get_safu_score(short_symbol, avg_entry_price, current_price)

        # Calculate rescue potential
        new_avg_price = simulate_new_avg_price(
            avg_entry_price, self.so_table[0], current_price
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

        # Get ML predictions
        snapshot = get_latest_snapshot(symbol, deal_id)
        recovery_odds = predict_recovery_odds(snapshot)
        confidence_score = predict_confidence_score(snapshot)

        # Trade health
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

        return {
            "symbol": symbol,
            "short_symbol": short_symbol,
            "deal_id": deal_id,
            "current_price": current_price,
            "avg_entry_price": avg_entry_price,
            "deviation_pct": deviation_pct,
            "total_spent": total_spent,
            "spent_so_far": spent_so_far,
            "indicators": indicators,
            "entry_score": entry_score,
            "current_score": current_score,
            "safu_score": safu_score,
            "recovery_odds": recovery_odds,
            "confidence_score": confidence_score,
            "tp1_shift": tp1_shift,
            "be_improvement": be_improvement,
            "health_score": health["health_score"],
            "health_status": health["health_status"],
            "is_zombie": is_zombie_trade(indicators, recovery_odds, current_score),
        }

    def _get_entry_score(self, deal_id: str, trade: Dict[str, Any]) -> float:
        """Get entry score from Redis or calculate it"""
        entry_score = load_entry_score_from_redis(deal_id)
        if entry_score is None:
            created_at = trade.get("created_at")
            if created_at:
                try:
                    entry_ts = int(
                        datetime.strptime(
                            created_at, "%Y-%m-%dT%H:%M:%S.%fZ"
                        ).timestamp()
                        * 1000
                    )
                    short_symbol = trade["pair"].replace("USDT_", "")
                    entry_score = load_fork_entry_score(short_symbol, entry_ts)
                    if entry_score is not None:
                        save_entry_score_to_redis(deal_id, entry_score)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse entry timestamp: {e}")
        return entry_score or 0.0

    def should_rescue_trade(self, metrics: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Smart decision engine for trade rescue
        Returns: (should_rescue, reason, confidence)
        """
        # Quick profit check
        if metrics["deviation_pct"] < 0:
            return False, "already_profitable", 0.0

        # Zombie check
        if metrics["is_zombie"]:
            return False, "zombie_trade", 0.0

        # Basic drawdown check
        if metrics["deviation_pct"] < self.trigger_pct:
            return False, "insufficient_drawdown", 0.0

        # Budget check
        if metrics["total_spent"] >= self.max_trade_usdt:
            return False, "budget_exceeded", 0.0

        # Calculate rescue confidence
        rescue_confidence = self._calculate_rescue_confidence(metrics)

        # ML-powered decision
        if rescue_confidence >= 0.75:
            return True, "high_confidence_rescue", rescue_confidence
        elif rescue_confidence >= 0.60:
            return True, "medium_confidence_rescue", rescue_confidence
        elif rescue_confidence >= 0.45 and metrics["deviation_pct"] >= 3.0:
            return True, "desperate_rescue", rescue_confidence
        else:
            return False, "low_confidence", rescue_confidence

    def _calculate_rescue_confidence(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate rescue confidence based on multiple factors
        Higher score = more likely to be profitable rescue
        """
        confidence = 0.0

        # Recovery odds (40% weight)
        recovery_weight = 0.4
        confidence += metrics["recovery_odds"] * recovery_weight

        # Confidence score (25% weight)
        conf_weight = 0.25
        confidence += metrics["confidence_score"] * conf_weight

        # SAFU score (20% weight)
        safu_weight = 0.20
        confidence += metrics["safu_score"] * safu_weight

        # Health score (10% weight)
        health_weight = 0.10
        confidence += metrics["health_score"] * health_weight

        # Technical indicators (5% weight)
        tech_weight = 0.05
        rsi_score = min(metrics["indicators"].get("rsi", 50) / 100, 1.0)
        macd_score = min(
            max(metrics["indicators"].get("macd_histogram", 0) * 1000, 0), 1.0
        )
        confidence += (rsi_score + macd_score) / 2 * tech_weight

        return min(confidence, 1.0)

    def calculate_rescue_volume(self, metrics: Dict[str, Any]) -> float:
        """Calculate optimal rescue volume"""
        # Get current step
        current_step = self._get_current_step(metrics["deal_id"])

        # Base volume from SO table
        if current_step < len(self.so_table):
            base_volume = self.so_table[current_step]
        else:
            base_volume = self.so_table[-1]

        # ML-based adjustment
        if self.config.get("use_ml_spend_model", True):
            input_features = {
                "entry_score": metrics["entry_score"],
                "current_score": metrics["current_score"],
                "drawdown_pct": metrics["deviation_pct"],
                "safu_score": metrics["safu_score"],
                "recovery_odds": metrics["recovery_odds"],
                "confidence_score": metrics["confidence_score"],
                "tp1_shift": metrics["tp1_shift"],
                "health_score": metrics["health_score"],
                "btc_status": 1,  # Assume safe for now
            }

            # Use ML prediction if available
            try:
                predicted_volume = predict_spend_volume(input_features)
                volume = adjust_volume(
                    predicted_volume,
                    metrics["total_spent"],
                    max_budget=self.max_trade_usdt,
                    drawdown_pct=metrics["deviation_pct"],
                    tp1_shift_pct=metrics["tp1_shift"],
                )
            except Exception as e:
                logger.warning(f"ML volume prediction failed: {e}, using base volume")
                volume = base_volume
        else:
            volume = base_volume

        # Apply spend guard
        remaining_budget = self.max_trade_usdt - metrics["total_spent"]
        volume = min(volume, remaining_budget)

        return max(volume, 0)

    def _get_current_step(self, deal_id: str) -> int:
        """Get current DCA step for this trade"""
        if not DCA_TRACKING_PATH.exists():
            return 0

        try:
            with open(DCA_TRACKING_PATH, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj["deal_id"] == deal_id:
                            return obj.get("step", 0) + 1
                    except (json.JSONDecodeError, KeyError):
                        continue
        except IOError:
            pass

        return 0

    def log_decision(
        self,
        metrics: Dict[str, Any],
        decision: str,
        reason: str,
        confidence: float,
        volume: float = 0,
    ):
        """Log decision with all relevant data"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "deal_id": metrics["deal_id"],
            "symbol": metrics["symbol"],
            "step": self._get_current_step(metrics["deal_id"]),
            "current_price": metrics["current_price"],
            "avg_entry_price": metrics["avg_entry_price"],
            "deviation_pct": metrics["deviation_pct"],
            "entry_score": metrics["entry_score"],
            "current_score": metrics["current_score"],
            "safu_score": metrics["safu_score"],
            "recovery_odds": metrics["recovery_odds"],
            "confidence_score": metrics["confidence_score"],
            "tp1_shift": metrics["tp1_shift"],
            "be_improvement": metrics["be_improvement"],
            "health_score": metrics["health_score"],
            "health_status": metrics["health_status"],
            "rescue_confidence": confidence,
            "decision": decision,
            "reason": reason,
            "volume": volume,
            "total_spent": metrics["total_spent"],
        }

        # Write to daily log
        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_path = LOG_DIR / today
        log_path.mkdir(parents=True, exist_ok=True)
        file_path = log_path / "smart_dca_log.jsonl"

        with open(file_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Log to console
        status_emoji = "✅" if decision == "rescue" else "⛔"
        logger.info(
            f"{status_emoji} {metrics['symbol']} | "
            f"DD: {metrics['deviation_pct']:.1f}% | "
            f"Conf: {confidence:.2f} | "
            f"Reason: {reason}"
        )

    def process_trades(self):
        """Main processing loop - streamlined and focused"""
        logger.info("🚀 Starting Smart DCA Rescue Engine")

        # Get BTC status
        btc_status = get_btc_status(self.config.get("btc_indicators", {}))
        logger.info(f"📊 BTC Status: {btc_status}")

        # Get active trades
        trades = get_live_3c_trades()
        logger.info(f"📈 Processing {len(trades)} active trades")

        rescue_count = 0
        skip_count = 0

        for trade in trades:
            try:
                # Calculate all metrics
                metrics = self.calculate_trade_metrics(trade)

                # Make rescue decision
                should_rescue, reason, confidence = self.should_rescue_trade(metrics)

                if should_rescue:
                    # Calculate rescue volume
                    volume = self.calculate_rescue_volume(metrics)

                    if volume > 0:
                        # Send rescue signal
                        send_dca_signal(metrics["symbol"], volume=volume)

                        # Update tracking
                        self._update_tracking(
                            metrics["deal_id"], metrics["short_symbol"]
                        )

                        # Log decision
                        self.log_decision(metrics, "rescue", reason, confidence, volume)
                        rescue_count += 1
                    else:
                        self.log_decision(metrics, "skip", "no_volume", confidence)
                        skip_count += 1
                else:
                    self.log_decision(metrics, "skip", reason, confidence)
                    skip_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing trade {trade.get('id', 'unknown')}: {e}"
                )
                continue

        logger.info(f"🎯 Rescue Summary: {rescue_count} rescued, {skip_count} skipped")

    def _update_tracking(self, deal_id: str, symbol: str):
        """Update DCA tracking log"""
        step = self._get_current_step(deal_id)
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


def run():
    """Main entry point"""
    core = SmartDCACore(config)
    core.process_trades()


if __name__ == "__main__":
    run()
