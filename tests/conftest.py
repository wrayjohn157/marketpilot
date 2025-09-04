"""Pytest configuration and shared fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest

from core.fork_scorer_refactored import ForkScorer, ForkScoreResult
from dca.core.dca_engine import DCAEngine
from dca.core.snapshot_manager import SnapshotManager
from dca.core.trade_tracker import TradeTracker


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing."""
    return {
        "weights": {
            "macd_histogram": 0.3,
            "rsi_recovery": 0.4,
            "ema_price_reclaim": 0.3,
        },
        "min_score": 0.7,
        "btc_multiplier": 1.0,
        "name": "test_strategy",
    }


@pytest.fixture
def sample_indicators() -> Dict[str, Any]:
    """Sample indicator data for testing."""
    return {
        "macd_histogram": 0.02,
        "rsi_recovery": 0.7,
        "ema_price_reclaim": 1.0,
        "btc_trend": 0.8,
        "volume_spike": 1.2,
    }


@pytest.fixture
def sample_trade_data() -> Dict[str, Any]:
    """Sample trade data for testing."""
    return {
        "id": 12345,
        "pair": "USDT_BTC",
        "status": "active",
        "created_at": "2024-01-01T00:00:00.000Z",
        "bought_amount": 1000.0,
        "bought_volume": 0.025,
        "avg_entry_price": 40000.0,
        "current_price": 42000.0,
        "profit": 50.0,
        "profit_percentage": 5.0,
    }


@pytest.fixture
def temp_dir() -> Path:
    """Temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.sismember.return_value = False
    mock_redis.sadd.return_value = 1
    return mock_redis


@pytest.fixture
def mock_requests():
    """Mock requests module for testing."""
    with pytest.Mock() as mock:
        mock.post.return_value.status_code = 200
        mock.post.return_value.raise_for_status.return_value = None
        yield mock


@pytest.fixture
def fork_scorer(sample_config):
    """ForkScorer instance for testing."""
    return ForkScorer(sample_config)


@pytest.fixture
def snapshot_manager(temp_dir):
    """SnapshotManager instance for testing."""
    return SnapshotManager(temp_dir)


@pytest.fixture
def trade_tracker(temp_dir):
    """TradeTracker instance for testing."""
    return TradeTracker(temp_dir)


@pytest.fixture
def sample_fork_candidates():
    """Sample fork candidates for testing."""
    return [
        {
            "symbol": "USDT_BTC",
            "timestamp": 1714678900000,
            "score": 0.85,
            "score_components": {
                "macd_histogram": 0.15,
                "rsi_recovery": 0.28,
                "ema_price_reclaim": 0.42,
            },
            "passed": True,
            "reason": "passed",
        },
        {
            "symbol": "USDT_ETH",
            "timestamp": 1714678901000,
            "score": 0.65,
            "score_components": {
                "macd_histogram": 0.12,
                "rsi_recovery": 0.20,
                "ema_price_reclaim": 0.33,
            },
            "passed": False,
            "reason": "below threshold",
        },
    ]


@pytest.fixture
def sample_credentials():
    """Sample API credentials for testing."""
    return {
        "3commas_bot_id": "12345",
        "3commas_bot_id2": "67890",
        "3commas_email_token": "test_token",
        "3commas_api_key": "test_api_key",
        "3commas_api_secret": "test_api_secret",
    }
