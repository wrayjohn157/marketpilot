#!/usr/bin/env python3

import logging
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

"""
Simple Process Manager - No systemd required
Manages all services as subprocesses with automatic restart
"""

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/simple_manager.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SimpleProcessManager:
    """Simple process manager without systemd dependency"""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True

        # Service configurations
        self.services = {
            "indicators": {
                "script": "data/rolling_indicators_standalone.py",
                "interval": 60,
                "enabled": True,
            },
            "dca": {"script": "dca/smart_dca_core.py", "interval": 30, "enabled": True},
            "fork": {"script": "fork/fork_runner.py", "interval": 120, "enabled": True},
        }

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all_services()

    def start_service(self, service_name: str) -> bool:
        """Start a single service"""
        if service_name not in self.services:
            logger.error(f"Unknown service: {service_name}")
            return False

        if not self.services[service_name]["enabled"]:
            logger.info(f"Service {service_name} is disabled")
            return False

        script_path = self.services[service_name]["script"]

        if not Path(script_path).exists():
            logger.error(f"Script not found: {script_path}")
            return False

        try:
            # Start the process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.processes[service_name] = process
            logger.info(f"✅ Started {service_name} (PID: {process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start {service_name}: {e}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a single service"""
        if service_name not in self.processes:
            logger.warning(f"Service {service_name} not running")
            return True

        try:
            process = self.processes[service_name]
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {service_name}")
                process.kill()
                process.wait()

            del self.processes[service_name]
            logger.info(f"✅ Stopped {service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop {service_name}: {e}")
            return False

    def restart_service(self, service_name: str) -> bool:
        """Restart a single service"""
        logger.info(f"Restarting {service_name}...")
        self.stop_service(service_name)
        time.sleep(2)
        return self.start_service(service_name)

    def start_all_services(self) -> bool:
        """Start all enabled services"""
        logger.info("🚀 Starting all services...")

        success = True
        for service_name in self.services:
            if not self.start_service(service_name):
                success = False

        return success

    def stop_all_services(self) -> bool:
        """Stop all services"""
        logger.info("🛑 Stopping all services...")

        success = True
        for service_name in list(self.processes.keys()):
            if not self.stop_service(service_name):
                success = False

        return success

    def check_services(self) -> Dict[str, bool]:
        """Check status of all services"""
        status = {}

        for service_name, process in self.processes.items():
            if process.poll() is None:
                status[service_name] = True  # Running
            else:
                status[service_name] = False  # Stopped
                logger.warning(f"Service {service_name} has stopped")

        return status

    def restart_failed_services(self):
        """Restart any services that have failed"""
        status = self.check_services()

        for service_name, is_running in status.items():
            if not is_running and self.services[service_name]["enabled"]:
                logger.info(f"Restarting failed service: {service_name}")
                self.start_service(service_name)

    def run(self):
        """Main run loop"""
        logger.info("🚀 Simple Process Manager starting...")

        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)

        # Start all services
        if not self.start_all_services():
            logger.error("Failed to start some services")
            return False

        logger.info("✅ All services started")

        # Main monitoring loop
        try:
            while self.running:
                # Check service health
                self.restart_failed_services()

                # Log status
                status = self.check_services()
                running_count = sum(1 for s in status.values() if s)
                total_count = len(self.services)

                logger.info(f"📊 Services running: {running_count}/{total_count}")

                # Wait before next check
                time.sleep(30)

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            self.stop_all_services()
            logger.info("✅ All services stopped")


def main():
    """Main entry point"""
    manager = SimpleProcessManager()

    try:
        manager.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
