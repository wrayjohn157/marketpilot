import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Progress } from './ui/Progress';

const ResultsPanel = ({
  simulationResult = null,
  isRunning = false,
  onExportResults = () => {}
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!simulationResult && !isRunning) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-400">
            <div className="text-4xl mb-4">📊</div>
            <div>No simulation results yet</div>
            <div className="text-sm">Run a simulation to see results here</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isRunning) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="text-4xl mb-4">⏳</div>
            <div className="text-lg mb-2">Running Simulation...</div>
            <div className="text-sm text-gray-400 mb-4">This may take a few minutes</div>
            <Progress value={50} className="w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const { simulation_summary, dca_metrics, performance_metrics, dca_points } = simulationResult;

  // Calculate additional metrics
  const totalDCAValue = dca_points?.reduce((sum, point) => sum + point.volume_usdt, 0) || 0;
  const avgDCAPrice = dca_points?.reduce((sum, point) => sum + point.price, 0) / dca_points?.length || 0;
  const dcaSuccessRate = dca_points?.filter(point => point.drawdown_pct < 0).length / dca_points?.length * 100 || 0;

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
        {['overview', 'dca', 'performance', 'timeline'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-400">
                {performance_metrics?.final_pnl_pct?.toFixed(2) || '0.00'}%
              </div>
              <p className="text-sm text-gray-400">Final P&L</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-400">
                {dca_metrics?.total_dca_count || 0}
              </div>
              <p className="text-sm text-gray-400">DCA Orders</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-purple-400">
                ${dca_metrics?.total_spent?.toFixed(0) || '0'}
              </div>
              <p className="text-sm text-gray-400">Total Spent</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-orange-400">
                {performance_metrics?.max_drawdown?.toFixed(2) || '0.00'}%
              </div>
              <p className="text-sm text-gray-400">Max Drawdown</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-cyan-400">
                {dcaSuccessRate.toFixed(1)}%
              </div>
              <p className="text-sm text-gray-400">DCA Success Rate</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-yellow-400">
                ${avgDCAPrice.toFixed(2)}
              </div>
              <p className="text-sm text-gray-400">Avg DCA Price</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-red-400">
                {performance_metrics?.risk_score?.toFixed(2) || '0.00'}
              </div>
              <p className="text-sm text-gray-400">Risk Score</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-indigo-400">
                {simulation_summary?.simulation_duration_hours?.toFixed(1) || '0.0'}h
              </div>
              <p className="text-sm text-gray-400">Duration</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* DCA Tab */}
      {activeTab === 'dca' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>DCA Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3">Volume Distribution</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Total DCA Volume:</span>
                      <span>${totalDCAValue.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Average DCA Size:</span>
                      <span>${(totalDCAValue / (dca_metrics?.total_dca_count || 1)).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>DCA Efficiency:</span>
                      <span>{dca_metrics?.dca_efficiency?.toFixed(1) || '0.0'}%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">Price Analysis</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Entry Price:</span>
                      <span>${simulation_summary?.entry_price?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Final Price:</span>
                      <span>${simulation_summary?.final_price?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Average Price:</span>
                      <span>${dca_metrics?.average_price?.toFixed(2) || '0.00'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {dca_points && dca_points.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>DCA Points Detail</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-700">
                        <th className="text-left py-2">#</th>
                        <th className="text-left py-2">Time</th>
                        <th className="text-left py-2">Price</th>
                        <th className="text-left py-2">Volume</th>
                        <th className="text-left py-2">Confidence</th>
                        <th className="text-left py-2">Drawdown</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dca_points.map((point, index) => (
                        <tr key={index} className="border-b border-gray-800">
                          <td className="py-2">{point.dca_count}</td>
                          <td className="py-2">
                            {new Date(point.timestamp).toLocaleString()}
                          </td>
                          <td className="py-2">${point.price.toFixed(2)}</td>
                          <td className="py-2">${point.volume_usdt.toFixed(2)}</td>
                          <td className="py-2">
                            <span className={`px-2 py-1 rounded text-xs ${
                              point.confidence > 0.7 ? 'bg-green-600' :
                              point.confidence > 0.5 ? 'bg-yellow-600' : 'bg-red-600'
                            }`}>
                              {(point.confidence * 100).toFixed(0)}%
                            </span>
                          </td>
                          <td className="py-2">
                            <span className={point.drawdown_pct < 0 ? 'text-red-400' : 'text-green-400'}>
                              {point.drawdown_pct.toFixed(2)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3">Profit & Loss</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Final P&L:</span>
                      <span className={performance_metrics?.final_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {performance_metrics?.final_pnl_pct?.toFixed(2) || '0.00'}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Entry P&L:</span>
                      <span className={performance_metrics?.entry_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {performance_metrics?.entry_pnl_pct?.toFixed(2) || '0.00'}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Current Drawdown:</span>
                      <span className="text-red-400">
                        {performance_metrics?.current_drawdown?.toFixed(2) || '0.00'}%
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">Risk Metrics</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Risk Score:</span>
                      <span className={performance_metrics?.risk_score < 0.5 ? 'text-green-400' : 'text-red-400'}>
                        {performance_metrics?.risk_score?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Max Drawdown:</span>
                      <span className="text-red-400">
                        {performance_metrics?.max_drawdown?.toFixed(2) || '0.00'}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>DCA Success Rate:</span>
                      <span className="text-blue-400">
                        {dcaSuccessRate.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Performance Visualization</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center text-gray-400 py-8">
                <div className="text-4xl mb-4">📈</div>
                <div>Performance charts will be displayed here</div>
                <div className="text-sm">Coming soon in future updates</div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Timeline Tab */}
      {activeTab === 'timeline' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Simulation Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
                  <div>
                    <div className="font-medium">Simulation Started</div>
                    <div className="text-sm text-gray-400">
                      {new Date(simulation_summary?.entry_time).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-green-400">✓</div>
                </div>

                {dca_points && dca_points.map((point, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-800 rounded">
                    <div>
                      <div className="font-medium">DCA #{point.dca_count}</div>
                      <div className="text-sm text-gray-400">
                        {new Date(point.timestamp).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-400">
                        Price: ${point.price.toFixed(2)} | Volume: ${point.volume_usdt.toFixed(2)}
                      </div>
                    </div>
                    <div className="text-blue-400">DCA</div>
                  </div>
                ))}

                <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
                  <div>
                    <div className="font-medium">Simulation Completed</div>
                    <div className="text-sm text-gray-400">
                      {new Date(simulation_summary?.entry_time + (simulation_summary?.simulation_duration_hours * 60 * 60 * 1000)).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-green-400">✓</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Export Button */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex justify-end">
            <Button onClick={onExportResults} variant="outline">
              Export Results
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResultsPanel;
