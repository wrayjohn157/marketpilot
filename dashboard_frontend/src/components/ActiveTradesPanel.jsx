import React, { useState, useEffect, useMemo } from "react";
import TradeCardEnhanced from "../components/ui/TradeCardEnhanced";
import SelectFilter from "../components/ui/SelectFilter";
import apiClient from "../lib/api";

export default function ActiveTradesPanel() {
  const [trades, setTrades] = useState([]);
  const [sortBy, setSortBy] = useState("pnl");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(new Set());

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getActiveTrades();

        if (data.error) {
          setError(data.error);
        } else {
          setTrades(data.dca_trades || []);
        }
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch trades:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTrades();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchTrades, 30000);
    return () => clearInterval(interval);
  }, []);

  const sortedTrades = useMemo(() => {
    switch (sortBy) {
      case "pnl":
        return [...trades].sort((a, b) => (b.open_pnl || 0) - (a.open_pnl || 0));
      case "drawdown":
        return [...trades].sort((a, b) => (b.drawdown_pct || 0) - (a.drawdown_pct || 0));
      case "dca":
        return [...trades].sort((a, b) => (b.step || 0) - (a.step || 0));
      case "confidence":
      default:
        return [...trades].sort((a, b) => (b.confidence_score || 0) - (a.confidence_score || 0));
    }
  }, [trades, sortBy]);

  const handleRefreshTrade = async (dealId) => {
    try {
      setRefreshing(prev => new Set(prev).add(dealId));
      await apiClient.refreshPrice(dealId);
      // Refresh all trades after individual refresh
      const data = await apiClient.getActiveTrades();
      setTrades(data.dca_trades || []);
    } catch (err) {
      console.error('Failed to refresh trade:', err);
    } finally {
      setRefreshing(prev => {
        const newSet = new Set(prev);
        newSet.delete(dealId);
        return newSet;
      });
    }
  };

  const handleSellTrade = async (dealId) => {
    if (!window.confirm('Are you sure you want to panic sell this trade?')) {
      return;
    }

    try {
      await apiClient.panicSell(dealId);
      // Refresh trades after sell
      const data = await apiClient.getActiveTrades();
      setTrades(data.dca_trades || []);
    } catch (err) {
      console.error('Failed to sell trade:', err);
      alert('Failed to sell trade: ' + err.message);
    }
  };

  const sortOptions = [
    { label: "PnL", value: "pnl" },
    { label: "Confidence", value: "confidence" },
    { label: "Drawdown", value: "drawdown" },
    { label: "DCA Step", value: "dca" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-400">Loading active trades...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <div className="text-red-400">Error loading trades: {error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4 max-w-xs">
        <SelectFilter
          label="Sort By"
          options={sortOptions}
          value={sortBy}
          onChange={(val) => {
            console.log("Sort mode changed to:", val);
            setSortBy(val);
          }}
        />
      </div>

      {sortedTrades.length === 0 ? (
        <div className="text-center text-gray-400 p-8">
          No active trades found
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
          {sortedTrades.map((trade) => (
            <TradeCardEnhanced
              key={`${sortBy}-${trade.deal_id}`}
              trade={trade}
              onRefresh={handleRefreshTrade}
              onSell={handleSellTrade}
              isRefreshing={refreshing.has(trade.deal_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
