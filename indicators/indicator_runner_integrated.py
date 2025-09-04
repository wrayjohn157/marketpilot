#!/usr/bin/env python3
"""
Integrated Indicator Runner - Uses Unified Indicator System
Replaces old fragmented indicator approach with new unified system
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.unified_config_manager import get_config, get_path
from utils.redis_manager import get_redis_manager
from utils.unified_indicator_system import IndicatorConfig, UnifiedIndicatorManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class IntegratedIndicatorManager:
    """Integrated Indicator Manager using Unified Indicator System"""

    def __init__(self):
        self.indicator_manager = None
        self.redis_manager = get_redis_manager()
        self.config = None
        self._load_config()
        self._initialize_indicator_manager()

    def _load_config(self):
        """Load indicator configuration"""
        try:
            config_data = get_config("unified_pipeline_config")
            self.config = IndicatorConfig(
                symbols=config_data.get("symbols", ["BTCUSDT", "ETHUSDT"]),
                timeframes=config_data.get("timeframes", ["1h", "15m"]),
                indicators=config_data.get("indicators", ["rsi", "macd", "adx", "ema"]),
                cache_ttl=config_data.get("cache_ttl", 3600),
            )
            logger.info("Indicator configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load indicator configuration: {e}")
            # Use default config
            self.config = IndicatorConfig()

    def _initialize_indicator_manager(self):
        """Initialize the Unified Indicator Manager"""
        try:
            self.indicator_manager = UnifiedIndicatorManager(self.config)
            logger.info("Unified Indicator Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Indicator Manager: {e}")
            raise

    def calculate_indicators_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Calculate indicators for a specific symbol"""
        try:
            logger.info(f"Calculating indicators for {symbol}")

            results = {
                "symbol": symbol,
                "timestamp": int(datetime.utcnow().timestamp()),
                "indicators": {},
                "errors": [],
            }

            # Calculate indicators for each timeframe
            for timeframe in self.config.timeframes:
                try:
                    # Get indicators for this timeframe
                    indicators = self.indicator_manager.calculate_indicators(
                        symbol=symbol, timeframe=timeframe
                    )

                    if indicators:
                        results["indicators"][timeframe] = indicators
                        logger.debug(f"✅ {symbol} {timeframe} indicators calculated")
                    else:
                        logger.warning(
                            f"⚠️ No indicators calculated for {symbol} {timeframe}"
                        )
                        results["errors"].append(f"No indicators for {timeframe}")

                except Exception as e:
                    logger.error(
                        f"Failed to calculate {symbol} {timeframe} indicators: {e}"
                    )
                    results["errors"].append(f"{timeframe}: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Failed to calculate indicators for {symbol}: {e}")
            return {
                "symbol": symbol,
                "timestamp": int(datetime.utcnow().timestamp()),
                "indicators": {},
                "errors": [str(e)],
            }

    def calculate_all_indicators(self) -> Dict[str, Any]:
        """Calculate indicators for all configured symbols"""
        logger.info("🚀 Starting Integrated Indicator Calculation")
        logger.info("=" * 50)

        try:
            results = {
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "symbols": {},
                "errors": [],
            }

            for symbol in self.config.symbols:
                try:
                    # Calculate indicators for symbol
                    symbol_results = self.calculate_indicators_for_symbol(symbol)
                    results["symbols"][symbol] = symbol_results
                    results["processed"] += 1

                    if symbol_results["indicators"]:
                        results["successful"] += 1
                        logger.info(f"✅ {symbol} indicators calculated successfully")
                    else:
                        results["failed"] += 1
                        logger.warning(f"⚠️ {symbol} indicators calculation failed")

                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{symbol}: {str(e)}")
                    logger.error(f"❌ {symbol} indicators calculation failed: {e}")
                    continue

            # Log results
            logger.info(f"✅ Indicator Calculation Complete:")
            logger.info(f"   Processed: {results['processed']}")
            logger.info(f"   Successful: {results['successful']}")
            logger.info(f"   Failed: {results['failed']}")
            logger.info(f"   Errors: {len(results['errors'])}")

            # Save results
            self._save_results(results)

            return results

        except Exception as e:
            logger.error(f"Indicator calculation failed: {e}")
            raise

    def get_indicator_data(
        self, symbol: str, timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Get indicator data for a symbol and timeframe"""
        try:
            # Try to get from cache first
            cached_data = self.redis_manager.get_indicators(symbol, timeframe)
            if cached_data:
                logger.debug(f"Retrieved cached indicators for {symbol} {timeframe}")
                return cached_data

            # Calculate fresh indicators
            indicators = self.indicator_manager.calculate_indicators(symbol, timeframe)
            if indicators:
                # Cache the results
                self.redis_manager.store_indicators(symbol, timeframe, indicators)
                logger.debug(
                    f"Calculated and cached indicators for {symbol} {timeframe}"
                )
                return indicators

            return None

        except Exception as e:
            logger.error(f"Failed to get indicator data for {symbol} {timeframe}: {e}")
            return None

    def validate_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Validate indicator data quality"""
        try:
            validation_result = self.indicator_manager.validate_indicators(indicators)

            return {
                "valid": validation_result.valid,
                "confidence": validation_result.confidence,
                "issues": validation_result.issues,
                "quality_score": validation_result.quality_score,
            }

        except Exception as e:
            logger.error(f"Failed to validate indicators: {e}")
            return {
                "valid": False,
                "confidence": 0.0,
                "issues": [str(e)],
                "quality_score": 0.0,
            }

    def run_indicator_cycle(self) -> Dict[str, Any]:
        """Run a complete indicator calculation cycle"""
        logger.info("🚀 Starting Indicator Cycle")
        logger.info("=" * 50)

        try:
            # Calculate all indicators
            results = self.calculate_all_indicators()

            # Update Redis counters
            self.redis_manager.set_counter(
                "indicators_calculated", results["successful"]
            )
            self.redis_manager.set_counter(
                "indicators_timestamp", int(datetime.utcnow().timestamp())
            )

            logger.info("🎉 Indicator Cycle complete")
            return results

        except Exception as e:
            logger.error(f"Indicator cycle failed: {e}")
            raise

    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save indicator results to file"""
        try:
            results_file = (
                get_path("snapshots")
                / f"indicators_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            results_file.parent.mkdir(parents=True, exist_ok=True)

            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)

            logger.info(f"Indicator results saved to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save indicator results: {e}")


def main():
    """Main function - run the integrated indicator system"""
    try:
        # Initialize indicator manager
        indicator_manager = IntegratedIndicatorManager()

        # Run indicator cycle
        results = indicator_manager.run_indicator_cycle()

        logger.info("🎉 Integrated Indicator System complete")
        return results

    except Exception as e:
        logger.error(f"Integrated Indicator System failed: {e}")
        raise


if __name__ == "__main__":
    main()
