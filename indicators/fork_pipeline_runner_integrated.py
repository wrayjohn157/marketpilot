#!/usr/bin/env python3
"""
Integrated Fork Pipeline Runner - Uses Unified Trading Pipeline
Replaces old fragmented approach with new unified system
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from config.unified_config_manager import get_path, get_config
from pipeline.unified_trading_pipeline import UnifiedTradingPipeline, PipelineConfig
from utils.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# === CONFIG ===
FORK_INPUT_FILE = str(get_path("base") / "output" / "fork_candidates.json")
FINAL_OUTPUT_FILE = get_path("final_fork_rrr_trades")
BACKTEST_CANDIDATES_FILE = str(get_path("base") / "output" / "fork_backtest_candidates.json")
FORK_HISTORY_BASE = get_path("fork_history")

def load_fork_candidates() -> List[Dict[str, Any]]:
    """Load fork candidates from input file"""
    try:
        if not Path(FORK_INPUT_FILE).exists():
            logger.warning(f"Fork input file not found: {FORK_INPUT_FILE}")
            return []
        
        with open(FORK_INPUT_FILE, 'r') as f:
            candidates = json.load(f)
        
        logger.info(f"Loaded {len(candidates)} fork candidates")
        return candidates
    except Exception as e:
        logger.error(f"Failed to load fork candidates: {e}")
        return []

def save_results(trades: List[Dict[str, Any]], output_file: Path) -> None:
    """Save results to output file"""
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(trades, f, indent=2)
        logger.info(f"Saved {len(trades)} results to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

def write_to_history_log(entry: Dict[str, Any], date_str: str) -> None:
    """Write entry to history log"""
    try:
        out_dir = FORK_HISTORY_BASE / date_str
        out_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = out_dir / "fork_score_history.json"
        
        # Load existing history
        history = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                history = json.load(f)
        
        # Add new entry
        history.append(entry)
        
        # Save updated history
        with open(log_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.debug(f"Added entry to history: {entry.get('symbol', 'unknown')}")
    except Exception as e:
        logger.error(f"Failed to write to history log: {e}")

async def run_unified_pipeline() -> List[Dict[str, Any]]:
    """Run the unified trading pipeline"""
    try:
        # Load configuration
        config_data = get_config("unified_pipeline_config")
        pipeline_config = PipelineConfig(
            min_tech_score=config_data.get("min_tech_score", 0.6),
            min_fork_score=config_data.get("min_fork_score", 0.73),
            min_tv_score=config_data.get("min_tv_score", 0.8),
            btc_condition=config_data.get("btc_condition", "neutral"),
            tv_enabled=config_data.get("tv_enabled", True),
            max_trades_per_batch=config_data.get("max_trades_per_batch", 10)
        )
        
        # Initialize unified pipeline
        pipeline = UnifiedTradingPipeline(pipeline_config)
        
        # Load fork candidates
        candidates = load_fork_candidates()
        if not candidates:
            logger.warning("No fork candidates to process")
            return []
        
        # Process candidates through unified pipeline
        results = []
        for candidate in candidates:
            try:
                # Convert candidate to trade format
                trade_data = {
                    "symbol": candidate.get("symbol", ""),
                    "indicators": candidate.get("indicators", {}),
                    "timestamp": int(datetime.utcnow().timestamp())
                }
                
                # Process through pipeline
                processed_trade = await pipeline.process_trade(trade_data)
                
                if processed_trade and processed_trade.passed:
                    # Convert back to result format
                    result = {
                        "symbol": processed_trade.symbol,
                        "score": processed_trade.adjusted_score,
                        "indicators": processed_trade.indicators,
                        "tv_tag": processed_trade.tv_tag,
                        "tv_kicker": processed_trade.tv_kicker,
                        "passed": processed_trade.passed,
                        "timestamp": processed_trade.timestamp,
                        "reason": processed_trade.reason
                    }
                    results.append(result)
                    
                    logger.info(f"✅ {processed_trade.symbol} | Score: {processed_trade.adjusted_score:.3f} | {processed_trade.reason}")
                else:
                    logger.info(f"❌ {candidate.get('symbol', 'unknown')} | Failed pipeline processing")
                    
            except Exception as e:
                logger.error(f"Failed to process candidate {candidate.get('symbol', 'unknown')}: {e}")
                continue
        
        logger.info(f"Pipeline processing complete: {len(results)} trades passed")
        return results
        
    except Exception as e:
        logger.error(f"Failed to run unified pipeline: {e}")
        return []

def main():
    """Main function - run the integrated fork pipeline"""
    logger.info("🚀 Starting Integrated Fork Pipeline Runner")
    logger.info("=" * 60)
    
    try:
        # Run the unified pipeline
        results = asyncio.run(run_unified_pipeline())
        
        if results:
            # Save results
            save_results(results, FINAL_OUTPUT_FILE)
            
            # Save backtest candidates
            save_results(results, Path(BACKTEST_CANDIDATES_FILE))
            
            # Write to history log
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            for result in results:
                write_to_history_log(result, date_str)
            
            logger.info(f"✅ Pipeline complete: {len(results)} trades processed")
        else:
            logger.warning("No trades passed the pipeline")
        
        # Update Redis counters
        try:
            r = get_redis_manager()
            r.set_counter("fork_pipeline_processed", len(results))
            r.set_counter("fork_pipeline_timestamp", int(datetime.utcnow().timestamp()))
        except Exception as e:
            logger.warning(f"Failed to update Redis counters: {e}")
        
        logger.info("🎉 Integrated Fork Pipeline Runner complete")
        
    except Exception as e:
        logger.error(f"Pipeline runner failed: {e}")
        raise

if __name__ == "__main__":
    main()