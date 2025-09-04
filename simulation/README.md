# DCA Simulation System

## 🎯 **Overview**
A clean, isolated simulation system for testing DCA strategies on historical data without affecting production systems.

## 🏗️ **Architecture**

```
simulation/
├── core/
│   ├── data_manager.py          # Historical data loading
│   ├── dca_simulator.py         # Core simulation engine
│   ├── parameter_tuner.py       # Parameter optimization
│   └── result_analyzer.py       # Performance analysis
├── api/
│   ├── simulation_routes.py     # FastAPI endpoints
│   └── data_routes.py           # Data access endpoints
├── frontend/
│   ├── SimulationChart.jsx      # Enhanced chart component
│   ├── ParameterPanel.jsx       # Parameter tuning UI
│   └── ResultsPanel.jsx         # Performance metrics
├── config/
│   ├── simulation_config.yaml   # Simulation settings
│   └── parameter_ranges.yaml    # Parameter boundaries
└── tests/
    ├── test_simulator.py        # Unit tests
    └── test_data_manager.py     # Data tests
```

## 🔧 **Key Features**

### **1. Historical Data Pipeline**
- Load klines from Binance API or local snapshots
- Support multiple timeframes (15m, 1h, 4h)
- Data validation and quality checks
- Symbol discovery and availability

### **2. DCA Simulation Engine**
- Isolated simulation using production DCA logic
- No risk to production systems
- Support for all DCA parameters
- Real-time simulation results

### **3. Parameter Optimization**
- Grid search for optimal parameters
- Genetic algorithm optimization
- Sensitivity analysis
- Performance comparison

### **4. Visualization & Analysis**
- Interactive candlestick charts
- DCA trigger point visualization
- Performance metrics dashboard
- Parameter impact analysis

## 🚀 **Usage**

```python
# Basic simulation
simulator = DCASimulator()
results = simulator.simulate(
    symbol="BTCUSDT",
    entry_time=1640995200000,  # 2022-01-01
    timeframe="1h",
    dca_params={
        "entry_score": 0.75,
        "confidence_threshold": 0.6,
        "max_trade_usdt": 2000
    }
)

# Parameter optimization
tuner = ParameterTuner()
best_params = tuner.optimize(
    symbol="BTCUSDT",
    entry_time=1640995200000,
    parameter_ranges={
        "entry_score": [0.6, 0.8],
        "confidence_threshold": [0.5, 0.7]
    }
)
```

## 📊 **Benefits**

- **Risk-free testing** - No impact on production
- **Parameter discovery** - Find optimal settings
- **Strategy validation** - Test before deploying
- **Performance analysis** - Understand what works
- **SAAS ready** - Clean, professional interface