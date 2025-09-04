"""Main DCA Engine for intelligent trading decisions."""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .snapshot_manager import SnapshotManager
from .trade_tracker import TradeTracker
from ..utils.entry_utils import (
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
from ..utils.fork_score_utils import compute_fork_score
from ..modules.fork_safu_evaluator import get_safu_score
from ..utils.btc_filter import get_btc_status
from ..modules.dca_decision_engine import should_dca
from ..utils.recovery_odds_utils import (
    get_latest_snapshot,
    predict_recovery_odds,
    SNAPSHOT_PATH,
)
from ..utils.recovery_confidence_utils import predict_confidence_score
from ..utils.tv_utils import load_tv_kicker
from ..utils.zombie_utils import is_zombie_trade
from ..utils.spend_predictor import predict_spend_volume, adjust_volume
from ..utils.trade_health_evaluator import evaluate_trade_health
from config.config_loader import PATHS

logger = logging.getLogger(__name__)


class DCAEngine:
    """Main DCA Engine for intelligent trading decisions."""
    
    def __init__(self, config_path: Path):
        """Initialize DCA Engine.
        
        Args:
            config_path: Path to DCA configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.snapshot_manager = SnapshotManager(SNAPSHOT_PATH)
        self.trade_tracker = TradeTracker(
            PATHS["base"] / "dca" / "logs" / "dca_tracking" / "dca_fired.jsonl"
        )
        
        # Load SAFU model
        from ..modules.fork_safu_evaluator import load_safu_exit_model
        self.safu_exit_model = load_safu_exit_model()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load DCA configuration from file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, IOError) as e:
            logger.error(f"Failed to load DCA config: {e}")
            return {}
    
    def detect_local_reversal(self, prices: List[float]) -> bool:
        """Detect local bottom reversal (V-shape) from price data.
        
        Args:
            prices: List of price values
            
        Returns:
            True if local reversal detected
        """
        if len(prices) < 5:
            return False
        return prices[-4] > prices[-3] > prices[-2] and prices[-2] < prices[-1]
    
    def run(self) -> None:
        """Main DCA execution loop."""
        logger.info("Starting DCA Engine...")
        
        try:
            # Get live trades
            trades = get_live_3c_trades()
            if not trades:
                logger.info("No live trades found")
                return
            
            # Process each trade
            for trade in trades:
                self._process_trade(trade)
                
        except Exception as e:
            logger.error(f"Error in DCA engine: {e}")
            raise
    
    def _process_trade(self, trade: Dict[str, Any]) -> None:
        """Process a single trade for DCA decisions.
        
        Args:
            trade: Trade data from 3Commas
        """
        try:
            symbol = trade.get("pair", "")
            deal_id = trade.get("id", 0)
            
            if not symbol or not deal_id:
                logger.warning(f"Invalid trade data: {trade}")
                return
            
            # Check if trade is zombie
            if is_zombie_trade(trade):
                logger.info(f"Skipping zombie trade: {symbol}")
                return
            
            # Get trade health
            health = evaluate_trade_health(trade)
            if health.get("should_exit", False):
                logger.info(f"Trade {symbol} marked for exit")
                return
            
            # Process DCA logic
            self._process_dca_logic(trade, symbol, deal_id)
            
        except Exception as e:
            logger.error(f"Error processing trade {trade.get('id', 'unknown')}: {e}")
    
    def _process_dca_logic(self, trade: Dict[str, Any], symbol: str, deal_id: int) -> None:
        """Process DCA logic for a trade.
        
        Args:
            trade: Trade data
            symbol: Trading symbol
            deal_id: Deal identifier
        """
        # This is a simplified version - the full logic would be much more complex
        # and would include all the original DCA decision making logic
        
        # Get latest indicators
        indicators = get_latest_indicators(symbol)
        if not indicators:
            logger.warning(f"No indicators available for {symbol}")
            return
        
        # Check if DCA should be triggered
        dca_decision = should_dca(trade, indicators, self.config)
        if not dca_decision.get("should_dca", False):
            return
        
        # Get DCA volume
        volume = dca_decision.get("volume", 0)
        step = dca_decision.get("step", 1)
        
        # Check if already fired recently
        if self.trade_tracker.was_dca_fired_recently(deal_id, step):
            logger.info(f"DCA already fired for {symbol} step {step}")
            return
        
        # Send DCA signal
        logger.info(f"Sending DCA signal for {symbol} | Volume: {volume:.2f} USDT (Step {step})")
        send_dca_signal(symbol, volume=volume)
        
        # Update tracking
        self.trade_tracker.update_dca_log(deal_id, step, symbol)