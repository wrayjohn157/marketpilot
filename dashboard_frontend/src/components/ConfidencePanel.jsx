import { useEffect, useState } from "react";
import { Card, CardContent } from "./ui/Card";
import apiClient from "../lib/api";

export default function ConfidencePanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await apiClient.getMLConfidence();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch ML confidence:', error);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const getConfidenceColor = (percentage) => {
    if (percentage >= 80) return "text-green-400";
    if (percentage >= 60) return "text-yellow-400";
    return "text-red-400";
  };

  const getStatusColor = (status) => {
    if (status === "healthy") return "text-green-400";
    if (status === "warning") return "text-yellow-400";
    return "text-red-400";
  };

  if (loading) {
    return (
      <Card className="bg-gray-900 border border-gray-200 p-4">
        <h2 className="text-white text-base font-semibold mb-3">AI/ML Confidence</h2>
        <CardContent>
          <p className="text-gray-500 text-sm">Loading...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gray-900 border border-gray-200 p-4">
      <h2 className="text-white text-base font-semibold mb-3">AI/ML Confidence</h2>
      <CardContent className="space-y-3">
        {data && !data.error ? (
          <>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">Overall Confidence</span>
              <span className={`text-lg font-bold ${getConfidenceColor(data.confidence_percentage)}`}>
                {data.confidence_percentage?.toFixed(1)}%
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">Model Status</span>
              <span className={`text-sm font-medium ${getStatusColor(data.status)}`}>
                {data.status?.toUpperCase()}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">Active Trades</span>
              <span className="text-white text-sm">
                {data.active_trades || 0}
              </span>
            </div>

            <div className="pt-2 border-t border-gray-800">
              <span className="text-xs text-gray-500">
                Model: {data.model_version} • Updated: {data.last_updated ? new Date(data.last_updated).toLocaleTimeString() : 'Unknown'}
              </span>
            </div>
          </>
        ) : (
          <p className="text-gray-500 text-sm">
            {data?.error || "Failed to load confidence data"}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
