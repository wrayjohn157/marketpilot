import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import LoadingSpinner from "../components/layout/LoadingSpinner";

export default function BTCRiskPanel() {
  const [btcData, setBtcData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBTCData = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/btc/context");
        if (!response.ok) throw new Error("Failed to fetch BTC data");
        const data = await response.json();
        setBtcData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBTCData();
    const interval = setInterval(fetchBTCData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">⚠️ BTC Risk Panel</h2>
        <LoadingSpinner text="Loading BTC data..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">⚠️ BTC Risk Panel</h2>
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 text-red-400">
          Error: {error}
        </div>
      </div>
    );
  }

  const getRiskLevel = (score) => {
    if (score >= 0.7) return { level: "High", color: "text-red-400", bg: "bg-red-900/20" };
    if (score >= 0.4) return { level: "Medium", color: "text-yellow-400", bg: "bg-yellow-900/20" };
    return { level: "Low", color: "text-green-400", bg: "bg-green-900/20" };
  };

  const riskLevel = getRiskLevel(btcData?.risk_score || 0);

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold mb-4">⚠️ BTC Risk Panel</h2>
      
      {/* Risk Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className={`rounded-lg p-4 ${riskLevel.bg} border ${riskLevel.color.includes('red') ? 'border-red-500' : riskLevel.color.includes('yellow') ? 'border-yellow-500' : 'border-green-500'}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className={`text-2xl font-bold ${riskLevel.color}`}>
                  {riskLevel.level} Risk
                </div>
                <div className="text-sm text-gray-400">
                  Risk Score: {(btcData?.risk_score * 100 || 0).toFixed(1)}%
                </div>
              </div>
              <div className="text-4xl">
                {riskLevel.level === "High" ? "🔴" : riskLevel.level === "Medium" ? "🟡" : "🟢"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* BTC Indicators */}
      <Card>
        <CardHeader>
          <CardTitle>BTC Indicators</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Price</div>
              <div className="text-xl font-bold">${btcData?.price?.toFixed(2) || "N/A"}</div>
              <div className={`text-sm ${(btcData?.price_change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(btcData?.price_change_24h || 0).toFixed(2)}% (24h)
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">RSI</div>
              <div className="text-xl font-bold">{btcData?.rsi?.toFixed(1) || "N/A"}</div>
              <div className="text-sm text-gray-400">
                {btcData?.rsi > 70 ? "Overbought" : btcData?.rsi < 30 ? "Oversold" : "Neutral"}
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">MACD</div>
              <div className="text-xl font-bold">{btcData?.macd?.toFixed(4) || "N/A"}</div>
              <div className="text-sm text-gray-400">
                {btcData?.macd > 0 ? "Bullish" : "Bearish"}
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Volume</div>
              <div className="text-xl font-bold">
                {btcData?.volume_24h ? (btcData.volume_24h / 1000000).toFixed(1) + "M" : "N/A"}
              </div>
              <div className="text-sm text-gray-400">24h Volume</div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Fear & Greed</div>
              <div className="text-xl font-bold">{btcData?.fear_greed_index || "N/A"}</div>
              <div className="text-sm text-gray-400">
                {btcData?.fear_greed_index > 75 ? "Extreme Greed" : 
                 btcData?.fear_greed_index > 55 ? "Greed" :
                 btcData?.fear_greed_index > 45 ? "Neutral" :
                 btcData?.fear_greed_index > 25 ? "Fear" : "Extreme Fear"}
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Market Cap</div>
              <div className="text-xl font-bold">
                {btcData?.market_cap ? "$" + (btcData.market_cap / 1000000000).toFixed(1) + "B" : "N/A"}
              </div>
              <div className="text-sm text-gray-400">Dominance</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trading Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Trading Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {btcData?.recommendations?.map((rec, index) => (
              <div key={index} className={`p-3 rounded-lg border ${
                rec.type === 'warning' ? 'bg-red-900/20 border-red-500 text-red-400' :
                rec.type === 'caution' ? 'bg-yellow-900/20 border-yellow-500 text-yellow-400' :
                'bg-green-900/20 border-green-500 text-green-400'
              }`}>
                <div className="flex items-start gap-2">
                  <span className="text-lg">
                    {rec.type === 'warning' ? '⚠️' : rec.type === 'caution' ? '⚡' : '✅'}
                  </span>
                  <div>
                    <div className="font-semibold">{rec.title}</div>
                    <div className="text-sm opacity-80">{rec.description}</div>
                  </div>
                </div>
              </div>
            )) || (
              <div className="text-center text-gray-400 py-4">
                No specific recommendations at this time
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}