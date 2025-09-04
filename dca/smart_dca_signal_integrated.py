#!/usr/bin/env python3
"""
Integrated Smart DCA Signal - Uses Smart DCA Core
Replaces old fragmented DCA system with new unified approach
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from config.unified_config_manager import get_path, get_config
from dca.smart_dca_core import SmartDCACore, DCAConfig
from utils.credential_manager import get_3commas_credentials
from utils.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class IntegratedDCAManager:
    """Integrated DCA Manager using Smart DCA Core"""
    
    def __init__(self):
        self.dca_core = None
        self.redis_manager = get_redis_manager()
        self.config = None
        self._load_config()
        self._initialize_dca_core()
    
    def _load_config(self):
        """Load DCA configuration"""
        try:
            config_data = get_config("dca_config")
            self.config = DCAConfig(
                min_confidence=config_data.get("min_confidence", 0.7),
                max_dca_attempts=config_data.get("max_dca_attempts", 5),
                base_volume=config_data.get("base_volume", 10.0),
                volume_multiplier=config_data.get("volume_multiplier", 1.2),
                zombie_threshold=config_data.get("zombie_threshold", 0.3),
                recovery_threshold=config_data.get("recovery_threshold", 0.6),
                btc_sentiment_weight=config_data.get("btc_sentiment_weight", 0.2)
            )
            logger.info("DCA configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load DCA configuration: {e}")
            # Use default config
            self.config = DCAConfig()
    
    def _initialize_dca_core(self):
        """Initialize the Smart DCA Core"""
        try:
            self.dca_core = SmartDCACore(self.config)
            logger.info("Smart DCA Core initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DCA Core: {e}")
            raise
    
    def get_live_trades(self) -> List[Dict[str, Any]]:
        """Get live trades from 3Commas"""
        try:
            credentials = get_3commas_credentials()
            # This would need to be implemented based on your 3Commas integration
            # For now, return empty list
            logger.info("Retrieved live trades from 3Commas")
            return []
        except Exception as e:
            logger.error(f"Failed to get live trades: {e}")
            return []
    
    def process_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single trade through the DCA system"""
        try:
            symbol = trade.get("symbol", "")
            current_price = trade.get("current_price", 0.0)
            position_size = trade.get("position_size", 0.0)
            avg_price = trade.get("avg_price", 0.0)
            
            logger.info(f"Processing trade: {symbol} | Price: {current_price} | Position: {position_size}")
            
            # Get current indicators
            indicators = self._get_current_indicators(symbol)
            
            # Get BTC sentiment
            btc_sentiment = self._get_btc_sentiment()
            
            # Process through Smart DCA Core
            decision = self.dca_core.should_dca(
                symbol=symbol,
                current_price=current_price,
                position_size=position_size,
                avg_price=avg_price,
                indicators=indicators,
                btc_sentiment=btc_sentiment
            )
            
            result = {
                "symbol": symbol,
                "should_dca": decision.should_dca,
                "confidence": decision.confidence,
                "volume": decision.volume,
                "reason": decision.reason,
                "timestamp": int(datetime.utcnow().timestamp())
            }
            
            if decision.should_dca:
                logger.info(f"✅ DCA recommended for {symbol}: {decision.volume} @ {decision.confidence:.2f} confidence")
            else:
                logger.info(f"❌ DCA not recommended for {symbol}: {decision.reason}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process trade {trade.get('symbol', 'unknown')}: {e}")
            return {
                "symbol": trade.get("symbol", "unknown"),
                "should_dca": False,
                "confidence": 0.0,
                "volume": 0.0,
                "reason": f"Error: {e}",
                "timestamp": int(datetime.utcnow().timestamp())
            }
    
    def _get_current_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get current indicators for symbol"""
        try:
            # Get indicators from Redis
            indicators_1h = self.redis_manager.get_indicators(symbol, "1h")
            indicators_15m = self.redis_manager.get_indicators(symbol, "15m")
            
            # Combine indicators
            combined = {}
            if indicators_1h:
                combined.update(indicators_1h)
            if indicators_15m:
                combined.update(indicators_15m)
            
            return combined
        except Exception as e:
            logger.warning(f"Failed to get indicators for {symbol}: {e}")
            return {}
    
    def _get_btc_sentiment(self) -> str:
        """Get current BTC sentiment"""
        try:
            btc_condition = self.redis_manager.get_cache("btc_condition")
            return btc_condition if btc_condition else "neutral"
        except Exception as e:
            logger.warning(f"Failed to get BTC sentiment: {e}")
            return "neutral"
    
    def execute_dca_signal(self, trade: Dict[str, Any], decision: Dict[str, Any]) -> bool:
        """Execute DCA signal if recommended"""
        try:
            if not decision.get("should_dca", False):
                return False
            
            symbol = trade.get("symbol", "")
            volume = decision.get("volume", 0.0)
            
            # This would integrate with your 3Commas API
            # For now, just log the action
            logger.info(f"Executing DCA signal: {symbol} | Volume: {volume}")
            
            # Update Redis counters
            self.redis_manager.increment_counter("dca_signals_sent")
            self.redis_manager.set_cache(f"last_dca_{symbol}", decision)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute DCA signal: {e}")
            return False
    
    def run_dca_cycle(self) -> Dict[str, Any]:
        """Run a complete DCA cycle"""
        logger.info("🚀 Starting Integrated DCA Cycle")
        logger.info("=" * 50)
        
        try:
            # Get live trades
            trades = self.get_live_trades()
            logger.info(f"Processing {len(trades)} live trades")
            
            results = {
                "processed": 0,
                "dca_recommended": 0,
                "dca_executed": 0,
                "errors": 0,
                "trades": []
            }
            
            for trade in trades:
                try:
                    # Process trade
                    decision = self.process_trade(trade)
                    results["trades"].append(decision)
                    results["processed"] += 1
                    
                    if decision.get("should_dca", False):
                        results["dca_recommended"] += 1
                        
                        # Execute DCA signal
                        if self.execute_dca_signal(trade, decision):
                            results["dca_executed"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing trade {trade.get('symbol', 'unknown')}: {e}")
                    results["errors"] += 1
                    continue
            
            # Log results
            logger.info(f"✅ DCA Cycle Complete:")
            logger.info(f"   Processed: {results['processed']}")
            logger.info(f"   DCA Recommended: {results['dca_recommended']}")
            logger.info(f"   DCA Executed: {results['dca_executed']}")
            logger.info(f"   Errors: {results['errors']}")
            
            # Save results to file
            self._save_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"DCA cycle failed: {e}")
            raise
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save DCA results to file"""
        try:
            results_file = get_path("dca_log_base") / f"dca_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results saved to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    """Main function - run the integrated DCA system"""
    try:
        # Initialize DCA manager
        dca_manager = IntegratedDCAManager()
        
        # Run DCA cycle
        results = dca_manager.run_dca_cycle()
        
        logger.info("🎉 Integrated DCA System complete")
        return results
        
    except Exception as e:
        logger.error(f"Integrated DCA System failed: {e}")
        raise

if __name__ == "__main__":
    main()