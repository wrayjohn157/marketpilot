import React, { useState, useEffect } from "react";
import TradeCard    from "../components/ui/TradeCardEnhanced";
import SelectFilter from "../components/ui/SelectFilter";

export default function ActiveTradesPanel() {
  const [trades, setTrades] = useState([]);
  const [sortBy, setSortBy] = useState("confidence");

  useEffect(() => {
    const fetchTrades = async () => {
      const res = await fetch("/dca-trades-active");
      const data = await res.json();
      setTrades(data.dca_trades || []);
    };
    fetchTrades();
  }, []);

  const sortTrades = (trades) => {
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
  };

  const sortedTrades = sortTrades(trades);

  const sortOptions = [
    { label: "Confidence", value: "confidence" },
    { label: "PnL", value: "pnl" },
    { label: "Drawdown", value: "drawdown" },
    { label: "DCA Step", value: "dca" }
  ];

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

      <div className="grid grid-cols-1 gap-4">
        {sortedTrades.map((trade) => (
          <TradeCard key={trade.deal_id} trade={trade} />
        ))}
      </div>
    </div>
  );
}
