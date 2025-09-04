#!/usr/bin/env python3
"""Refactored Smart DCA Signal - Clean, modular implementation."""

import logging
import sys
from pathlib import Path
from typing import List

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dca.core import DCAEngine
from config.config_loader import PATHS

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def detect_local_reversal(prices: List[float]) -> bool:
    """Detect local bottom reversal (V-shape) from price data.
    
    Args:
        prices: List of price values
        
    Returns:
        True if local reversal detected
    """
    if len(prices) < 5:
        return False
    return prices[-4] > prices[-3] > prices[-2] and prices[-2] < prices[-1]


def main() -> None:
    """Main entry point for DCA signal processing."""
    try:
        # Initialize DCA Engine
        config_path = PATHS["dca_config"]
        engine = DCAEngine(config_path)
        
        # Run DCA processing
        engine.run()
        
    except Exception as e:
        logger.error(f"Fatal error in DCA signal processing: {e}")
        raise


if __name__ == "__main__":
    main()