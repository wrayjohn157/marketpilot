import React, { useEffect, useState } from "react";
import apiClient from "../lib/api";

export default function AccountSummaryFixed() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getAccountSummary();

        if (data.error) {
          setError(data.error);
        } else {
          setSummary(data.summary);
        }
      } catch (err) {
        console.error("Error loading account summary:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();

    // Refresh every 30 seconds
    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatUSD = (value) => {
    return value?.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }) || "$0.00";
  };

  const getTodayChangePct = () => {
    if (!summary?.balance || !summary?.today_pnl) return "0.00%";
    const pct = (summary.today_pnl / summary.balance) * 100;
    return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
  };

  const getNormalizedBalance = () => {
    if (!summary) return 0;
    return summary.balance;
  };

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold mb-2 text-white">Account Summary</h3>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded mb-4"></div>
          <div className="grid grid-cols-3 gap-2">
            <div className="h-4 bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold mb-2 text-white">Account Summary</h3>
        <div className="text-red-400 text-sm">
          Error: {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          className="mt-2 text-blue-400 hover:text-blue-300 text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h3 className="text-lg font-semibold mb-2 text-white">Account Summary</h3>

      <div className="text-3xl md:text-4xl font-bold text-white">
        {formatUSD(getNormalizedBalance())}
      </div>

      <div className="grid grid-cols-3 gap-2 text-sm mt-4 text-gray-300">
        <div className="text-center">
          <div className="text-white font-semibold">
            {summary?.active_trades ?? 0}
          </div>
          <div className="text-xs">Active</div>
        </div>

        <div className="text-center">
          <div className={`font-semibold ${summary?.today_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            {getTodayChangePct()}
          </div>
          <div className="text-xs">Today</div>
        </div>

        <div className="text-center">
          <div className="text-white font-semibold">
            {formatUSD(summary?.allocated ?? 0)}
          </div>
          <div className="text-xs">Allocated</div>
        </div>
      </div>

      {/* Optional Expanded PnL Metrics */}
      <div className="grid grid-cols-2 gap-2 text-xs mt-4 text-gray-400">
        <div className="text-left">uPnL: {formatUSD(summary?.upnl)}</div>
        <div className="text-right">Today's PnL: {formatUSD(summary?.today_pnl)}</div>
      </div>
    </div>
  );
}
