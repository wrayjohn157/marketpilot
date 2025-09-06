import React from "react";
import { TrendingUp, TrendingDown, DollarSign, AlertTriangle, Target, BarChart3, RefreshCw, X } from "lucide-react";

export default function TradeCardEnhanced({ trade, onRefresh, onSell, isRefreshing = false }) {
  const {
    deal_id,
    symbol,
    pair = symbol, // Use symbol as fallback for pair
    open_pnl,
    open_pnl_pct,
    drawdown_pct = 0, // Default to 0 if not provided
    drawdown_usd = 0, // Default to 0 if not provided
    step,
    confidence_score,
    spent_amount,
    current_price,
    entry_price = trade.avg_entry_price, // Map avg_entry_price to entry_price
    bought_amount
  } = trade;

  const isProfit = open_pnl >= 0;
  const isHighDrawdown = drawdown_pct > 10;
  const isHighConfidence = confidence_score > 0.7;

  // Calculate actual PnL percentage if not provided
  const actualPnlPct = open_pnl_pct !== undefined ? open_pnl_pct :
    ((current_price - entry_price) / entry_price) * 100;

  // Calculate actual drawdown if not provided
  const actualDrawdownPct = drawdown_pct !== 0 ? drawdown_pct :
    Math.max(0, ((entry_price - current_price) / entry_price) * 100);

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

  // Calculate price distance bar
  const priceRange = Math.abs(current_price - entry_price);
  const maxRange = Math.max(priceRange, entry_price * 0.05); // At least 5% range
  const barPosition = Math.min(100, (priceRange / maxRange) * 100);
  const isAboveEntry = current_price > entry_price;

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-all duration-200">
      {/* Header - Fixed ticker redundancy */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <h3 className="text-lg font-semibold text-white">{symbol}</h3>
        </div>
        <div className="flex items-center gap-2">
          {isHighConfidence && (
            <div className="w-2 h-2 rounded-full bg-green-400" title="High Confidence"></div>
          )}
          {isHighDrawdown && (
            <AlertTriangle className="w-4 h-4 text-red-400" title="High Drawdown" />
          )}
          {/* Individual refresh button */}
          <button
            onClick={() => onRefresh && onRefresh(deal_id)}
            disabled={isRefreshing}
            className={`p-1.5 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors ${
              isRefreshing ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            title="Refresh trade data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* PnL Section - Fixed percentage display */}
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
            {formatPercentage(actualPnlPct)}
          </span>
        </div>
      </div>

      {/* Price Distance Bar - 3Commas style */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
          <span>Entry: {formatCurrency(entry_price)}</span>
          <span>Current: {formatCurrency(current_price)}</span>
        </div>
        <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className="absolute inset-0 flex">
            {/* Entry price marker */}
            <div className="w-1 bg-gray-600"></div>
            {/* Price range bar */}
            <div className="flex-1 relative">
              {/* Current price indicator */}
              <div
                className={`absolute top-0 w-1 h-full ${
                  isAboveEntry ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{
                  left: `${isAboveEntry ? Math.min(95, barPosition) : Math.max(5, 100 - barPosition)}%`
                }}
              ></div>
              {/* Background gradient */}
              <div className={`absolute inset-0 ${
                isAboveEntry
                  ? 'bg-gradient-to-r from-gray-700 to-green-900'
                  : 'bg-gradient-to-r from-red-900 to-gray-700'
              }`}></div>
            </div>
          </div>
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>BE: {formatCurrency(entry_price)}</span>
          <span className={isProfit ? "text-green-400" : "text-red-400"}>
            {isProfit ? "+" : ""}{formatCurrency(open_pnl)}
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
          <div className={`text-sm font-medium ${getDrawdownColor(actualDrawdownPct)}`}>
            {formatPercentage(actualDrawdownPct)}
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
          ID: {deal_id ? String(deal_id).slice(-6) : "N/A"}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-800">
        <div className="flex items-center gap-2">
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

        {/* Panic Sell Button */}
        <button
          onClick={() => onSell && onSell(deal_id)}
          className="flex items-center gap-1 px-3 py-1.5 bg-red-900 hover:bg-red-800 text-red-300 hover:text-red-200 rounded-lg transition-colors text-sm font-medium"
        >
          <X className="w-4 h-4" />
          Panic Sell
        </button>
      </div>
    </div>
  );
}
