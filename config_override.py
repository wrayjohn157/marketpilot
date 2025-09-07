#!/usr/bin/env python3
"""
Config override for MarketPilot
Sets the correct paths for the current environment
"""

import os
import sys
from pathlib import Path

# Set the base path to the current directory
BASE_PATH = Path(__file__).parent

# Override the config paths
os.environ["MARKET7_BASE_PATH"] = str(BASE_PATH)
os.environ["MARKET7_ENV"] = "production"

# Add the current directory to Python path
sys.path.insert(0, str(BASE_PATH))

# Create required directories
required_dirs = [
    BASE_PATH / "data" / "snapshots",
    BASE_PATH / "output" / "fork_history",
    BASE_PATH / "dashboard_backend" / "btc_logs",
    BASE_PATH / "live" / "logs",
    BASE_PATH / "live" / "models",
    BASE_PATH / "dashboard_backend" / "cache",
]

for dir_path in required_dirs:
    dir_path.mkdir(parents=True, exist_ok=True)

print(f"✅ Config override applied. Base path: {BASE_PATH}")
