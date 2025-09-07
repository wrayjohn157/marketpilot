#!/usr/bin/env python3

import logging
import os
import subprocess
import sys
import time

"""
Start Trading Services with proper PYTHONPATH
"""

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def start_trading_services():
    """Start all trading services with proper environment"""

    # Set PYTHONPATH
    project_root = os.path.abspath(os.path.dirname(__file__))
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{project_root}:{env.get('PYTHONPATH', '')}"

    # Change to project directory
    os.chdir(project_root)

    logger.info("🚀 Starting Trading Services...")

    # Services to start
    services = [
        {
            "name": "fork_pipeline",
            "command": ["python3", "indicators/fork_pipeline_runner.py"],
            "description": "Fork scoring and detection",
        },
        {
            "name": "dca_service",
            "command": ["python3", "dca/smart_dca_signal.py"],
            "description": "Smart DCA signal management",
        },
        {
            "name": "ml_pipeline",
            "command": ["python3", "ml/unified_ml_pipeline.py"],
            "description": "ML prediction pipeline",
        },
    ]

    running_processes = {}

    for service in services:
        try:
            logger.info(f"🚀 Starting {service['name']} - {service['description']}")
            process = subprocess.Popen(
                service["command"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )
            running_processes[service["name"]] = process
            logger.info(f"✅ {service['name']} started with PID {process.pid}")
            time.sleep(2)  # Give each service time to start

        except Exception as e:
            logger.error(f"❌ Failed to start {service['name']}: {e}")

    # Show status
    logger.info("📊 Trading Services Status:")
    for name, process in running_processes.items():
        if process.poll() is None:
            logger.info(f"  ✅ {name} (PID: {process.pid}) - Running")
        else:
            logger.info(f"  ❌ {name} (PID: {process.pid}) - Stopped")

    logger.info("🎉 Trading services started!")
    logger.info("🌐 Backend API: http://155.138.202.35:8000")
    logger.info("📊 3Commas Integration: Active")

    return running_processes


if __name__ == "__main__":
    start_trading_services()
