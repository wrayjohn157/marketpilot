#!/usr/bin/env python3
"""
Standalone Service Runner - Minimal systemd dependency
Runs all services in a single process with proper coordination
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from config.unified_config_manager import get_config
from utils.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/standalone_runner.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class StandaloneServiceRunner:
    """Runs all services in a single process with minimal systemd dependency"""

    def __init__(self):
        self.running = True
        self.services = {}
        self.redis_manager = get_redis_manager()
        self.config = self._load_config()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self) -> Dict:
        """Load configuration"""
        return {
            "indicator_interval": 60,  # seconds
            "dca_interval": 30,  # seconds
            "fork_interval": 120,  # seconds
            "ml_interval": 300,  # seconds
            "max_retries": 3,
            "retry_delay": 5,
        }

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def run_indicator_service(self):
        """Run indicator calculation service"""
        logger.info("🚀 Starting Indicator Service")

        while self.running:
            try:
                # Import and run indicator calculation
                from indicators.indicator_runner_integrated import (
                    IntegratedIndicatorManager,
                )

                indicator_manager = IntegratedIndicatorManager()
                results = indicator_manager.run_indicator_cycle()

                logger.info(
                    f"✅ Indicators calculated: {results.get('successful', 0)} symbols"
                )

                # Update Redis with timestamp
                self.redis_manager.set_counter(
                    "indicators_last_run", int(datetime.now(datetime.UTC).timestamp())
                )

            except Exception as e:
                logger.error(f"❌ Indicator service error: {e}")

            # Wait for next cycle
            await asyncio.sleep(self.config["indicator_interval"])

    async def run_dca_service(self):
        """Run DCA decision service"""
        logger.info("🚀 Starting DCA Service")

        while self.running:
            try:
                # Import and run DCA processing
                from dca.smart_dca_core import SmartDCACore

                # Load DCA config
                dca_config = get_config("dca")
                dca_core = SmartDCACore(dca_config)
                dca_core.process_trades()

                logger.info("✅ DCA cycle completed")

                # Update Redis with timestamp
                self.redis_manager.set_counter(
                    "dca_last_run", int(datetime.now(datetime.UTC).timestamp())
                )

            except Exception as e:
                logger.error(f"❌ DCA service error: {e}")

            # Wait for next cycle
            await asyncio.sleep(self.config["dca_interval"])

    async def run_fork_service(self):
        """Run fork detection service"""
        logger.info("🚀 Starting Fork Service")

        while self.running:
            try:
                # Import and run fork detection
                from fork.fork_runner import main as run_fork_detection

                run_fork_detection()
                logger.info("✅ Fork detection cycle completed")

                # Update Redis with timestamp
                self.redis_manager.set_counter(
                    "fork_last_run", int(datetime.now(datetime.UTC).timestamp())
                )

            except Exception as e:
                logger.error(f"❌ Fork service error: {e}")

            # Wait for next cycle
            await asyncio.sleep(self.config["fork_interval"])

    async def run_ml_service(self):
        """Run ML inference service"""
        logger.info("🚀 Starting ML Service")

        while self.running:
            try:
                # Import and run ML inference
                from ml.unified_ml_pipeline import UnifiedMLPipeline

                ml_pipeline = UnifiedMLPipeline()
                results = await ml_pipeline.run_inference_cycle()

                logger.info(f"✅ ML inference completed: {results}")

                # Update Redis with timestamp
                self.redis_manager.set_counter(
                    "ml_last_run", int(datetime.now(datetime.UTC).timestamp())
                )

            except Exception as e:
                logger.error(f"❌ ML service error: {e}")

            # Wait for next cycle
            await asyncio.sleep(self.config["ml_interval"])

    async def run_health_monitor(self):
        """Monitor service health and restart if needed"""
        logger.info("🚀 Starting Health Monitor")

        while self.running:
            try:
                # Check Redis connectivity
                if not self.redis_manager.ping():
                    logger.warning("⚠️ Redis connection lost, attempting reconnect...")
                    self.redis_manager = get_redis_manager()

                # Log service status
                status = {
                    "indicators": self.redis_manager.get_counter("indicators_last_run"),
                    "dca": self.redis_manager.get_counter("dca_last_run"),
                    "fork": self.redis_manager.get_counter("fork_last_run"),
                    "ml": self.redis_manager.get_counter("ml_last_run"),
                }

                logger.info(f"📊 Service Status: {status}")

            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")

            # Check every 30 seconds
            await asyncio.sleep(30)

    async def run_all_services(self):
        """Run all services concurrently"""
        logger.info("🚀 Starting MarketPilot Standalone Runner")
        logger.info("=" * 60)

        # Create tasks for all services
        tasks = [
            asyncio.create_task(self.run_indicator_service()),
            asyncio.create_task(self.run_dca_service()),
            asyncio.create_task(self.run_fork_service()),
            asyncio.create_task(self.run_ml_service()),
            asyncio.create_task(self.run_health_monitor()),
        ]

        try:
            # Wait for all tasks to complete (they run indefinitely)
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ Service runner error: {e}")
        finally:
            # Cancel all tasks
            for task in tasks:
                task.cancel()

            logger.info("🛑 All services stopped")


def main():
    """Main entry point"""
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Create and run service runner
    runner = StandaloneServiceRunner()

    try:
        asyncio.run(runner.run_all_services())
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
