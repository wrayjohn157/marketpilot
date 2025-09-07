import React from "react";
import { TrendingUp, TrendingDown, DollarSign, AlertTriangle, Target, BarChart3 } from "lucide-react";

export default function TradeCardEnhanced({ trade }) {
  const {
    deal_id,
    symbol,
    pair,
    open_pnl,
    open_pnl_pct,
    drawdown_pct,
    drawdown_usd,
    step,
    confidence_score,
    spent_amount,
    current_price,
    entry_price
  } = trade;

  const isProfit = open_pnl >= 0;
  const isHighDrawdown = drawdown_pct > 10;
  const isHighConfidence = confidence_score > 0.7;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value || 0);
  };

  const formatPercentage = (value) => {
    return `${(value || 0).toFixed(2)}%`;
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return "text-green-400";
    if (score >= 0.6) return "text-yellow-400";
    return "text-red-400";
  };

  const getDrawdownColor = (pct) => {
    if (pct <= 5) return "text-green-400";
    if (pct <= 10) return "text-yellow-400";
    return "text-red-400";
  };

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-all duration-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <h3 className="text-lg font-semibold text-white">{symbol}</h3>
          <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
            {pair}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {isHighConfidence && (
            <div className="w-2 h-2 rounded-full bg-green-400" title="High Confidence"></div>
          )}
          {isHighDrawdown && (
            <AlertTriangle className="w-4 h-4 text-red-400" title="High Drawdown" />
          )}
        </div>
      </div>

      {/* PnL Section */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">Unrealized P&L</span>
          <div className={`flex items-center gap-1 ${isProfit ? "text-green-400" : "text-red-400"}`}>
            {isProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span className="font-semibold">{formatCurrency(open_pnl)}</span>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-sm font-medium ${isProfit ? "text-green-400" : "text-red-400"}`}>
            {formatPercentage(open_pnl_pct)}
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <DollarSign className="w-3 h-3" />
            <span>Entry Price</span>
          </div>
          <div className="text-sm font-medium text-white">
            {formatCurrency(entry_price)}
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <DollarSign className="w-3 h-3" />
            <span>Current Price</span>
          </div>
          <div className="text-sm font-medium text-white">
            {formatCurrency(current_price)}
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <BarChart3 className="w-3 h-3" />
            <span>Drawdown</span>
          </div>
          <div className={`text-sm font-medium ${getDrawdownColor(drawdown_pct)}`}>
            {formatPercentage(drawdown_pct)}
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <Target className="w-3 h-3" />
            <span>DCA Step</span>
          </div>
          <div className="text-sm font-medium text-white">
            {step || 0}
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-800">
        <div className="space-y-1">
          <div className="text-xs text-gray-400">Confidence</div>
          <div className={`text-sm font-medium ${getConfidenceColor(confidence_score)}`}>
            {formatPercentage(confidence_score * 100)}
          </div>
        </div>

        <div className="space-y-1">
          <div className="text-xs text-gray-400">Invested</div>
          <div className="text-sm font-medium text-white">
            {formatCurrency(spent_amount)}
          </div>
        </div>

        <div className="text-xs text-gray-500">
          ID: {deal_id ? String(deal_id) : "N/A"}
        </div>
      </div>

      {/* Status Indicators */}
      <div className="flex items-center gap-2 mt-3">
        {isHighConfidence && (
          <span className="text-xs bg-green-900 text-green-300 px-2 py-1 rounded">
            High Confidence
          </span>
        )}
        {isHighDrawdown && (
          <span className="text-xs bg-red-900 text-red-300 px-2 py-1 rounded">
            High Drawdown
          </span>
        )}
        {step > 3 && (
          <span className="text-xs bg-yellow-900 text-yellow-300 px-2 py-1 rounded">
            Deep DCA
          </span>
        )}
      </div>
    </div>
  );
}
