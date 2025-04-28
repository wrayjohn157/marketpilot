# /market7/config/config_loader.py

import yaml
from pathlib import Path

# === Load paths_config.yaml ===
CONFIG_PATH = Path(__file__).resolve().parent / "paths_config.yaml"

with open(CONFIG_PATH, "r") as f:
    raw_config = yaml.safe_load(f)

# === Dynamically map all fields ===
PATHS = {}
for key, value in raw_config.items():
    normalized_key = key.replace("_path", "").replace("_base", "")
    PATHS[normalized_key] = Path(value)

# === Safety check (required critical paths) ===
required_keys = {"base", "snapshots", "fork_history", "btc_logs", "live_logs", "models"}
missing = required_keys - PATHS.keys()
if missing:
    raise ValueError(f"[ERROR] Missing required path(s) in paths_config.yaml: {missing}")
