import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { FormField } from './ui/FormField';
import { Switch } from './ui/Switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select';

const ParameterPanel = ({
  parameters = {},
  onParametersChange = () => {},
  onRunSimulation = () => {},
  onRunOptimization = () => {},
  isRunning = false,
  optimizationResults = []
}) => {
  const [localParams, setLocalParams] = useState(parameters);
  const [optimizationType, setOptimizationType] = useState('grid_search');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Update local parameters when props change
  useEffect(() => {
    setLocalParams(parameters);
  }, [parameters]);

  // Handle parameter change
  const handleParameterChange = (key, value) => {
    const newParams = { ...localParams, [key]: value };
    setLocalParams(newParams);
    onParametersChange(newParams);
  };

  // Handle numeric input
  const handleNumericChange = (key, value) => {
    const numValue = parseFloat(value) || 0;
    handleParameterChange(key, numValue);
  };

  // Handle boolean input
  const handleBooleanChange = (key, value) => {
    handleParameterChange(key, value);
  };

  // Get parameter ranges for optimization
  const getParameterRanges = () => {
    return {
      confidence_threshold: [0.4, 0.5, 0.6, 0.7, 0.8],
      min_drawdown_pct: [1.0, 2.0, 3.0, 5.0, 7.0],
      rsi_oversold_threshold: [20, 25, 30, 35, 40],
      macd_histogram_threshold: [-0.005, -0.003, -0.001, -0.0005],
      min_volume_ratio: [0.5, 0.7, 0.8, 1.0, 1.2],
      base_dca_volume: [50, 100, 150, 200, 250],
      max_dca_volume: [200, 300, 500, 750, 1000],
      max_dca_count: [5, 7, 10, 12, 15],
      max_trade_usdt: [1000, 1500, 2000, 3000, 5000]
    };
  };

  // Run optimization
  const handleRunOptimization = () => {
    const parameterRanges = getParameterRanges();
    onRunOptimization(optimizationType, parameterRanges);
  };

  return (
    <div className="space-y-6">
      {/* Basic Parameters */}
      <Card>
        <CardHeader>
          <CardTitle>Basic DCA Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Confidence Threshold">
              <Input
                type="number"
                value={localParams.confidence_threshold || 0.6}
                onChange={(e) => handleNumericChange('confidence_threshold', e.target.value)}
                step="0.1"
                min="0"
                max="1"
              />
            </FormField>

            <FormField label="Min Drawdown %">
              <Input
                type="number"
                value={localParams.min_drawdown_pct || 2.0}
                onChange={(e) => handleNumericChange('min_drawdown_pct', e.target.value)}
                step="0.1"
                min="0"
                max="20"
              />
            </FormField>

            <FormField label="RSI Oversold Threshold">
              <Input
                type="number"
                value={localParams.rsi_oversold_threshold || 30}
                onChange={(e) => handleNumericChange('rsi_oversold_threshold', e.target.value)}
                step="1"
                min="10"
                max="50"
              />
            </FormField>

            <FormField label="MACD Histogram Threshold">
              <Input
                type="number"
                value={localParams.macd_histogram_threshold || -0.001}
                onChange={(e) => handleNumericChange('macd_histogram_threshold', e.target.value)}
                step="0.0001"
                min="-0.01"
                max="0.01"
              />
            </FormField>

            <FormField label="Base DCA Volume (USDT)">
              <Input
                type="number"
                value={localParams.base_dca_volume || 100}
                onChange={(e) => handleNumericChange('base_dca_volume', e.target.value)}
                step="10"
                min="10"
                max="1000"
              />
            </FormField>

            <FormField label="Max DCA Volume (USDT)">
              <Input
                type="number"
                value={localParams.max_dca_volume || 500}
                onChange={(e) => handleNumericChange('max_dca_volume', e.target.value)}
                step="50"
                min="50"
                max="2000"
              />
            </FormField>

            <FormField label="Max DCA Count">
              <Input
                type="number"
                value={localParams.max_dca_count || 10}
                onChange={(e) => handleNumericChange('max_dca_count', e.target.value)}
                step="1"
                min="1"
                max="20"
              />
            </FormField>

            <FormField label="Max Trade USDT">
              <Input
                type="number"
                value={localParams.max_trade_usdt || 2000}
                onChange={(e) => handleNumericChange('max_trade_usdt', e.target.value)}
                step="100"
                min="100"
                max="10000"
              />
            </FormField>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Parameters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Advanced Parameters
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? 'Hide' : 'Show'} Advanced
            </Button>
          </CardTitle>
        </CardHeader>
        {showAdvanced && (
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField label="Min Volume Ratio">
                <Input
                  type="number"
                  value={localParams.min_volume_ratio || 0.8}
                  onChange={(e) => handleNumericChange('min_volume_ratio', e.target.value)}
                  step="0.1"
                  min="0.1"
                  max="2.0"
                />
              </FormField>

              <FormField label="Volume Scaling Factor">
                <Input
                  type="number"
                  value={localParams.volume_scaling_factor || 0.2}
                  onChange={(e) => handleNumericChange('volume_scaling_factor', e.target.value)}
                  step="0.05"
                  min="0"
                  max="1"
                />
              </FormField>

              <FormField label="Confidence Factor Min">
                <Input
                  type="number"
                  value={localParams.confidence_factor_min || 0.5}
                  onChange={(e) => handleNumericChange('confidence_factor_min', e.target.value)}
                  step="0.1"
                  min="0"
                  max="1"
                />
              </FormField>

              <FormField label="Risk Score Threshold">
                <Input
                  type="number"
                  value={localParams.risk_score_threshold || 0.7}
                  onChange={(e) => handleNumericChange('risk_score_threshold', e.target.value)}
                  step="0.1"
                  min="0"
                  max="1"
                />
              </FormField>
            </div>

            <div className="space-y-2">
              <FormField label="Use ML Models" className="flex-row items-center gap-2">
                <Switch
                  checked={localParams.use_ml_models || false}
                  onCheckedChange={(value) => handleBooleanChange('use_ml_models', value)}
                />
              </FormField>

              <FormField label="Use BTC Filter" className="flex-row items-center gap-2">
                <Switch
                  checked={localParams.use_btc_filter || false}
                  onCheckedChange={(value) => handleBooleanChange('use_btc_filter', value)}
                />
              </FormField>

              <FormField label="Use Volume Filter" className="flex-row items-center gap-2">
                <Switch
                  checked={localParams.use_volume_filter || false}
                  onCheckedChange={(value) => handleBooleanChange('use_volume_filter', value)}
                />
              </FormField>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Optimization Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Parameter Optimization</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField label="Optimization Type">
              <Select value={optimizationType} onValueChange={setOptimizationType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="grid_search">Grid Search</SelectItem>
                  <SelectItem value="genetic_algorithm">Genetic Algorithm</SelectItem>
                  <SelectItem value="sensitivity_analysis">Sensitivity Analysis</SelectItem>
                </SelectContent>
              </Select>
            </FormField>

            <FormField label="Max Combinations">
              <Input
                type="number"
                value={localParams.max_combinations || 1000}
                onChange={(e) => handleNumericChange('max_combinations', e.target.value)}
                step="100"
                min="100"
                max="10000"
              />
            </FormField>
          </div>

          <div className="flex space-x-4">
            <Button
              onClick={handleRunOptimization}
              disabled={isRunning}
              className="flex-1"
            >
              {isRunning ? 'Running...' : 'Run Optimization'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex space-x-4">
            <Button
              onClick={onRunSimulation}
              disabled={isRunning}
              className="flex-1"
            >
              {isRunning ? 'Running Simulation...' : 'Run Simulation'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Optimization Results */}
      {optimizationResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Optimization Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {optimizationResults.slice(0, 5).map((result, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-800 rounded">
                  <div>
                    <div className="font-medium">Rank #{index + 1}</div>
                    <div className="text-sm text-gray-400">
                      Score: {result.performance_score?.toFixed(4) || 'N/A'}
                    </div>
                  </div>
                  <div className="text-sm">
                    <div>P&L: {result.final_pnl_pct?.toFixed(2) || 'N/A'}%</div>
                    <div>DCA Count: {result.total_dca_count || 'N/A'}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ParameterPanel;
