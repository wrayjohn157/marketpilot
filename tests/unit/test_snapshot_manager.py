"""Unit tests for SnapshotManager."""

import json
from pathlib import Path

import pytest

from dca.core.snapshot_manager import SnapshotManager


class TestSnapshotManager:
    """Test cases for SnapshotManager class."""

    def test_snapshot_manager_initialization(self, temp_dir):
        """Test SnapshotManager initialization."""
        manager = SnapshotManager(temp_dir)
        assert manager.snapshot_dir == temp_dir
        assert temp_dir.exists()

    def test_get_last_snapshot_values_file_not_exists(self, temp_dir):
        """Test getting snapshot values when file doesn't exist."""
        manager = SnapshotManager(temp_dir)
        confidence, tp1_shift = manager.get_last_snapshot_values("USDT_BTC", 12345)

        assert confidence == 0.0
        assert tp1_shift == 0.0

    def test_get_last_snapshot_values_empty_file(self, temp_dir):
        """Test getting snapshot values from empty file."""
        manager = SnapshotManager(temp_dir)
        snap_path = temp_dir / "USDT_BTC_12345.jsonl"
        snap_path.touch()  # Create empty file

        confidence, tp1_shift = manager.get_last_snapshot_values("USDT_BTC", 12345)

        assert confidence == 0.0
        assert tp1_shift == 0.0

    def test_get_last_snapshot_values_valid_data(self, temp_dir):
        """Test getting snapshot values from valid data."""
        manager = SnapshotManager(temp_dir)
        snap_path = temp_dir / "USDT_BTC_12345.jsonl"

        # Write test data
        test_data = [
            {"confidence_score": 0.5, "tp1_shift": 0.1, "timestamp": "2024-01-01"},
            {"confidence_score": 0.8, "tp1_shift": 0.2, "timestamp": "2024-01-02"},
        ]

        with open(snap_path, "w") as f:
            for data in test_data:
                f.write(json.dumps(data) + "\n")

        confidence, tp1_shift = manager.get_last_snapshot_values("USDT_BTC", 12345)

        assert confidence == 0.8  # Last entry
        assert tp1_shift == 0.2

    def test_get_last_snapshot_values_missing_keys(self, temp_dir):
        """Test getting snapshot values when keys are missing."""
        manager = SnapshotManager(temp_dir)
        snap_path = temp_dir / "USDT_BTC_12345.jsonl"

        # Write data without required keys
        test_data = {"timestamp": "2024-01-01", "other_key": "value"}

        with open(snap_path, "w") as f:
            f.write(json.dumps(test_data) + "\n")

        confidence, tp1_shift = manager.get_last_snapshot_values("USDT_BTC", 12345)

        assert confidence == 0.0
        assert tp1_shift == 0.0

    def test_get_last_snapshot_values_invalid_json(self, temp_dir, caplog):
        """Test getting snapshot values with invalid JSON."""
        manager = SnapshotManager(temp_dir)
        snap_path = temp_dir / "USDT_BTC_12345.jsonl"

        # Write invalid JSON
        with open(snap_path, "w") as f:
            f.write("invalid json data\n")

        confidence, tp1_shift = manager.get_last_snapshot_values("USDT_BTC", 12345)

        assert confidence == 0.0
        assert tp1_shift == 0.0
        assert "Failed to read snapshot" in caplog.text

    def test_save_snapshot(self, temp_dir):
        """Test saving snapshot data."""
        manager = SnapshotManager(temp_dir)
        snap_path = temp_dir / "USDT_BTC_12345.jsonl"

        snapshot_data = {
            "confidence_score": 0.75,
            "tp1_shift": 0.15,
            "timestamp": "2024-01-01T00:00:00Z",
        }

        manager.save_snapshot("USDT_BTC", 12345, snapshot_data)

        assert snap_path.exists()

        # Verify data was written correctly
        with open(snap_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            saved_data = json.loads(lines[0])
            assert saved_data == snapshot_data

    def test_save_snapshot_append_mode(self, temp_dir):
        """Test that save_snapshot appends to existing file."""
        manager = SnapshotManager(temp_dir)
        snap_path = temp_dir / "USDT_BTC_12345.jsonl"

        # Save first snapshot
        snapshot1 = {"confidence_score": 0.5, "tp1_shift": 0.1}
        manager.save_snapshot("USDT_BTC", 12345, snapshot1)

        # Save second snapshot
        snapshot2 = {"confidence_score": 0.8, "tp1_shift": 0.2}
        manager.save_snapshot("USDT_BTC", 12345, snapshot2)

        # Verify both snapshots are in file
        with open(snap_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2

            data1 = json.loads(lines[0])
            data2 = json.loads(lines[1])

            assert data1 == snapshot1
            assert data2 == snapshot2

    def test_save_snapshot_io_error(self, temp_dir, caplog):
        """Test save_snapshot with IO error."""
        manager = SnapshotManager(temp_dir)

        # Create a directory with the same name as the file to cause IO error
        snap_path = temp_dir / "USDT_BTC_12345.jsonl"
        snap_path.mkdir(parents=True)

        snapshot_data = {"confidence_score": 0.75, "tp1_shift": 0.15}
        manager.save_snapshot("USDT_BTC", 12345, snapshot_data)

        assert "Failed to save snapshot" in caplog.text

    def test_multiple_symbols(self, temp_dir):
        """Test handling multiple symbols."""
        manager = SnapshotManager(temp_dir)

        # Save snapshots for different symbols
        manager.save_snapshot("USDT_BTC", 12345, {"confidence_score": 0.8})
        manager.save_snapshot("USDT_ETH", 67890, {"confidence_score": 0.6})

        # Verify they are stored separately
        btc_confidence, _ = manager.get_last_snapshot_values("USDT_BTC", 12345)
        eth_confidence, _ = manager.get_last_snapshot_values("USDT_ETH", 67890)

        assert btc_confidence == 0.8
        assert eth_confidence == 0.6
