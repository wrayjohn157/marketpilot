import React, { useState, useEffect, useMemo } from "react";
import TradeCard from "../components/ui/TradeCardEnhanced";
import SelectFilter from "../components/ui/SelectFilter";
import apiClient from "../lib/api";

export default function ActiveTradesPanel() {
  const [trades, setTrades] = useState([]);
  const [sortBy, setSortBy] = useState("pnl");

  useEffect(() => {
    const fetchTrades = async () => {
      const data = await apiClient.getActiveTrades();
      setTrades(data.dca_trades || []);
    };
    fetchTrades();
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
        {sortedTrades.map((trade, index) => (
          <TradeCard key={`${sortBy}-${trade.symbol}-${index}`} trade={trade} />
        ))}
      </div>
    </div>
  );
}
