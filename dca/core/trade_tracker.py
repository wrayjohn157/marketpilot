from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import logging

"""Trade tracking utilities for DCA operations."""

logger = logging.getLogger(__name__)

class TradeTracker:
    """Tracks DCA trade operations and prevents duplicate signals."""
    
    def __init__(self, tracking_path: Path):
        """Initialize trade tracker.
        
        Args:
            tracking_path: Path to the tracking file
        """
        self.tracking_path = tracking_path
        self.tracking_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_last_logged_snapshot(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """Get the last logged snapshot for a deal.
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Last logged snapshot or None
        """
        if not self.tracking_path.exists():
            return None
        
        try:
            with open(self.tracking_path, "r") as f:
                entries = [
                    json.loads(line) for line in f 
                    if f'"deal_id": {deal_id}' in line
                ]
            if not entries:
                return None
            return entries[-1]
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read tracking data for deal {deal_id}: {e}")
            return None
    
    def get_last_fired_step(self, deal_id: int) -> int:
        """Get the last fired step for a deal.
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Last fired step number
        """
        if not self.tracking_path.exists():
            return 0
        
        last = 0
        try:
            with open(self.tracking_path, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj["deal_id"] == deal_id and obj.get("step", 0) > last:
                            last = obj["step"]
                    except (json.JSONDecodeError, KeyError):
                        continue
        except IOError as e:
            logger.warning(f"Failed to read tracking data: {e}")
        
        return last
    
    def was_dca_fired_recently(self, deal_id: int, step: int) -> bool:
        """Check if DCA was fired recently for a specific step.
        
        Args:
            deal_id: Deal identifier
            step: Step number
            
        Returns:
            True if DCA was fired recently for this step
        """
        if not self.tracking_path.exists():
            return False
        
        try:
            with open(self.tracking_path, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj["deal_id"] == deal_id and obj["step"] == step:
                            return True
                    except (json.JSONDecodeError, KeyError):
                        continue
        except IOError as e:
            logger.warning(f"Failed to read tracking data: {e}")
        
        return False
    
    def update_dca_log(self, deal_id: int, step: int, symbol: str) -> None:
        """Update DCA log with new entry.
        
        Args:
            deal_id: Deal identifier
            step: Step number
            symbol: Trading symbol
        """
        entry = {
            "deal_id": deal_id,
            "step": step,
            "symbol": symbol,
            "timestamp": str(datetime.utcnow())
        }
        
        try:
            with open(self.tracking_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logger.error(f"Failed to update DCA log: {e}")
    
    def write_log(self, entry: Dict[str, Any]) -> None:
        """Write log entry to tracking file.
        
        Args:
            entry: Log entry data
        """
        try:
            with open(self.tracking_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            logger.error(f"Failed to write log entry: {e}")