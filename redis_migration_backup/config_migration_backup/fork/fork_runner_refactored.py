from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

import requests
import yaml

from config.config_loader import PATHS
from core.fork_scorer_refactored import ForkScorer
from fork.utils.entry_utils import get_entry_price, compute_score_hash
from fork.utils.fork_entry_logger import log_fork_entry
import hashlib
import hmac
import subprocess
from utils.credential_manager import get_3commas_credentials


#!/usr/bin/env python3
"""Refactored Fork Runner - Clean, modular implementation."""

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class ForkRunner:
    """Main fork detection and execution engine."""
    
    def __init__(self, config_path: Path):
        """Initialize fork runner.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize Redis connection
        self.redis_client = self._init_redis()
        
        # Load credentials
        self.credentials = self._load_credentials()
        
        # Initialize fork scorer
        self.fork_scorer = ForkScorer(self.config.get("scoring", {}))
        
        # Script paths
        self.project_root = Path(__file__).parent.parent
        self.fork_score_script = self.project_root / "indicators" / "fork_score_filter.py"
        self.tv_kicker_script = self.project_root / "indicators" / "tv_kicker.py"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, IOError) as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {}
    
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection.
        
        Returns:
            Redis client or None if connection fails
        """
        try:
            return redis.Redis(host="localhost", port=6379, decode_responses=True)
        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            return None
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load API credentials.
        
        Returns:
            Credentials dictionary
        """
        cred_path = PATHS["paper_cred"]
        try:
            with open(cred_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load credentials: {e}")
            return {}
    
    def format_pair(self, symbol: str) -> str:
        """Format symbol for 3Commas API.
        
        Args:
            symbol: Raw symbol string
            
        Returns:
            Formatted symbol
        """
        return f"USDT_{symbol.replace('USDT', '').replace('USDT_', '')}"
    
    def run_fork_score_filter(self) -> List[Dict[str, Any]]:
        """Run fork score filter script.
        
        Returns:
            List of scored fork candidates
        """
        try:
            result = subprocess.run(
                [str(self.fork_score_script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Fork score filter failed: {result.stderr}")
                return []
            
            # Parse output
            candidates = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        candidate = json.loads(line)
                        candidates.append(candidate)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse candidate: {e}")
                        continue
            
            return candidates
            
        except subprocess.TimeoutExpired:
            logger.error("Fork score filter timed out")
            return []
        except Exception as e:
            logger.error(f"Error running fork score filter: {e}")
            return []
    
    def run_tv_kicker(self) -> List[Dict[str, Any]]:
        """Run TradingView kicker script.
        
        Returns:
            List of TV signals
        """
        try:
            result = subprocess.run(
                [str(self.tv_kicker_script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"TV kicker failed: {result.stderr}")
                return []
            
            # Parse output
            signals = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        signal = json.loads(line)
                        signals.append(signal)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse TV signal: {e}")
                        continue
            
            return signals
            
        except subprocess.TimeoutExpired:
            logger.error("TV kicker timed out")
            return []
        except Exception as e:
            logger.error(f"Error running TV kicker: {e}")
            return []
    
    def send_3commas_signal(self, symbol: str, side: str = "buy") -> bool:
        """Send signal to 3Commas.
        
        Args:
            symbol: Trading symbol
            side: Trade side (buy/sell)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "action": side,
                "message_type": "bot",
                "bot_id": self.credentials.get("3commas_bot_id"),
                "email_token": self.credentials.get("3commas_email_token"),
                "delay_seconds": 0,
                "pair": self.format_pair(symbol),
            }
            
            url = "https://app.3commas.io/trade_signal/trading_view"
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✅ Signal sent for {symbol} ({side})")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to send signal for {symbol}: {e}")
            return False
        except KeyError as e:
            logger.error(f"Missing credential: {e}")
            return False
    
    def process_candidates(self, candidates: List[Dict[str, Any]]) -> None:
        """Process fork candidates and send signals.
        
        Args:
            candidates: List of fork candidates
        """
        for candidate in candidates:
            try:
                symbol = candidate.get("symbol", "")
                if not symbol:
                    continue
                
                # Check if already sent
                if self.redis_client and self.redis_client.sismember("FORK_SENT_TRADES", symbol):
                    logger.info(f"Signal already sent for {symbol}")
                    continue
                
                # Send signal
                if self.send_3commas_signal(symbol):
                    # Mark as sent
                    if self.redis_client:
                        self.redis_client.sadd("FORK_SENT_TRADES", symbol)
                    
                    # Log entry
                    log_fork_entry(candidate)
                    
            except Exception as e:
                logger.error(f"Error processing candidate {candidate}: {e}")
    
    def run(self) -> None:
        """Main execution loop."""
        logger.info("Starting Fork Runner...")
        
        try:
            # Run fork score filter
            candidates = self.run_fork_score_filter()
            if not candidates:
                logger.info("No fork candidates found")
                return
            
            logger.info(f"Found {len(candidates)} fork candidates")
            
            # Process candidates
            self.process_candidates(candidates)
            
            # Run TV kicker
            tv_signals = self.run_tv_kicker()
            if tv_signals:
                logger.info(f"Found {len(tv_signals)} TV signals")
                # Process TV signals if needed
            
        except Exception as e:
            logger.error(f"Error in fork runner: {e}")
            raise

def main() -> Any:
    """Main entry point."""
    config_path = PATHS.get("fork_config", Path("config/fork_config.yaml"))
    runner = ForkRunner(config_path)
    runner.run()

if __name__ == "__main__":
    main()