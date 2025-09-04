from typing import Dict, List, Optional, Any, Union, Tuple

import yaml

# /market7/strat/utils/strategy_loader.py

from
 pathlib import Path

# Point to /market7/strat/strategies
STRATEGY_PATH = Path(__file__).resolve().parents[1] / "strategies"

def load_strategy_config(name: str) -> dict:
    """
    Load a strategy YAML file from /market7/strat/strategies/.

    Args:
        name (str): Strategy name (without .yaml)

    Returns:
        dict: Parsed YAML config
    """
    path = STRATEGY_PATH / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Strategy config not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)
