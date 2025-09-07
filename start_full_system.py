#!/usr/bin/env python3
"""
Full MarketPilot System Startup
- Fixes all dependencies
- Starts all services properly
- End-to-end trading system
"""

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FullSystemManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.services = {}

        # Set Python path to include current directory
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = f"{self.base_dir}:{self.env.get('PYTHONPATH', '')}"

        # Ensure we're in the right directory
        os.chdir(self.base_dir)

    def check_dependencies(self):
        """Check and install missing dependencies"""
        logger.info("🔍 Checking dependencies...")

        # Check if Redis is running
        try:
            result = subprocess.run(
                ["redis-cli", "ping"], capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error("❌ Redis is not running. Starting Redis...")
                subprocess.run(
                    ["sudo", "systemctl", "start", "redis-server"], check=True
                )
                time.sleep(2)
        except Exception as e:
            logger.error(f"❌ Redis check failed: {e}")

        # Check if PostgreSQL is running
        try:
            result = subprocess.run(["pg_isready"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ PostgreSQL is not running. Starting PostgreSQL...")
                subprocess.run(["sudo", "systemctl", "start", "postgresql"], check=True)
                time.sleep(3)
        except Exception as e:
            logger.error(f"❌ PostgreSQL check failed: {e}")

        logger.info("✅ Dependencies checked")

    def create_missing_modules(self):
        """Create any missing module files"""
        logger.info("🔧 Creating missing modules...")

        # Create __init__.py files for proper Python packages
        init_files = [
            "config/__init__.py",
            "utils/__init__.py",
            "dca/__init__.py",
            "indicators/__init__.py",
            "ml/__init__.py",
            "core/__init__.py",
        ]

        for init_file in init_files:
            init_path = self.base_dir / init_file
            if not init_path.exists():
                init_path.write_text("")
                logger.info(f"✅ Created {init_file}")

    def start_service(self, name, command, working_dir=None):
        """Start a service with proper environment"""
        try:
            if working_dir is None:
                working_dir = self.base_dir

            logger.info(f"🚀 Starting {name}...")
            process = subprocess.Popen(
                command,
                cwd=working_dir,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

            self.services[name] = {
                "process": process,
                "command": command,
                "pid": process.pid,
            }

            logger.info(f"✅ {name} started with PID {process.pid}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return False

    def test_imports(self):
        """Test if we can import the required modules"""
        logger.info("🔍 Testing imports...")

        test_commands = [
            'python3 -c "import sys; sys.path.insert(0, "."); from config.unified_config_manager import get_path; print("✅ config import works")"',
            'python3 -c "import sys; sys.path.insert(0, "."); from utils.redis_manager import get_redis_manager; print("✅ utils import works")"',
            'python3 -c "import sys; sys.path.insert(0, "."); from dca.smart_dca_signal import SmartDCASignal; print("✅ dca import works")"',
            'python3 -c "import sys; sys.path.insert(0, "."); from indicators.fork_pipeline_runner import run_unified_pipeline; print("✅ indicators import works")"',
            'python3 -c "import sys; sys.path.insert(0, "."); from ml.unified_ml_pipeline import UnifiedMLPipeline; print("✅ ml import works")"',
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd, shell=True, cwd=self.base_dir, capture_output=True, text=True
                )
                if result.returncode == 0:
                    logger.info(result.stdout.strip())
                else:
                    logger.error(f"❌ Import failed: {result.stderr.strip()}")
            except Exception as e:
                logger.error(f"❌ Import test failed: {e}")

    def start_full_system(self):
        """Start the complete MarketPilot system"""
        logger.info("🚀 Starting Full MarketPilot System...")

        # 1. Check dependencies
        self.check_dependencies()

        # 2. Create missing modules
        self.create_missing_modules()

        # 3. Test imports
        self.test_imports()

        # 4. Start services in order
        services_to_start = [
            {"name": "redis", "command": ["redis-server", "--daemonize", "yes"]},
            {
                "name": "postgres",
                "command": ["sudo", "systemctl", "start", "postgresql"],
            },
            {
                "name": "dashboard_backend",
                "command": ["python3", "dashboard_backend/main.py"],
            },
            {
                "name": "ml_pipeline",
                "command": ["python3", "ml/unified_ml_pipeline.py"],
            },
            {
                "name": "fork_pipeline",
                "command": ["python3", "indicators/fork_pipeline_runner.py"],
            },
            {"name": "dca_service", "command": ["python3", "dca/smart_dca_signal.py"]},
            {
                "name": "fork_score_filter",
                "command": ["python3", "indicators/fork_score_filter.py"],
            },
        ]

        # Start services
        for service in services_to_start:
            if service["name"] in ["redis", "postgres"]:
                # System services
                try:
                    subprocess.run(service["command"], check=True)
                    logger.info(f"✅ {service['name']} started")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"❌ Failed to start {service['name']}: {e}")
            else:
                # Python services
                self.start_service(service["name"], service["command"])
                time.sleep(3)

        # 5. Start Docker services
        logger.info("🐳 Starting Docker services...")
        try:
            subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "-f",
                    "deploy/docker-compose-minimal.yml",
                    "up",
                    "-d",
                ],
                check=True,
            )
            time.sleep(5)
            subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "-f",
                    "deploy/docker-compose-dashboard.yml",
                    "up",
                    "-d",
                ],
                check=True,
            )
            logger.info("✅ Docker services started")
        except Exception as e:
            logger.error(f"❌ Docker services failed: {e}")

        # 6. Show status
        self.show_status()

        logger.info("🎉 Full MarketPilot System Started!")
        logger.info("🌐 Frontend: http://155.138.202.35:3000")
        logger.info("🔧 Backend: http://155.138.202.35:8000")

    def show_status(self):
        """Show status of all services"""
        logger.info("📊 System Status:")

        # Check Python services
        for name, info in self.services.items():
            process = info["process"]
            if process.poll() is None:
                logger.info(f"  ✅ {name} (PID: {info['pid']}) - Running")
            else:
                logger.info(f"  ❌ {name} (PID: {info['pid']}) - Stopped")

        # Check ports
        try:
            result = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True)
            ports = ["3000", "8000", "6379", "5432"]
            for port in ports:
                if f":{port}" in result.stdout:
                    logger.info(f"  ✅ Port {port} - Listening")
                else:
                    logger.info(f"  ❌ Port {port} - Not listening")
        except Exception as e:
            logger.error(f"❌ Port check failed: {e}")

    def run_forever(self):
        """Keep the system running"""
        try:
            logger.info(
                "🔄 System manager running... Press Ctrl+C to stop all services"
            )
            while True:
                time.sleep(10)
                # Check if any services died and restart them
                for name, info in list(self.services.items()):
                    if info["process"].poll() is not None:
                        logger.warning(f"⚠️  {name} died, restarting...")
                        self.start_service(name, info["command"])
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
            self.stop_all()

    def stop_all(self):
        """Stop all services"""
        logger.info("🛑 Stopping all services...")

        # Stop Python services
        for name, info in self.services.items():
            try:
                process = info["process"]
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                logger.info(f"✅ {name} stopped")
            except Exception as e:
                logger.error(f"❌ Failed to stop {name}: {e}")

        # Stop Docker services
        try:
            subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "-f",
                    "deploy/docker-compose-dashboard.yml",
                    "down",
                ]
            )
            subprocess.run(
                [
                    "sudo",
                    "docker-compose",
                    "-f",
                    "deploy/docker-compose-minimal.yml",
                    "down",
                ]
            )
            logger.info("✅ Docker services stopped")
        except Exception as e:
            logger.error(f"❌ Docker stop failed: {e}")


def main():
    manager = FullSystemManager()

    try:
        manager.start_full_system()
        manager.run_forever()
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        manager.stop_all()


if __name__ == "__main__":
    main()
