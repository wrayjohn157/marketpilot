import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import LoadingSpinner from "../components/layout/LoadingSpinner";

export default function BacktestSummary() {
  const [backtestData, setBacktestData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBacktestData = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/backtest/summary");
        if (!response.ok) throw new Error("Failed to fetch backtest data");
        const data = await response.json();
        setBacktestData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBacktestData();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">📚 Backtest Summary</h2>
        <LoadingSpinner text="Loading backtest data..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">📚 Backtest Summary</h2>
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 text-red-400">
          Error: {error}
        </div>
      </div>
    );
  }

  const summary = backtestData?.summary || {};
  const strategies = backtestData?.strategies || [];

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold mb-4">📚 Backtest Summary</h2>

      {/* Overall Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-400">
                {summary.total_return ? (summary.total_return * 100).toFixed(1) + "%" : "N/A"}
              </div>
              <div className="text-sm text-gray-400">Total Return</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-400">
                {summary.sharpe_ratio ? summary.sharpe_ratio.toFixed(2) : "N/A"}
              </div>
              <div className="text-sm text-gray-400">Sharpe Ratio</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {summary.max_drawdown ? (summary.max_drawdown * 100).toFixed(1) + "%" : "N/A"}
              </div>
              <div className="text-sm text-gray-400">Max Drawdown</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-purple-400">
                {summary.win_rate ? (summary.win_rate * 100).toFixed(1) + "%" : "N/A"}
              </div>
              <div className="text-sm text-gray-400">Win Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {strategies.length > 0 ? (
              strategies.map((strategy, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold">{strategy.name}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${
                      strategy.performance > 0 ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'
                    }`}>
                      {(strategy.performance * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-400">Trades</div>
                      <div className="font-semibold">{strategy.total_trades || 0}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Win Rate</div>
                      <div className="font-semibold">
                        {strategy.win_rate ? (strategy.win_rate * 100).toFixed(1) + "%" : "N/A"}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400">Avg Return</div>
                      <div className="font-semibold">
                        {strategy.avg_return ? (strategy.avg_return * 100).toFixed(2) + "%" : "N/A"}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400">Max DD</div>
                      <div className="font-semibold">
                        {strategy.max_drawdown ? (strategy.max_drawdown * 100).toFixed(1) + "%" : "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-400 py-8">
                No strategy data available
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Volatility</div>
              <div className="text-xl font-bold">
                {summary.volatility ? (summary.volatility * 100).toFixed(2) + "%" : "N/A"}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">VaR (95%)</div>
              <div className="text-xl font-bold">
                {summary.var_95 ? (summary.var_95 * 100).toFixed(2) + "%" : "N/A"}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Calmar Ratio</div>
              <div className="text-xl font-bold">
                {summary.calmar_ratio ? summary.calmar_ratio.toFixed(2) : "N/A"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Trades */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {backtestData?.recent_trades?.length > 0 ? (
              backtestData.recent_trades.slice(0, 10).map((trade, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-800 rounded-lg p-3">
                  <div className="flex items-center gap-3">
                    <span className="font-semibold">{trade.symbol}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      trade.result === 'win' ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'
                    }`}>
                      {trade.result}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    {trade.return ? (trade.return * 100).toFixed(2) + "%" : "N/A"}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-400 py-4">
                No recent trades available
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
