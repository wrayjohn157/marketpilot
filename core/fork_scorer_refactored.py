from typing import Dict, Any, Optional, Tuple
import logging

from dataclasses import dataclass

"""Refactored Fork Scorer - Clean, type-safe implementation."""

logger = logging.getLogger(__name__)

@dataclass
class ForkScoreResult:
    """Result of fork scoring operation."""
    symbol: str
    timestamp: int
    score: float
    score_components: Dict[str, float]
    passed: bool
    reason: str
    btc_multiplier: float = 1.0
    source: str = "unknown"

class ForkScorer:
    """Enhanced fork scorer with better error handling and type safety."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize fork scorer.
        
        Args:
            config: Scoring configuration
        """
        self.config = config
        self.weights = config.get("weights", {})
        self.min_score = config.get("min_score", 0.7)
        self.btc_multiplier = config.get("btc_multiplier", 1.0)
        self.source = config.get("name", "unknown")
    
    def score_fork(
        self, 
        symbol: str, 
        timestamp: int, 
        indicators: Dict[str, Any]
    ) -> ForkScoreResult:
        """Compute fork score for a given symbol and indicator snapshot.
        
        Args:
            symbol: Symbol being scored (e.g., "USDT_XRP")
            timestamp: Timestamp of fork candidate
            indicators: Snapshot of indicators (MACD, RSI, etc)
            
        Returns:
            ForkScoreResult with scoring details
        """
        try:
            score_components = {}
            total_score = 0.0
            
            # Calculate weighted score components
            for key, weight in self.weights.items():
                value = indicators.get(key, 0)
                if not isinstance(value, (int, float)):
                    logger.warning(f"Invalid indicator value for {key}: {value}")
                    value = 0
                
                component_score = float(value) * float(weight)
                score_components[key] = round(component_score, 4)
                total_score += component_score
            
            # Determine if score passes threshold
            passed = total_score >= self.min_score
            reason = "passed" if passed else "below threshold"
            
            return ForkScoreResult(
                symbol=symbol,
                timestamp=timestamp,
                score=round(total_score, 4),
                score_components=score_components,
                passed=passed,
                reason=reason,
                btc_multiplier=self.btc_multiplier,
                source=self.source
            )
            
        except Exception as e:
            logger.error(f"Error scoring fork for {symbol}: {e}")
            return ForkScoreResult(
                symbol=symbol,
                timestamp=timestamp,
                score=0.0,
                score_components={},
                passed=False,
                reason=f"scoring error: {e}",
                btc_multiplier=self.btc_multiplier,
                source=self.source
            )
    
    def validate_indicators(self, indicators: Dict[str, Any]) -> bool:
        """Validate that required indicators are present.
        
        Args:
            indicators: Indicator data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_indicators = set(self.weights.keys())
        available_indicators = set(indicators.keys())
        
        missing = required_indicators - available_indicators
        if missing:
            logger.warning(f"Missing required indicators: {missing}")
            return False
        
        return True
    
    def get_score_breakdown(self, result: ForkScoreResult) -> str:
        """Get human-readable score breakdown.
        
        Args:
            result: Fork score result
            
        Returns:
            Formatted score breakdown string
        """
        breakdown = []
        for component, score in result.score_components.items():
            weight = self.weights.get(component, 0)
            breakdown.append(f"{component}: {score:.4f} (weight: {weight})")
        
        return f"Score: {result.score:.4f} | " + " | ".join(breakdown)

def score_fork_with_strategy(
    symbol: str, 
    timestamp: int, 
    indicators: Dict[str, Any], 
    strategy: Dict[str, Any]
) -> ForkScoreResult:
    """Score fork using a specific strategy configuration.
    
    Args:
        symbol: Symbol being scored
        timestamp: Timestamp of fork candidate
        indicators: Snapshot of indicators
        strategy: Strategy configuration
        
    Returns:
        Fork score result
    """
    scorer = ForkScorer(strategy)
    return scorer.score_fork(symbol, timestamp, indicators)

# Backward compatibility function
def score_fork(
    symbol: str, 
    timestamp: int, 
    indicators: Dict[str, Any], 
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Legacy fork scoring function for backward compatibility.
    
    Args:
        symbol: Symbol being scored
        timestamp: Timestamp of fork candidate
        indicators: Snapshot of indicators
        config: Scoring configuration
        
    Returns:
        Dictionary with scoring results
    """
    scorer = ForkScorer(config)
    result = scorer.score_fork(symbol, timestamp, indicators)
    
    return {
        "symbol": result.symbol,
        "timestamp": result.timestamp,
        "score": result.score,
        "score_components": result.score_components,
        "passed": result.passed,
        "reason": result.reason
    }

if __name__ == "__main__":
    # Example usage
    example_indicators = {
        "macd_histogram": 0.02,
        "rsi_recovery": 0.7,
        "ema_price_reclaim": 1,
    }

    example_config = {
        "weights": {
            "macd_histogram": 0.3,
            "rsi_recovery": 0.4,
            "ema_price_reclaim": 0.3,
        },
        "min_score": 0.7,
        "name": "example_strategy"
    }

    scorer = ForkScorer(example_config)
    result = scorer.score_fork("USDT_ABC", 1714678900000, example_indicators)
    print(f"Result: {result}")
    print(f"Breakdown: {scorer.get_score_breakdown(result)}")