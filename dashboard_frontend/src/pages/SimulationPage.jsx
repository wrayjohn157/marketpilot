import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { FormField } from '../components/ui/FormField';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/Select';
import SimulationChart from '../components/SimulationChart';
import ParameterPanel from '../components/ParameterPanel';
import ResultsPanel from '../components/ResultsPanel';

const SimulationPage = () => {
  // State management
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [entryTime, setEntryTime] = useState(null);
  const [simulationDays, setSimulationDays] = useState(30);
  const [isRunning, setIsRunning] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);
  const [optimizationResults, setOptimizationResults] = useState([]);
  const [availableSymbols, setAvailableSymbols] = useState([]);
  const [availableTimeframes, setAvailableTimeframes] = useState(['15m', '1h', '4h', '1d']);
  const [historicalData, setHistoricalData] = useState([]);
  const [selectedCandle, setSelectedCandle] = useState(null);

  // DCA Parameters
  const [dcaParameters, setDcaParameters] = useState({
    confidence_threshold: 0.6,
    min_drawdown_pct: 2.0,
    rsi_oversold_threshold: 30,
    macd_histogram_threshold: -0.001,
    min_volume_ratio: 0.8,
    base_dca_volume: 100,
    max_dca_volume: 500,
    max_dca_count: 10,
    max_trade_usdt: 2000,
    use_ml_models: false,
    use_btc_filter: false,
    use_volume_filter: false
  });

  // Load available symbols on component mount
  useEffect(() => {
    loadAvailableSymbols();
    loadAvailableTimeframes();
  }, []);

  // Load historical data when symbol or timeframe changes
  useEffect(() => {
    if (symbol && timeframe) {
      loadHistoricalData();
    }
  }, [symbol, timeframe]);

  // API calls
  const loadAvailableSymbols = async () => {
    try {
      const response = await fetch('/api/simulation/data/symbols');
      const data = await response.json();
      if (data.success) {
        setAvailableSymbols(data.symbols);
      }
    } catch (error) {
      console.error('Error loading symbols:', error);
    }
  };

  const loadAvailableTimeframes = async () => {
    try {
      const response = await fetch('/api/simulation/data/timeframes');
      const data = await response.json();
      if (data.success) {
        setAvailableTimeframes(data.timeframes);
      }
    } catch (error) {
      console.error('Error loading timeframes:', error);
    }
  };

  const loadHistoricalData = async () => {
    try {
      const endTime = Date.now();
      const startTime = endTime - (simulationDays * 24 * 60 * 60 * 1000);
      
      const response = await fetch('/api/simulation/data/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          timeframe,
          start_time: startTime,
          end_time: endTime
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setHistoricalData(data.data.candles);
      }
    } catch (error) {
      console.error('Error loading historical data:', error);
    }
  };

  // Run simulation
  const runSimulation = async () => {
    if (!entryTime) {
      alert('Please select an entry point by clicking on a candle in the chart');
      return;
    }

    setIsRunning(true);
    try {
      const response = await fetch('/api/simulation/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          entry_time: entryTime,
          timeframe,
          dca_params: dcaParameters,
          simulation_days: simulationDays
        })
      });

      const data = await response.json();
      if (data.success) {
        setSimulationResult(data.result);
      } else {
        alert('Simulation failed: ' + data.detail);
      }
    } catch (error) {
      console.error('Error running simulation:', error);
      alert('Error running simulation: ' + error.message);
    } finally {
      setIsRunning(false);
    }
  };

  // Run optimization
  const runOptimization = async (optimizationType, parameterRanges) => {
    setIsRunning(true);
    try {
      const response = await fetch('/api/simulation/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          entry_time: entryTime,
          timeframe,
          parameter_ranges: parameterRanges,
          optimization_type: optimizationType,
          simulation_days: simulationDays
        })
      });

      const data = await response.json();
      if (data.success) {
        setOptimizationResults(data.results);
        if (data.best_result) {
          setDcaParameters(data.best_result.parameters);
        }
      } else {
        alert('Optimization failed: ' + data.detail);
      }
    } catch (error) {
      console.error('Error running optimization:', error);
      alert('Error running optimization: ' + error.message);
    } finally {
      setIsRunning(false);
    }
  };

  // Handle candle click
  const handleCandleClick = useCallback((candle, index) => {
    setEntryTime(candle.timestamp.getTime());
    setSelectedCandle(candle);
  }, []);

  // Export results
  const exportResults = () => {
    if (!simulationResult) return;
    
    const dataStr = JSON.stringify(simulationResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dca_simulation_${symbol}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">DCA Simulation System</h1>
          <p className="text-gray-400">
            Test and optimize DCA strategies on historical data
          </p>
        </div>

        {/* Configuration Panel */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Simulation Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <FormField label="Symbol">
                <Select value={symbol} onValueChange={setSymbol}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableSymbols.map(sym => (
                      <SelectItem key={sym} value={sym}>{sym}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormField>

              <FormField label="Timeframe">
                <Select value={timeframe} onValueChange={setTimeframe}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableTimeframes.map(tf => (
                      <SelectItem key={tf} value={tf}>{tf}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormField>

              <FormField label="Simulation Days">
                <Input
                  type="number"
                  value={simulationDays}
                  onChange={(e) => setSimulationDays(parseInt(e.target.value))}
                  min="1"
                  max="365"
                />
              </FormField>

              <FormField label="Entry Point">
                <div className="text-sm text-gray-400">
                  {entryTime ? 
                    `Selected: ${new Date(entryTime).toLocaleString()}` : 
                    'Click on chart to select'
                  }
                </div>
              </FormField>
            </div>
          </CardContent>
        </Card>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart */}
          <div className="lg:col-span-2">
            <SimulationChart
              data={historicalData}
              dcaPoints={simulationResult?.dca_points || []}
              entryPoint={selectedCandle ? {
                timestamp: selectedCandle.timestamp,
                price: selectedCandle.close
              } : null}
              onCandleClick={handleCandleClick}
              selectedCandle={selectedCandle}
              height={500}
            />
          </div>

          {/* Parameters & Results */}
          <div className="space-y-6">
            <ParameterPanel
              parameters={dcaParameters}
              onParametersChange={setDcaParameters}
              onRunSimulation={runSimulation}
              onRunOptimization={runOptimization}
              isRunning={isRunning}
              optimizationResults={optimizationResults}
            />
          </div>
        </div>

        {/* Results Panel */}
        <div className="mt-6">
          <ResultsPanel
            simulationResult={simulationResult}
            isRunning={isRunning}
            onExportResults={exportResults}
          />
        </div>

        {/* Status Bar */}
        <div className="mt-6 p-4 bg-gray-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-400">
              {isRunning ? 'Running simulation...' : 
               simulationResult ? 'Simulation completed' : 
               'Ready to run simulation'}
            </div>
            <div className="text-sm text-gray-400">
              {historicalData.length} candles loaded
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationPage;