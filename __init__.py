import sys
from pathlib import Path

from .config import *
from .core import *

"""
MarketPilot Trading System

A comprehensive automated trading platform with DCA strategies,
technical analysis, and machine learning capabilities.
"""

__version__ = "2.0.0"
__author__ = "MarketPilot Team"

# Core modules
# Make this a proper Python package
# Add the project root to Python path once, properly
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
