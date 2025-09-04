"""Type definitions for Market7 trading system."""

from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
from pathlib import Path

# Basic types
Symbol = str
DealId = int
Timestamp = int
Volume = float
Price = float
Percentage = float

# Trading data structures
TradeData = Dict[str, Any]
IndicatorData = Dict[str, Union[float, int, str]]
SnapshotData = Dict[str, Any]
ConfigData = Dict[str, Any]

# API response types
APIResponse = Dict[str, Any]
Credentials = Dict[str, str]

# File paths
FilePath = Union[str, Path]

# Trading decisions
DCADecision = Dict[str, Any]
ForkScore = Dict[str, Any]
RecoveryOdds = Tuple[float, float]  # (odds, confidence)

# Market data
KlineData = List[Union[float, int]]
PriceData = List[float]

# Configuration types
DCAConfig = Dict[str, Any]
LeverageConfig = Dict[str, Any]
ForkConfig = Dict[str, Any]

# Logging types
LogEntry = Dict[str, Any]
TradeLog = Dict[str, Any]

# ML model types
ModelPrediction = Dict[str, float]
FeatureVector = List[float]

# Exchange types
OrderData = Dict[str, Any]
PositionData = Dict[str, Any]
BalanceData = Dict[str, Any]

# Error types
ErrorCode = int
ErrorMessage = str
ErrorContext = Dict[str, Any]