#!/usr/bin/env python3
"""
Profitability Analyzer for Smart DCA System
Analyzes trade performance and provides optimization recommendations
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ProfitabilityAnalyzer:
    """
    Analyzes DCA trade performance and provides optimization insights
    """

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.analysis_results = {}

    def analyze_recent_trades(self, days: int = 7) -> Dict[str, any]:
        """Analyze recent trades for profitability patterns"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        trades_data = []

        # Collect trade data from logs
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = self.log_dir / date / "smart_dca_log.jsonl"

            if log_file.exists():
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            trade = json.loads(line)
                            trades_data.append(trade)
                        except json.JSONDecodeError:
                            continue

        if not trades_data:
            return {"error": "No trade data found"}

        # Convert to DataFrame for analysis
        df = pd.DataFrame(trades_data)

        # Calculate profitability metrics
        analysis = {
            "total_trades": len(df),
            "rescue_trades": len(df[df["decision"] == "rescue"]),
            "skipped_trades": len(df[df["decision"] == "skip"]),
            "rescue_rate": len(df[df["decision"] == "rescue"]) / len(df) * 100,
            "avg_confidence": df["rescue_confidence"].mean(),
            "avg_drawdown": df["deviation_pct"].mean(),
            "avg_volume": df["volume"].mean(),
            "profitability_score": self._calculate_profitability_score(df),
            "recommendations": self._generate_recommendations(df),
        }

        return analysis

    def _calculate_profitability_score(self, df: pd.DataFrame) -> float:
        """Calculate overall profitability score (0-100)"""
        if df.empty:
            return 0.0

        # Factors that contribute to profitability
        factors = []

        # 1. Rescue confidence (higher is better)
        avg_confidence = df["rescue_confidence"].mean()
        factors.append(("confidence", avg_confidence * 100))

        # 2. Drawdown management (moderate drawdown is good)
        avg_drawdown = df["deviation_pct"].mean()
        drawdown_score = max(0, 100 - (avg_drawdown - 2) * 10)  # Optimal around 2%
        factors.append(("drawdown_management", drawdown_score))

        # 3. Volume efficiency (not too high, not too low)
        avg_volume = df["volume"].mean()
        volume_score = max(
            0, 100 - abs(avg_volume - 100) * 0.5
        )  # Optimal around 100 USDT
        factors.append(("volume_efficiency", volume_score))

        # 4. Recovery odds (higher is better)
        avg_recovery = df["recovery_odds"].mean()
        factors.append(("recovery_odds", avg_recovery * 100))

        # 5. SAFU score (higher is better)
        avg_safu = df["safu_score"].mean()
        factors.append(("safu_score", avg_safu * 100))

        # Weighted average
        weights = [
            0.25,
            0.20,
            0.15,
            0.25,
            0.15,
        ]  # Confidence and recovery most important
        weighted_score = sum(
            factor[1] * weight for factor, weight in zip(factors, weights)
        )

        return min(weighted_score, 100.0)

    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate optimization recommendations based on data"""
        recommendations = []

        if df.empty:
            return ["No data available for analysis"]

        # Analyze rescue rate
        rescue_rate = len(df[df["decision"] == "rescue"]) / len(df) * 100
        if rescue_rate < 20:
            recommendations.append(
                "Low rescue rate - consider lowering confidence thresholds"
            )
        elif rescue_rate > 60:
            recommendations.append(
                "High rescue rate - consider raising confidence thresholds"
            )

        # Analyze confidence levels
        avg_confidence = df["rescue_confidence"].mean()
        if avg_confidence < 0.6:
            recommendations.append("Low average confidence - review ML model training")
        elif avg_confidence > 0.8:
            recommendations.append("High confidence - system may be too conservative")

        # Analyze drawdown patterns
        avg_drawdown = df["deviation_pct"].mean()
        if avg_drawdown < 1.0:
            recommendations.append("Low drawdown - consider lowering trigger threshold")
        elif avg_drawdown > 5.0:
            recommendations.append("High drawdown - consider raising trigger threshold")

        # Analyze volume efficiency
        avg_volume = df["volume"].mean()
        if avg_volume < 50:
            recommendations.append("Low volume - consider increasing base volume")
        elif avg_volume > 200:
            recommendations.append("High volume - consider reducing base volume")

        # Analyze recovery odds
        avg_recovery = df["recovery_odds"].mean()
        if avg_recovery < 0.5:
            recommendations.append(
                "Low recovery odds - review recovery prediction model"
            )

        # Analyze SAFU scores
        avg_safu = df["safu_score"].mean()
        if avg_safu < 0.4:
            recommendations.append("Low SAFU scores - review safety evaluation")

        return recommendations

    def analyze_by_symbol(self, days: int = 7) -> Dict[str, Dict]:
        """Analyze profitability by trading symbol"""
        end_date = datetime.utcnow()
        trades_data = []

        # Collect trade data
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = self.log_dir / date / "smart_dca_log.jsonl"

            if log_file.exists():
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            trade = json.loads(line)
                            trades_data.append(trade)
                        except json.JSONDecodeError:
                            continue

        if not trades_data:
            return {"error": "No trade data found"}

        df = pd.DataFrame(trades_data)
        symbol_analysis = {}

        for symbol in df["symbol"].unique():
            symbol_df = df[df["symbol"] == symbol]

            symbol_analysis[symbol] = {
                "total_trades": len(symbol_df),
                "rescue_rate": len(symbol_df[symbol_df["decision"] == "rescue"])
                / len(symbol_df)
                * 100,
                "avg_confidence": symbol_df["rescue_confidence"].mean(),
                "avg_drawdown": symbol_df["deviation_pct"].mean(),
                "avg_volume": symbol_df["volume"].mean(),
                "profitability_score": self._calculate_profitability_score(symbol_df),
            }

        return symbol_analysis

    def generate_optimization_report(self, days: int = 7) -> str:
        """Generate comprehensive optimization report"""
        analysis = self.analyze_recent_trades(days)
        symbol_analysis = self.analyze_by_symbol(days)

        report = f"""
# Smart DCA Profitability Analysis Report
Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
Analysis Period: {days} days

## Overall Performance
- Total Trades: {analysis.get('total_trades', 0)}
- Rescue Rate: {analysis.get('rescue_rate', 0):.1f}%
- Average Confidence: {analysis.get('avg_confidence', 0):.2f}
- Average Drawdown: {analysis.get('avg_drawdown', 0):.1f}%
- Average Volume: {analysis.get('avg_volume', 0):.1f} USDT
- Profitability Score: {analysis.get('profitability_score', 0):.1f}/100

## Recommendations
"""

        for i, rec in enumerate(analysis.get("recommendations", []), 1):
            report += f"{i}. {rec}\n"

        report += "\n## Symbol Performance\n"
        for symbol, data in symbol_analysis.items():
            if isinstance(data, dict) and "profitability_score" in data:
                report += f"- {symbol}: {data['profitability_score']:.1f}/100 (Rescue: {data['rescue_rate']:.1f}%)\n"

        return report


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze DCA profitability")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    parser.add_argument("--output", type=str, help="Output file for report")

    args = parser.parse_args()

    log_dir = Path("dca/logs")
    analyzer = ProfitabilityAnalyzer(log_dir)

    report = analyzer.generate_optimization_report(args.days)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
