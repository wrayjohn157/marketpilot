import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import LoadingSpinner from "../components/layout/LoadingSpinner";

export default function ScanReview() {
  const [scanData, setScanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all');

  useEffect(() => {
    const fetchScanData = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/scan/results");
        if (!response.ok) throw new Error("Failed to fetch scan data");
        const data = await response.json();
        setScanData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchScanData();
    const interval = setInterval(fetchScanData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">📈 Market Scan Review</h2>
        <LoadingSpinner text="Loading scan results..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-4">📈 Market Scan Review</h2>
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 text-red-400">
          Error: {error}
        </div>
      </div>
    );
  }

  const scans = scanData?.scans || [];
  const filteredScans = selectedFilter === 'all' 
    ? scans 
    : scans.filter(scan => scan.status === selectedFilter);

  const getStatusColor = (status) => {
    switch (status) {
      case 'bullish': return 'text-green-400 bg-green-900/20';
      case 'bearish': return 'text-red-400 bg-red-900/20';
      case 'neutral': return 'text-yellow-400 bg-yellow-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold mb-4">📈 Market Scan Review</h2>
      
      {/* Scan Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Scan Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-400">
                {scans.length}
              </div>
              <div className="text-sm text-gray-400">Total Scans</div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-400">
                {scans.filter(s => s.status === 'bullish').length}
              </div>
              <div className="text-sm text-gray-400">Bullish</div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-400">
                {scans.filter(s => s.status === 'bearish').length}
              </div>
              <div className="text-sm text-gray-400">Bearish</div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {scans.filter(s => s.status === 'neutral').length}
              </div>
              <div className="text-sm text-gray-400">Neutral</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {['all', 'bullish', 'bearish', 'neutral'].map(filter => (
              <button
                key={filter}
                onClick={() => setSelectedFilter(filter)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedFilter === filter
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {filter.charAt(0).toUpperCase() + filter.slice(1)}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Scan Results */}
      <Card>
        <CardHeader>
          <CardTitle>Scan Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredScans.length > 0 ? (
              filteredScans.map((scan, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-semibold">{scan.symbol}</span>
                      <span className={`px-2 py-1 rounded text-xs ${getStatusColor(scan.status)}`}>
                        {scan.status}
                      </span>
                    </div>
                    <div className="text-sm text-gray-400">
                      {new Date(scan.timestamp).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-400">Price</div>
                      <div className="font-semibold">${scan.price?.toFixed(4) || "N/A"}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Score</div>
                      <div className="font-semibold">{scan.score?.toFixed(2) || "N/A"}</div>
                    </div>
                    <div>
                      <div className="text-gray-400">Volume</div>
                      <div className="font-semibold">
                        {scan.volume ? (scan.volume / 1000000).toFixed(1) + "M" : "N/A"}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400">Change 24h</div>
                      <div className={`font-semibold ${(scan.change_24h || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {scan.change_24h ? scan.change_24h.toFixed(2) + "%" : "N/A"}
                      </div>
                    </div>
                  </div>
                  
                  {scan.indicators && (
                    <div className="mt-3 pt-3 border-t border-gray-700">
                      <div className="text-sm text-gray-400 mb-2">Key Indicators:</div>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(scan.indicators).map(([key, value]) => (
                          <span key={key} className="px-2 py-1 bg-gray-700 rounded text-xs">
                            {key}: {typeof value === 'number' ? value.toFixed(2) : value}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {scan.notes && (
                    <div className="mt-3 pt-3 border-t border-gray-700">
                      <div className="text-sm text-gray-400">{scan.notes}</div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center text-gray-400 py-8">
                No scan results available
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Scan Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Scan Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Average Score</div>
              <div className="text-xl font-bold">
                {scanData?.stats?.avg_score ? scanData.stats.avg_score.toFixed(2) : "N/A"}
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Success Rate</div>
              <div className="text-xl font-bold">
                {scanData?.stats?.success_rate ? (scanData.stats.success_rate * 100).toFixed(1) + "%" : "N/A"}
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Last Updated</div>
              <div className="text-xl font-bold">
                {scanData?.last_updated ? new Date(scanData.last_updated).toLocaleTimeString() : "N/A"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}