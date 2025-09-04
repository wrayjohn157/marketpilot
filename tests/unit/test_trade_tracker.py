"""Unit tests for TradeTracker."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from dca.core.trade_tracker import TradeTracker


class TestTradeTracker:
    """Test cases for TradeTracker class."""

    def test_trade_tracker_initialization(self, temp_dir):
        """Test TradeTracker initialization."""
        tracker = TradeTracker(temp_dir)
        assert tracker.tracking_path == temp_dir
        assert temp_dir.parent.exists()

    def test_get_last_logged_snapshot_no_file(self, temp_dir):
        """Test getting last logged snapshot when file doesn't exist."""
        tracker = TradeTracker(temp_dir)
        result = tracker.get_last_logged_snapshot(12345)
        assert result is None

    def test_get_last_logged_snapshot_no_matching_deal(self, temp_dir):
        """Test getting last logged snapshot when no matching deal exists."""
        tracker = TradeTracker(temp_dir)

        # Create file with different deal ID
        with open(tracker.tracking_path, "w") as f:
            f.write(json.dumps({"deal_id": 99999, "step": 1}) + "\n")

        result = tracker.get_last_logged_snapshot(12345)
        assert result is None

    def test_get_last_logged_snapshot_matching_deal(self, temp_dir):
        """Test getting last logged snapshot with matching deal."""
        tracker = TradeTracker(temp_dir)

        # Create file with matching deal ID
        test_data = {
            "deal_id": 12345,
            "step": 2,
            "symbol": "USDT_BTC",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        with open(tracker.tracking_path, "w") as f:
            f.write(json.dumps(test_data) + "\n")

        result = tracker.get_last_logged_snapshot(12345)
        assert result == test_data

    def test_get_last_logged_snapshot_multiple_entries(self, temp_dir):
        """Test getting last logged snapshot with multiple entries."""
        tracker = TradeTracker(temp_dir)

        # Create file with multiple entries for same deal
        entries = [
            {"deal_id": 12345, "step": 1, "timestamp": "2024-01-01T00:00:00Z"},
            {"deal_id": 12345, "step": 2, "timestamp": "2024-01-01T01:00:00Z"},
            {"deal_id": 12345, "step": 3, "timestamp": "2024-01-01T02:00:00Z"},
        ]

        with open(tracker.tracking_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        result = tracker.get_last_logged_snapshot(12345)
        assert result == entries[-1]  # Should return last entry

    def test_get_last_fired_step_no_file(self, temp_dir):
        """Test getting last fired step when file doesn't exist."""
        tracker = TradeTracker(temp_dir)
        result = tracker.get_last_fired_step(12345)
        assert result == 0

    def test_get_last_fired_step_no_matching_deal(self, temp_dir):
        """Test getting last fired step when no matching deal exists."""
        tracker = TradeTracker(temp_dir)

        with open(tracker.tracking_path, "w") as f:
            f.write(json.dumps({"deal_id": 99999, "step": 5}) + "\n")

        result = tracker.get_last_fired_step(12345)
        assert result == 0

    def test_get_last_fired_step_matching_deal(self, temp_dir):
        """Test getting last fired step with matching deal."""
        tracker = TradeTracker(temp_dir)

        entries = [
            {"deal_id": 12345, "step": 1},
            {"deal_id": 12345, "step": 3},
            {"deal_id": 12345, "step": 2},
        ]

        with open(tracker.tracking_path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        result = tracker.get_last_fired_step(12345)
        assert result == 3  # Should return highest step

    def test_was_dca_fired_recently_no_file(self, temp_dir):
        """Test was_dca_fired_recently when file doesn't exist."""
        tracker = TradeTracker(temp_dir)
        result = tracker.was_dca_fired_recently(12345, 1)
        assert result is False

    def test_was_dca_fired_recently_not_fired(self, temp_dir):
        """Test was_dca_fired_recently when step wasn't fired."""
        tracker = TradeTracker(temp_dir)

        with open(tracker.tracking_path, "w") as f:
            f.write(json.dumps({"deal_id": 12345, "step": 1}) + "\n")

        result = tracker.was_dca_fired_recently(12345, 2)
        assert result is False

    def test_was_dca_fired_recently_fired(self, temp_dir):
        """Test was_dca_fired_recently when step was fired."""
        tracker = TradeTracker(temp_dir)

        with open(tracker.tracking_path, "w") as f:
            f.write(json.dumps({"deal_id": 12345, "step": 2}) + "\n")

        result = tracker.was_dca_fired_recently(12345, 2)
        assert result is True

    def test_update_dca_log(self, temp_dir):
        """Test updating DCA log."""
        tracker = TradeTracker(temp_dir)

        tracker.update_dca_log(12345, 1, "USDT_BTC")

        assert tracker.tracking_path.exists()

        with open(tracker.tracking_path, "r") as f:
            data = json.loads(f.read())
            assert data["deal_id"] == 12345
            assert data["step"] == 1
            assert data["symbol"] == "USDT_BTC"
            assert "timestamp" in data

    def test_write_log(self, temp_dir):
        """Test writing log entry."""
        tracker = TradeTracker(temp_dir)

        log_entry = {"deal_id": 12345, "action": "test", "data": {"key": "value"}}

        tracker.write_log(log_entry)

        assert tracker.tracking_path.exists()

        with open(tracker.tracking_path, "r") as f:
            data = json.loads(f.read())
            assert data == log_entry

    def test_invalid_json_handling(self, temp_dir, caplog):
        """Test handling of invalid JSON in tracking file."""
        tracker = TradeTracker(temp_dir)

        # Write invalid JSON
        with open(tracker.tracking_path, "w") as f:
            f.write("invalid json\n")
            f.write(json.dumps({"deal_id": 12345, "step": 1}) + "\n")

        result = tracker.get_last_fired_step(12345)
        assert result == 1  # Should handle invalid line gracefully

    def test_io_error_handling(self, temp_dir, caplog):
        """Test IO error handling."""
        tracker = TradeTracker(temp_dir)

        # Create a directory with the same name as the tracking file
        tracker.tracking_path.mkdir(parents=True)

        tracker.write_log({"test": "data"})
        assert "Failed to write log entry" in caplog.text
