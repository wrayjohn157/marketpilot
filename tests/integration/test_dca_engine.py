"""Integration tests for DCA Engine."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dca.core.dca_engine import DCAEngine


class TestDCAEngineIntegration:
    """Integration tests for DCAEngine."""

    @pytest.fixture
    def mock_config(self, temp_dir):
        """Mock configuration for testing."""
        config_path = temp_dir / "dca_config.yaml"
        config = {
            "scoring": {
                "weights": {
                    "macd_histogram": 0.3,
                    "rsi_recovery": 0.4,
                    "ema_price_reclaim": 0.3,
                },
                "min_score": 0.7
            },
            "dca_steps": [
                {"step": 1, "volume": 15.0, "min_gap": 2.0},
                {"step": 2, "volume": 25.0, "min_gap": 3.0}
            ]
        }
        
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(config, f)
        
        return config_path

    @pytest.fixture
    def mock_credentials(self, temp_dir):
        """Mock credentials for testing."""
        cred_path = temp_dir / "credentials.json"
        creds = {
            "3commas_bot_id": "12345",
            "3commas_email_token": "test_token",
            "3commas_api_key": "test_key",
            "3commas_api_secret": "test_secret"
        }
        
        with open(cred_path, 'w') as f:
            json.dump(creds, f)
        
        return cred_path

    @pytest.fixture
    def dca_engine(self, mock_config, mock_credentials, temp_dir):
        """DCA Engine instance for testing."""
        # Mock the PATHS and other dependencies
        with patch('dca.core.dca_engine.PATHS') as mock_paths:
            mock_paths.__getitem__.side_effect = lambda key: {
                "dca_config": mock_config,
                "paper_cred": mock_credentials,
                "base": temp_dir
            }.get(key, temp_dir)
            
            with patch('dca.core.dca_engine.SNAPSHOT_PATH', temp_dir):
                engine = DCAEngine(mock_config)
                return engine

    def test_dca_engine_initialization(self, dca_engine):
        """Test DCA Engine initialization."""
        assert dca_engine.config is not None
        assert dca_engine.snapshot_manager is not None
        assert dca_engine.trade_tracker is not None
        assert dca_engine.fork_scorer is not None

    def test_detect_local_reversal(self, dca_engine):
        """Test local reversal detection."""
        # Test V-shape pattern
        prices = [100, 95, 90, 88, 92]  # V-shape
        assert dca_engine.detect_local_reversal(prices) is True
        
        # Test non-V-shape pattern
        prices = [100, 95, 90, 85, 80]  # Downward trend
        assert dca_engine.detect_local_reversal(prices) is False
        
        # Test insufficient data
        prices = [100, 95]  # Not enough data
        assert dca_engine.detect_local_reversal(prices) is False

    @patch('dca.core.dca_engine.get_live_3c_trades')
    def test_run_no_trades(self, mock_get_trades, dca_engine):
        """Test run method with no trades."""
        mock_get_trades.return_value = []
        
        # Should not raise any exceptions
        dca_engine.run()

    @patch('dca.core.dca_engine.get_live_3c_trades')
    @patch('dca.core.dca_engine.is_zombie_trade')
    @patch('dca.core.dca_engine.evaluate_trade_health')
    @patch('dca.core.dca_engine.should_dca')
    def test_run_with_trades(self, mock_should_dca, mock_health, mock_zombie, mock_get_trades, dca_engine):
        """Test run method with trades."""
        # Setup mocks
        mock_get_trades.return_value = [
            {
                "id": 12345,
                "pair": "USDT_BTC",
                "status": "active",
                "created_at": "2024-01-01T00:00:00.000Z",
                "bought_amount": 1000.0,
                "bought_volume": 0.025,
                "avg_entry_price": 40000.0
            }
        ]
        
        mock_zombie.return_value = False
        mock_health.return_value = {"should_exit": False}
        mock_should_dca.return_value = {"should_dca": False}
        
        # Should not raise any exceptions
        dca_engine.run()

    @patch('dca.core.dca_engine.get_live_3c_trades')
    @patch('dca.core.dca_engine.is_zombie_trade')
    @patch('dca.core.dca_engine.evaluate_trade_health')
    @patch('dca.core.dca_engine.should_dca')
    @patch('dca.core.dca_engine.send_dca_signal')
    def test_run_with_dca_signal(self, mock_send_signal, mock_should_dca, mock_health, mock_zombie, mock_get_trades, dca_engine):
        """Test run method that triggers DCA signal."""
        # Setup mocks
        mock_get_trades.return_value = [
            {
                "id": 12345,
                "pair": "USDT_BTC",
                "status": "active",
                "created_at": "2024-01-01T00:00:00.000Z",
                "bought_amount": 1000.0,
                "bought_volume": 0.025,
                "avg_entry_price": 40000.0
            }
        ]
        
        mock_zombie.return_value = False
        mock_health.return_value = {"should_exit": False}
        mock_should_dca.return_value = {
            "should_dca": True,
            "volume": 15.0,
            "step": 1
        }
        
        dca_engine.run()
        
        # Verify DCA signal was sent
        mock_send_signal.assert_called_once_with("USDT_BTC", volume=15.0)

    def test_error_handling_in_run(self, dca_engine):
        """Test error handling in run method."""
        with patch('dca.core.dca_engine.get_live_3c_trades') as mock_get_trades:
            mock_get_trades.side_effect = Exception("API Error")
            
            # Should not raise exception, should handle gracefully
            with pytest.raises(Exception):
                dca_engine.run()

    def test_process_trade_invalid_data(self, dca_engine):
        """Test processing trade with invalid data."""
        invalid_trade = {"invalid": "data"}
        
        # Should handle gracefully without crashing
        dca_engine._process_trade(invalid_trade)

    def test_process_trade_missing_symbol(self, dca_engine):
        """Test processing trade with missing symbol."""
        trade = {"id": 12345}  # Missing pair/symbol
        
        # Should handle gracefully
        dca_engine._process_trade(trade)

    @patch('dca.core.dca_engine.get_latest_indicators')
    @patch('dca.core.dca_engine.should_dca')
    def test_process_dca_logic_no_indicators(self, mock_should_dca, mock_indicators, dca_engine):
        """Test DCA logic processing with no indicators."""
        trade = {"id": 12345, "pair": "USDT_BTC"}
        mock_indicators.return_value = None
        
        # Should handle gracefully
        dca_engine._process_dca_logic(trade, "USDT_BTC", 12345)
        
        # Should not call should_dca
        mock_should_dca.assert_not_called()

    @patch('dca.core.dca_engine.get_latest_indicators')
    @patch('dca.core.dca_engine.should_dca')
    @patch('dca.core.dca_engine.send_dca_signal')
    def test_process_dca_logic_should_dca(self, mock_send_signal, mock_should_dca, mock_indicators, dca_engine):
        """Test DCA logic when DCA should be triggered."""
        trade = {"id": 12345, "pair": "USDT_BTC"}
        mock_indicators.return_value = {"macd_histogram": 0.02}
        mock_should_dca.return_value = {
            "should_dca": True,
            "volume": 20.0,
            "step": 2
        }
        
        dca_engine._process_dca_logic(trade, "USDT_BTC", 12345)
        
        # Verify DCA signal was sent
        mock_send_signal.assert_called_once_with("USDT_BTC", volume=20.0)