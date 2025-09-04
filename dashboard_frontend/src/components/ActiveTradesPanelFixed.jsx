import React, { useState, useEffect, useMemo } from "react";
import TradeCardEnhanced from "./ui/TradeCardEnhanced";
import SelectFilter from "./ui/SelectFilter";
import apiClient from "../lib/api";

export default function ActiveTradesPanelFixed() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState("pnl");

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
        console.error("Error loading active trades:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTrades();
    
    // Refresh every 30 seconds
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

  const sortOptions = [
    { label: "PnL", value: "pnl" },
    { label: "Confidence", value: "confidence" },
    { label: "Drawdown", value: "drawdown" },
    { label: "DCA Step", value: "dca" },
  ];

  if (loading) {
    return (
      <div>
        <div className="mb-4 max-w-xs">
          <SelectFilter
            label="Sort By"
            options={sortOptions}
            value={sortBy}
            onChange={setSortBy}
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-900 rounded-xl p-6 border border-gray-800 animate-pulse">
              <div className="h-4 bg-gray-700 rounded mb-4"></div>
              <div className="h-8 bg-gray-700 rounded mb-4"></div>
              <div className="grid grid-cols-2 gap-4">
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-700 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-400 mb-4">
          Error loading trades: {error}
        </div>
        <button 
          onClick={() => window.location.reload()} 
          className="text-blue-400 hover:text-blue-300"
        >
          Retry
        </button>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-400 mb-4">
          No active trades found
        </div>
        <div className="text-sm text-gray-500">
          Trades will appear here when they are active
        </div>
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

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
        {sortedTrades.map((trade) => (
          <TradeCardEnhanced key={`${sortBy}-${trade.deal_id}`} trade={trade} />
        ))}
      </div>
    </div>
  );
}