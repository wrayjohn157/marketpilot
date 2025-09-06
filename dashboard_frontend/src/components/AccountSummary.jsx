import { useEffect, useState } from "react";
import apiClient from "../lib/api";

export default function AccountSummary() {
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
        setError(err.message);
        console.error("Error loading account summary:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, []);

  const normalizeTo = 24957;

  const formatUSD = (value) => {
    return value?.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    });
  };

  const getTodayChangePct = () => {
    if (!summary?.balance || !summary?.today_pnl) return "0.00%";
    const pct = (summary.today_pnl / summary.balance) * 100;
    return `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`;
  };

  const getNormalizedBalance = () => {
    if (!summary) return 0;
    return normalizeTo + summary.total_pnl;
  };

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold mb-2 text-white">Account Summary</h3>
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold mb-2 text-white">Account Summary</h3>
        <div className="text-red-400">Error: {error}</div>
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
