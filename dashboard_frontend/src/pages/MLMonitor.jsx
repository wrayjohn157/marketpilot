import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import LoadingSpinner from "../components/layout/LoadingSpinner";

export default function MLMonitor() {
  const [mlData, setMlData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMLData = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/ml/status");
        if (!response.ok) throw new Error("Failed to fetch ML data");
        const data = await response.json();
        setMlData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMLData();
    const interval = setInterval(fetchMLData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">🤖 ML Monitor</h2>
        <LoadingSpinner text="Loading ML status..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">🤖 ML Monitor</h2>
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 text-red-400">
          Error: {error}
        </div>
      </div>
    );
  }

  const models = mlData?.models || [];
  const predictions = mlData?.predictions || [];

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold mb-4">🤖 ML Monitor</h2>
      
      {/* Model Status */}
      <Card>
        <CardHeader>
          <CardTitle>Model Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model, index) => (
              <div key={index} className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{model.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs ${
                    model.status === 'active' ? 'bg-green-900 text-green-400' : 'bg-red-900 text-red-400'
                  }`}>
                    {model.status}
                  </span>
                </div>
                <div className="text-sm text-gray-400">
                  <div>Accuracy: {(model.accuracy * 100).toFixed(1)}%</div>
                  <div>Last Updated: {new Date(model.lastUpdated).toLocaleString()}</div>
                  <div>Version: {model.version}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Predictions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Predictions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {predictions.length > 0 ? (
              predictions.map((prediction, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{prediction.symbol}</span>
                    <span className="text-sm text-gray-400">
                      {new Date(prediction.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-400">Confidence</div>
                      <div className="font-semibold">{(prediction.confidence * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Recovery Odds</div>
                      <div className="font-semibold">{(prediction.recoveryOdds * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-gray-400">SAFU Score</div>
                      <div className="font-semibold">{prediction.safuScore.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">DCA Spend</div>
                      <div className="font-semibold">${prediction.dcaSpend.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-400 py-8">
                No recent predictions available
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* ML Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-400">
                {mlData?.metrics?.totalPredictions || 0}
              </div>
              <div className="text-sm text-gray-400">Total Predictions</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-400">
                {(mlData?.metrics?.averageAccuracy * 100 || 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-400">Average Accuracy</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {mlData?.metrics?.activeModels || 0}
              </div>
              <div className="text-sm text-gray-400">Active Models</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}