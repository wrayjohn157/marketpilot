import React from "react";
import MarketSentiment from "../components/MarketSentiment";
import AccountSummary from "../components/AccountSummary";
import ConfidencePanel from "../components/ConfidencePanel";
import ActiveTradesPanel from "../components/ActiveTradesPanel"; // ✅ Enhanced Panel

export default function TradeDashboard() {
  return (
    <div className="p-4 md:p-6">
      <h1 className="text-2xl md:text-4xl font-bold mb-6 flex items-center gap-2">
        <span role="img" aria-label="chart">📈</span> Market 5.0 Dashboard
      </h1>

      {/* Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <AccountSummary />
        <MarketSentiment />
        <ConfidencePanel />
      </div>

      {/* Trade Cards */}
      <div className="mt-8">
        <ActiveTradesPanel /> {/* ✅ Renders Enhanced Trade Cards */}
      </div>
    </div>
  );
}
