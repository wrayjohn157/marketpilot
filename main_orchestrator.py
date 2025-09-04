#!/usr/bin/env python3
"""
Main Orchestrator - Coordinates All Integrated Systems
Unified entry point for the entire trading system using new integrated components
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.unified_config_manager import get_config, get_path
from dca.smart_dca_signal_integrated import IntegratedDCAManager
from indicators.fork_pipeline_runner_integrated import run_unified_pipeline
from indicators.indicator_runner_integrated import IntegratedIndicatorManager
from ml.ml_pipeline_runner_integrated import IntegratedMLManager
from utils.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MainOrchestrator:
    """Main orchestrator for all integrated systems"""

    def __init__(self):
        self.redis_manager = get_redis_manager()
        self.config = None
        self._load_config()

        # Initialize integrated managers
        self.dca_manager = None
        self.ml_manager = None
        self.indicator_manager = None

        self._initialize_managers()

    def _load_config(self):
        """Load main configuration"""
        try:
            self.config = {
                "run_indicators": True,
                "run_ml_training": False,  # Set to True for training mode
                "run_ml_inference": True,
                "run_fork_pipeline": True,
                "run_dca_cycle": True,
                "parallel_execution": True,
                "max_concurrent_tasks": 3,
            }
            logger.info("Main configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load main configuration: {e}")
            self.config = {}

    def _initialize_managers(self):
        """Initialize all integrated managers"""
        try:
            # Initialize managers only if needed
            if self.config.get("run_dca_cycle", False):
                self.dca_manager = IntegratedDCAManager()
                logger.info("DCA Manager initialized")

            if self.config.get("run_ml_training", False) or self.config.get(
                "run_ml_inference", False
            ):
                self.ml_manager = IntegratedMLManager()
                logger.info("ML Manager initialized")

            if self.config.get("run_indicators", False):
                self.indicator_manager = IntegratedIndicatorManager()
                logger.info("Indicator Manager initialized")

            logger.info("All managers initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize managers: {e}")
            raise

    async def run_indicator_cycle(self) -> Dict[str, Any]:
        """Run indicator calculation cycle"""
        try:
            logger.info("🔄 Starting Indicator Cycle")
            if self.indicator_manager:
                results = self.indicator_manager.run_indicator_cycle()
                logger.info("✅ Indicator Cycle complete")
                return results
            else:
                logger.warning("Indicator Manager not initialized")
                return {"error": "Indicator Manager not initialized"}
        except Exception as e:
            logger.error(f"Indicator cycle failed: {e}")
            return {"error": str(e)}

    async def run_ml_training(self) -> Dict[str, Any]:
        """Run ML model training"""
        try:
            logger.info("🔄 Starting ML Training")
            if self.ml_manager:
                results = self.ml_manager.train_all_models()
                logger.info("✅ ML Training complete")
                return results
            else:
                logger.warning("ML Manager not initialized")
                return {"error": "ML Manager not initialized"}
        except Exception as e:
            logger.error(f"ML training failed: {e}")
            return {"error": str(e)}

    async def run_ml_inference(self) -> Dict[str, Any]:
        """Run ML inference cycle"""
        try:
            logger.info("🔄 Starting ML Inference")
            if self.ml_manager:
                results = self.ml_manager.run_inference_cycle()
                logger.info("✅ ML Inference complete")
                return results
            else:
                logger.warning("ML Manager not initialized")
                return {"error": "ML Manager not initialized"}
        except Exception as e:
            logger.error(f"ML inference failed: {e}")
            return {"error": str(e)}

    async def run_fork_pipeline(self) -> Dict[str, Any]:
        """Run fork pipeline"""
        try:
            logger.info("🔄 Starting Fork Pipeline")
            results = await run_unified_pipeline()
            logger.info("✅ Fork Pipeline complete")
            return results
        except Exception as e:
            logger.error(f"Fork pipeline failed: {e}")
            return {"error": str(e)}

    async def run_dca_cycle(self) -> Dict[str, Any]:
        """Run DCA cycle"""
        try:
            logger.info("🔄 Starting DCA Cycle")
            if self.dca_manager:
                results = self.dca_manager.run_dca_cycle()
                logger.info("✅ DCA Cycle complete")
                return results
            else:
                logger.warning("DCA Manager not initialized")
                return {"error": "DCA Manager not initialized"}
        except Exception as e:
            logger.error(f"DCA cycle failed: {e}")
            return {"error": str(e)}

    async def run_parallel_cycles(self) -> Dict[str, Any]:
        """Run cycles in parallel"""
        try:
            logger.info("🚀 Starting Parallel Execution")

            tasks = []

            # Add tasks based on configuration
            if self.config.get("run_indicators", False):
                tasks.append(("indicators", self.run_indicator_cycle()))

            if self.config.get("run_ml_training", False):
                tasks.append(("ml_training", self.run_ml_training()))

            if self.config.get("run_ml_inference", False):
                tasks.append(("ml_inference", self.run_ml_inference()))

            if self.config.get("run_fork_pipeline", False):
                tasks.append(("fork_pipeline", self.run_fork_pipeline()))

            if self.config.get("run_dca_cycle", False):
                tasks.append(("dca_cycle", self.run_dca_cycle()))

            # Execute tasks in parallel
            results = {}
            if tasks:
                task_names, task_coroutines = zip(*tasks)
                task_results = await asyncio.gather(
                    *task_coroutines, return_exceptions=True
                )

                for name, result in zip(task_names, task_results):
                    if isinstance(result, Exception):
                        results[name] = {"error": str(result)}
                        logger.error(f"Task {name} failed: {result}")
                    else:
                        results[name] = result
                        logger.info(f"Task {name} completed successfully")

            logger.info("✅ Parallel execution complete")
            return results

        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            return {"error": str(e)}

    async def run_sequential_cycles(self) -> Dict[str, Any]:
        """Run cycles sequentially"""
        try:
            logger.info("🚀 Starting Sequential Execution")

            results = {}

            # Run cycles in order
            if self.config.get("run_indicators", False):
                results["indicators"] = await self.run_indicator_cycle()

            if self.config.get("run_ml_training", False):
                results["ml_training"] = await self.run_ml_training()

            if self.config.get("run_ml_inference", False):
                results["ml_inference"] = await self.run_ml_inference()

            if self.config.get("run_fork_pipeline", False):
                results["fork_pipeline"] = await self.run_fork_pipeline()

            if self.config.get("run_dca_cycle", False):
                results["dca_cycle"] = await self.run_dca_cycle()

            logger.info("✅ Sequential execution complete")
            return results

        except Exception as e:
            logger.error(f"Sequential execution failed: {e}")
            return {"error": str(e)}

    async def run_main_cycle(self) -> Dict[str, Any]:
        """Run the main trading cycle"""
        logger.info("🚀 Starting Main Trading Cycle")
        logger.info("=" * 60)

        try:
            start_time = datetime.utcnow()

            # Choose execution mode
            if self.config.get("parallel_execution", True):
                results = await self.run_parallel_cycles()
            else:
                results = await self.run_sequential_cycles()

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Add metadata
            results["metadata"] = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "parallel_execution": self.config.get("parallel_execution", True),
            }

            # Update Redis counters
            self.redis_manager.set_counter("main_cycle_completed")
            self.redis_manager.set_counter(
                "main_cycle_timestamp", int(end_time.timestamp())
            )

            # Save results
            self._save_results(results)

            logger.info(f"🎉 Main Trading Cycle complete in {duration:.2f} seconds")
            return results

        except Exception as e:
            logger.error(f"Main trading cycle failed: {e}")
            raise

    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save main cycle results"""
        try:
            results_file = (
                get_path("live_logs")
                / f"main_cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            results_file.parent.mkdir(parents=True, exist_ok=True)

            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)

            logger.info(f"Main cycle results saved to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save main cycle results: {e}")


async def main():
    """Main function - run the integrated trading system"""
    try:
        # Initialize orchestrator
        orchestrator = MainOrchestrator()

        # Run main cycle
        results = await orchestrator.run_main_cycle()

        logger.info("🎉 Integrated Trading System complete")
        return results

    except Exception as e:
        logger.error(f"Integrated Trading System failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
