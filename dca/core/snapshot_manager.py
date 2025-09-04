"""Snapshot management utilities for DCA trading."""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Manages snapshot data for DCA trading decisions."""
    
    def __init__(self, snapshot_dir: Path):
        """Initialize snapshot manager.
        
        Args:
            snapshot_dir: Directory where snapshots are stored
        """
        self.snapshot_dir = snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    def get_last_snapshot_values(self, symbol: str, deal_id: int) -> Tuple[float, float]:
        """Get the last snapshot values for a symbol and deal.
        
        Args:
            symbol: Trading symbol
            deal_id: Deal identifier
            
        Returns:
            Tuple of (confidence_score, tp1_shift)
        """
        snap_path = self.snapshot_dir / f"{symbol}_{deal_id}.jsonl"
        if not snap_path.exists():
            return 0.0, 0.0
        
        try:
            with open(snap_path, "r") as f:
                lines = f.readlines()
                if not lines:
                    return 0.0, 0.0
                last = json.loads(lines[-1])
                return last.get("confidence_score", 0.0), last.get("tp1_shift", 0.0)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read snapshot for {symbol}_{deal_id}: {e}")
            return 0.0, 0.0
    
    def save_snapshot(self, symbol: str, deal_id: int, snapshot_data: dict) -> None:
        """Save snapshot data to file.
        
        Args:
            symbol: Trading symbol
            deal_id: Deal identifier
            snapshot_data: Data to save
        """
        snap_path = self.snapshot_dir / f"{symbol}_{deal_id}.jsonl"
        try:
            with open(snap_path, "a") as f:
                f.write(json.dumps(snapshot_data) + "\n")
        except IOError as e:
            logger.error(f"Failed to save snapshot for {symbol}_{deal_id}: {e}")