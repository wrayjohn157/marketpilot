#!/usr/bin/env python3
"""
Simple service manager for MarketPilot supporting tech filters
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


class ServiceManager:
    def __init__(self):
        self.services = {}
        self.base_dir = Path(__file__).parent

    def start_service(self, name, command, working_dir=None):
        """Start a service and track its PID"""
        try:
            if working_dir is None:
                working_dir = self.base_dir

            print(f"🚀 Starting {name}...")
            process = subprocess.Popen(
                command,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

            self.services[name] = {
                "process": process,
                "command": command,
                "pid": process.pid,
            }

            print(f"✅ {name} started with PID {process.pid}")
            return True

        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return False

    def stop_service(self, name):
        """Stop a service by name"""
        if name in self.services:
            try:
                process = self.services[name]["process"]
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
                del self.services[name]
                return True
            except Exception as e:
                print(f"❌ Failed to stop {name}: {e}")
                return False
        return False

    def stop_all(self):
        """Stop all services"""
        print("🛑 Stopping all services...")
        for name in list(self.services.keys()):
            self.stop_service(name)

    def status(self):
        """Show status of all services"""
        print("📊 Service Status:")
        for name, info in self.services.items():
            process = info["process"]
            if process.poll() is None:
                print(f"  ✅ {name} (PID: {info['pid']}) - Running")
            else:
                print(f"  ❌ {name} (PID: {info['pid']}) - Stopped")

    def run_forever(self):
        """Run services and keep them alive"""
        try:
            print("🔄 Service manager running... Press Ctrl+C to stop all services")
            while True:
                time.sleep(1)
                # Check if any services died
                for name, info in list(self.services.items()):
                    if info["process"].poll() is not None:
                        print(f"⚠️  {name} died, restarting...")
                        self.stop_service(name)
                        # Restart logic could go here
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.stop_all()


def main():
    manager = ServiceManager()

    # Define services to start
    services_to_start = [
        {"name": "ml_pipeline", "command": ["python3", "ml/unified_ml_pipeline.py"]},
        {
            "name": "dashboard_backend",
            "command": ["python3", "dashboard_backend/main.py"],
        },
        {
            "name": "simple_trade_sender",
            "command": ["python3", "simple_trade_sender.py"],
        },
    ]

    # Start services
    for service in services_to_start:
        manager.start_service(service["name"], service["command"])
        time.sleep(2)  # Give each service time to start

    # Show status
    manager.status()

    # Keep running
    manager.run_forever()


if __name__ == "__main__":
    main()
