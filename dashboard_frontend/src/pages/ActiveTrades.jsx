import React from "react";
import TradeTable from "../components/TradeTable";

export default function ActiveTrades() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold mb-4">📊 Active Trades</h2>
      <TradeTable />
    </div>
  );
}
