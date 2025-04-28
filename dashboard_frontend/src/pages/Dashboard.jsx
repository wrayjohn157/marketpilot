import React from "react";
import TradeCardEnhanced from "../components/ui/TradeCardEnhanced";

export default function Dashboard() {
  return (
    <div className="p-6 text-white bg-gray-900 min-h-screen space-y-6">
      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="p-4">
            <h2 className="text-xl font-semibold mb-2">Account Summary</h2>
            <p className="text-2xl font-bold">$25,600</p>
            <div className="mt-2 text-sm text-gray-400">5 Active Trades</div>
            <div className="text-sm text-green-400">+1.4% Today</div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="p-4">
            <h2 className="text-xl font-semibold mb-2">BTC Sentiment</h2>
            <div className="text-green-400 text-2xl font-bold">SAFE ✅</div>
            <div className="mt-2 text-sm text-gray-400">RSI: 52.6 | ADX: 37.1</div>
            <div className="text-sm">📈 Above EMA50</div>
          </CardContent>
        </Card>

        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="p-4">
            <h2 className="text-xl font-semibold mb-2">AI/ML Confidence</h2>
            <ul className="space-y-2">
              <li className="flex justify-between">
                <span>USDT.ETC</span>
                <span className="text-green-400">0.79</span>
              </li>
              <li className="flex justify-between">
                <span>USDT.SOL</span>
                <span className="text-yellow-400">0.76</span>
              </li>
              <li className="flex justify-between">
                <span>USDT.BTC</span>
                <span className="text-red-400">0.63</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Active Trades Table */}
      <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Active Trades</h2>
        <table className="w-full text-sm text-left text-gray-300">
          <thead className="text-xs text-gray-400 uppercase border-b border-gray-700">
            <tr>
              <th className="px-4 py-2">Symbol</th>
              <th>Status</th>
              <th>Score</th>
              <th>Confidence</th>
              <th>DCA Step</th>
              <th>Budget</th>
              <th>PnL</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-700">
              <td className="px-4 py-2">USDT.ETC</td>
              <td className="text-green-400">Active</td>
              <td>0.89</td>
              <td className="text-green-400">RUN</td>
              <td>3</td>
              <td>$340</td>
              <td className="text-red-400">-$120</td>
            </tr>
            <tr>
              <td className="px-4 py-2">USDT.SOL</td>
              <td className="text-green-400">Active</td>
              <td>0.84</td>
              <td className="text-green-300">QK</td>
              <td>2</td>
              <td>$80</td>
              <td className="text-green-400">+$10</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
