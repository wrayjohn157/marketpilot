# /market7/config/config_loader.py

import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "paths_config.yaml"

with open(CONFIG_PATH, "r") as f:
    raw_config = yaml.safe_load(f)

PATHS = {
    "base": Path(raw_config["base_path"]),
    "snapshots": Path(raw_config["snapshots_path"]),
    "fork_history": Path(raw_config["fork_history_path"]),
    "btc_logs": Path(raw_config["btc_logs_path"]),
    "live_logs": Path(raw_config["live_logs_path"]),
    "models": Path(raw_config["models_path"]),
    "paper_cred": Path(raw_config["paper_cred_path"]),
    "tv_history": Path(raw_config["tv_history_path"]),
    "final_fork_rrr_trades": Path(raw_config["final_fork_rrr_trades"]),
    "fork_tv_adjusted": Path(raw_config["fork_tv_adjusted"]),
    "filtered_pairs": Path(raw_config["filtered_pairs_path"]),
}

# === Optional safety validation ===
expected_keys = {
    "base", "snapshots", "fork_history", "btc_logs", "live_logs", "models",
    "paper_cred", "tv_history", "final_fork_rrr_trades", "fork_tv_adjusted", "filtered_pairs"
}
missing_keys = expected_keys - PATHS.keys()
if missing_keys:
    raise ValueError(f"Missing config path(s) in paths_config.yaml: {missing_keys}")
