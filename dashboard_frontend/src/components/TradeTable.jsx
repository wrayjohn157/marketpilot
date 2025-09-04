import React, { useEffect, useState } from "react";

function TradeTable() {
  const [trades, setTrades] = useState([]);

  useEffect(() => {
    fetch("/api/fork/metrics")
      .then(res => res.json())
      .then((data) => {
        const deals = data?.metrics?.active_deals;
        setTrades(Array.isArray(deals) ? deals : []);
      })
      .catch((err) => {
        console.error("❌ Fetch error:", err);
        setTrades([]);
      });
  }, []);

  return (
    <div className="p-4 sm:p-6 overflow-x-auto">
      <h2 className="text-xl font-semibold mb-4">📊 Live Trades</h2>

      {/* Desktop Table View */}
      <div className="overflow-x-auto hidden lg:block">
        <table className="min-w-full table-auto border-collapse">
          <thead>
            <tr className="bg-gray-800 text-left text-sm">
              <th className="p-2">Symbol</th>
              <th className="p-2">Status</th>
              <th className="p-2">Fork Score</th>
              <th className="p-2">Confidence</th>
              <th className="p-2">Tags</th>
              <th className="p-2">DCA Step</th>
              <th className="p-2">Budget Used</th>
              <th className="p-2">Open PnL</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, idx) => (
              <tr key={idx} className="border-t border-gray-700 hover:bg-gray-800">
                <td className="p-2 font-medium">{trade.pair}</td>
                <td className="p-2 text-green-400">Active</td>
                <td className="p-2">—</td>
                <td className="p-2">—</td>
                <td className="p-2">—</td>
                <td className="p-2">—</td>
                <td className="p-2">${trade.spent_amount?.toFixed(0)}</td>
                <td className={`p-2 ${trade.open_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                  {trade.open_pnl?.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="lg:hidden space-y-4">
        {trades.map((trade, idx) => (
          <div key={idx} className="bg-gray-800 rounded-xl p-4 shadow-md">
            <div className="font-semibold text-lg">{trade.pair}</div>
            <div className="text-sm mt-1 text-green-400">Active</div>
            <div className="text-sm mt-2">💵 Budget: ${trade.spent_amount?.toFixed(0)}</div>
            <div className={`text-sm ${trade.open_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
              📈 Open PnL: {trade.open_pnl?.toFixed(2)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TradeTable;
