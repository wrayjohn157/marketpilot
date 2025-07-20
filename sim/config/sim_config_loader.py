import yaml
from pathlib import Path


def load_sim_config(filename: str) -> dict:
    base_path = Path(__file__).resolve().parent.parent
    config_path = base_path / "config" / filename
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Ensure 'timeframe' is always present, with a default fallback
    if "timeframe" not in config:
        config["timeframe"] = "15m"

    return config
