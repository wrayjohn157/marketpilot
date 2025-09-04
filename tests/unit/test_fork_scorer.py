"""Unit tests for ForkScorer."""

import pytest

from core.fork_scorer_refactored import (
    ForkScorer,
    ForkScoreResult,
    score_fork_with_strategy,
)


class TestForkScorer:
    """Test cases for ForkScorer class."""

    def test_fork_scorer_initialization(self, sample_config):
        """Test ForkScorer initialization."""
        scorer = ForkScorer(sample_config)

        assert scorer.weights == sample_config["weights"]
        assert scorer.min_score == sample_config["min_score"]
        assert scorer.btc_multiplier == sample_config["btc_multiplier"]
        assert scorer.source == sample_config["name"]

    def test_score_fork_passing_score(self, fork_scorer, sample_indicators):
        """Test fork scoring with passing score."""
        result = fork_scorer.score_fork("USDT_BTC", 1714678900000, sample_indicators)

        assert isinstance(result, ForkScoreResult)
        assert result.symbol == "USDT_BTC"
        assert result.timestamp == 1714678900000
        assert result.score > 0.7  # Should pass threshold
        assert result.passed is True
        assert result.reason == "passed"
        assert result.btc_multiplier == 1.0
        assert result.source == "test_strategy"

    def test_score_fork_failing_score(self, sample_config, sample_indicators):
        """Test fork scoring with failing score."""
        # Create config with high threshold
        high_threshold_config = sample_config.copy()
        high_threshold_config["min_score"] = 0.95

        scorer = ForkScorer(high_threshold_config)
        result = scorer.score_fork("USDT_BTC", 1714678900000, sample_indicators)

        assert result.passed is False
        assert result.reason == "below threshold"

    def test_score_fork_missing_indicators(self, fork_scorer):
        """Test fork scoring with missing indicators."""
        incomplete_indicators = {"macd_histogram": 0.02}  # Missing other indicators

        result = fork_scorer.score_fork(
            "USDT_BTC", 1714678900000, incomplete_indicators
        )

        assert result.score < 0.7  # Should fail due to missing indicators
        assert result.passed is False

    def test_score_fork_invalid_indicators(self, fork_scorer):
        """Test fork scoring with invalid indicator values."""
        invalid_indicators = {
            "macd_histogram": "invalid",
            "rsi_recovery": None,
            "ema_price_reclaim": 1.0,
        }

        result = fork_scorer.score_fork("USDT_BTC", 1714678900000, invalid_indicators)

        # Should handle invalid values gracefully
        assert isinstance(result, ForkScoreResult)
        assert result.score >= 0  # Should not crash

    def test_validate_indicators_complete(self, fork_scorer, sample_indicators):
        """Test indicator validation with complete data."""
        assert fork_scorer.validate_indicators(sample_indicators) is True

    def test_validate_indicators_incomplete(self, fork_scorer):
        """Test indicator validation with incomplete data."""
        incomplete_indicators = {"macd_histogram": 0.02}
        assert fork_scorer.validate_indicators(incomplete_indicators) is False

    def test_get_score_breakdown(self, fork_scorer, sample_indicators):
        """Test score breakdown generation."""
        result = fork_scorer.score_fork("USDT_BTC", 1714678900000, sample_indicators)
        breakdown = fork_scorer.get_score_breakdown(result)

        assert isinstance(breakdown, str)
        assert "Score:" in breakdown
        assert "macd_histogram:" in breakdown
        assert "rsi_recovery:" in breakdown
        assert "ema_price_reclaim:" in breakdown

    def test_score_fork_with_strategy_function(self, sample_config, sample_indicators):
        """Test the standalone score_fork_with_strategy function."""
        result = score_fork_with_strategy(
            "USDT_BTC", 1714678900000, sample_indicators, sample_config
        )

        assert isinstance(result, ForkScoreResult)
        assert result.symbol == "USDT_BTC"
        assert result.passed is True

    def test_error_handling(self, fork_scorer):
        """Test error handling in fork scoring."""
        # Test with completely invalid data
        result = fork_scorer.score_fork("", None, {})

        assert isinstance(result, ForkScoreResult)
        assert result.score == 0.0
        assert result.passed is False
        assert "error" in result.reason.lower()

    def test_score_components_calculation(self, fork_scorer, sample_indicators):
        """Test that score components are calculated correctly."""
        result = fork_scorer.score_fork("USDT_BTC", 1714678900000, sample_indicators)

        # Check that each component is calculated correctly
        expected_macd = (
            sample_indicators["macd_histogram"] * fork_scorer.weights["macd_histogram"]
        )
        expected_rsi = (
            sample_indicators["rsi_recovery"] * fork_scorer.weights["rsi_recovery"]
        )
        expected_ema = (
            sample_indicators["ema_price_reclaim"]
            * fork_scorer.weights["ema_price_reclaim"]
        )

        assert abs(result.score_components["macd_histogram"] - expected_macd) < 0.0001
        assert abs(result.score_components["rsi_recovery"] - expected_rsi) < 0.0001
        assert abs(result.score_components["ema_price_reclaim"] - expected_ema) < 0.0001
