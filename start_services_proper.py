#!/usr/bin/env python3

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

"""
Proper service manager for MarketPilot with correct Python path
"""


class ProperServiceManager:
    def __init__(self):
        self.services = {}
        self.base_dir = Path(__file__).parent

        # Set Python path to include current directory
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = f"{self.base_dir}:{self.env.get('PYTHONPATH', '')}"

    def start_service(self, name, command, working_dir=None):
        """Start a service with proper environment"""
        try:
            if working_dir is None:
                working_dir = self.base_dir

            print(f"🚀 Starting {name}...")
            process = subprocess.Popen(
                command,
                cwd=working_dir,
                env=self.env,  # Use our environment with PYTHONPATH
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

    def test_imports(self):
        """Test if we can import the required modules"""
        print("🔍 Testing imports...")
        try:
            # Test config import
            result = subprocess.run(
                [
                    "python3",
                    "-c",
                    'import sys; sys.path.insert(0, "."); from config.unified_config_manager import get_path; print("✅ config import works")',
                ],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("✅ Config module import works")
            else:
                print(f"❌ Config import failed: {result.stderr}")

            # Test utils import
            result = subprocess.run(
                [
                    "python3",
                    "-c",
                    'import sys; sys.path.insert(0, "."); from utils.redis_manager import get_redis_manager; print("✅ utils import works")',
                ],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("✅ Utils module import works")
            else:
                print(f"❌ Utils import failed: {result.stderr}")

        except Exception as e:
            print(f"❌ Import test failed: {e}")

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
    manager = ProperServiceManager()

    # Test imports first
    manager.test_imports()

    # Define services to start
    services_to_start = [
        {
            "name": "dashboard_backend",
            "command": ["python3", "dashboard_backend/main.py"],
        },
        {"name": "ml_pipeline", "command": ["python3", "ml/unified_ml_pipeline.py"]},
        {
            "name": "fork_pipeline",
            "command": ["python3", "indicators/fork_pipeline_runner.py"],
        },
        {"name": "dca_service", "command": ["python3", "dca/smart_dca_signal.py"]},
    ]

    # Start services
    for service in services_to_start:
        manager.start_service(service["name"], service["command"])
        time.sleep(3)  # Give each service time to start

    # Show status
    manager.status()

    # Keep running
    manager.run_forever()


if __name__ == "__main__":
    main()
