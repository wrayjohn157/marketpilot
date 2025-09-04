from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from dca_status import compute_indicators  # example: replace with your real function
import yaml

from dashboard_backend.dca.core import (
from dca_trades_api import adjust_volume  # example: replace with your real function
from dca_trades_api import should_dca  # example: replace with your real function
import argparse
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


# dashboard_backend/dca/core.py
"""
Core DCA engine functions extracted for reuse in simulation and live evaluation.
"""

from
 pathlib import Path

# These should point to the modules where your production code lives.

def load_config(path: Path = None, fallback: bool = False):
    """
    Load a DCA configuration YAML from the given path or default production path.

    If fallback is True, load the fallback default config instead.
    """
    if fallback:
        config_path = Path("/home/signal/market7/sim/config/sim_dca_config_fallback.yaml")
    elif path:
        config_path = Path(path)
    else:
        config_path = get_path("dca_config")
    with open(config_path) as f:
        return yaml.safe_load(f)

# simulate_dca.py
"""
A simple driver script to run DCA simulation using the real engine.
"""

    load_config,
    compute_indicators,
    should_dca,
    adjust_volume,
)

def run_sim(data_file: str, config_file: str, fallback: bool = False):
    # Load configuration (fallback uses a separate defaults file)
    cfg_path = config_file
    if fallback:
        cfg_path = "sim/config/sim_dca_config_fallback.yaml"
    config = load_config(cfg_path)

    # Load historical candles (expects a YAML list of dicts)
    with open(data_file) as f:
        history = yaml.safe_load(f)

    for candle in history:
        # Compute necessary indicators for this candle
        indicators = compute_indicators(candle, config)
        # Decide whether to simulate a DCA step
        fire, reason = should_dca(candle, config, indicators)
        if fire:
            volume = adjust_volume(candle, config, indicators)
            print(
                f"DCA step @ {candle.get('timestamp')} → volume={volume:.4f}, reason: {reason}"
            )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run DCA simulation on historical data"
    )
    parser.add_argument("datafile", help="Path to historical candles YAML")
    parser.add_argument(
        "--config",
        default="sim/config/dca_config.yaml",
        help="Path to active DCA config YAML",
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Use fallback defaults instead of active config",
    )
    args = parser.parse_args()
    run_sim(args.datafile, args.config, fallback=args.fallback)
