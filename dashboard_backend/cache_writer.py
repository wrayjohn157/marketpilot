#!/usr/bin/env python3
# /market7/dashboard_backend/cache_writer.py

import os
import json
from datetime import datetime
from pathlib import Path

from unified_fork_metrics import get_fork_trade_metrics
from config.config_loader import PATHS

OUTPUT_PATH = PATHS["base"] / "dashboard_backend" / "cache" / "fork_metrics.json"

def main():
    data = get_fork_trade_metrics()
    data["last_updated"] = datetime.utcnow().isoformat()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Cached fork metrics to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
