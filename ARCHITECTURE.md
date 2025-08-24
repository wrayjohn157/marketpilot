# Market7 Architecture Documentation

## Overview

Market7 is an intelligent crypto trading pipeline that combines fork filtering, smart DCA (Dollar-Cost Averaging), machine learning predictions, leverage trading, and recovery management to optimize trade entries and exits. The system operates as a distributed architecture with real-time data processing, ML-powered decision making, and a comprehensive dashboard interface.

## System Architecture

### Core Modules

#### 1. Fork Scoring Engine (`/core`, `/fork`, `/indicators`)
- **Purpose**: Identifies and scores potential trading opportunities using technical indicators
- **Components**:
  - `fork_scorer.py`: Core scoring algorithm with configurable weights
  - `fork_runner.py`: Main execution engine for fork detection
  - `fork_score_filter.py`: Filters candidates based on RRR (Risk-Reward-Ratio)
  - `tv_kicker.py`: TradingView screener integration
- **Scoring**: Combines MACD, RSI, EMA reclaim, and BTC market conditions
- **Output**: Scored candidates with confidence metrics

#### 2. Leverage Trading System (`/lev`) - **NEW**
- **Purpose**: Advanced leverage trading with long/short capabilities and futures integration
- **Components**:
  - `run_lev.py`: Main leverage trading execution engine
  - `lev_decision_engine.py`: Leverage DCA decision logic with enhanced guards
  - `futures_adapter.py`: Binance futures API integration
  - `fork_score_filter.py`: Leverage-aware fork filtering
  - `tv_kicker_lev.py`: Leverage TradingView signal processing
- **Features**:
  - **Long/Short Support**: Simultaneous long and short positions
  - **Futures Integration**: USDT-M perpetual futures trading
  - **Enhanced Risk Management**: Liquidation buffer protection
  - **ML Integration**: Recovery odds and confidence scoring
  - **BTC Market Filtering**: Direction-aware market condition filtering

#### 3. SAFU (Safe Exit) System (`/ml/safu`)
- **Purpose**: ML-powered exit decision making for risk management
- **Components**:
  - `train_safu_classifier.py`: Trains exit prediction models
  - `safu_exit_model.pkl`: Pre-trained model for exit decisions
  - `extract_safu_snapshot_analysis.py`: Analyzes trade snapshots
- **Features**: Exit probability scoring, recovery analysis, capital protection

#### 4. Smart DCA Engine (`/dca`) - **ENHANCED**
- **Purpose**: Intelligent DCA decision making with ML confidence scoring and advanced guards
- **Components**:
  - `smart_dca_signal.py`: Main DCA decision engine
  - `dca_decision_engine.py`: Core decision logic
  - `fork_safu_evaluator.py`: SAFU integration for DCA decisions
- **Enhanced Features**:
  - **Advanced DCA Guards**:
    - `confidence_dca_guard`: ML confidence-based DCA protection
    - `step_repeat_guard`: Prevents redundant DCA steps
    - `trailing_step_guard`: Dynamic step spacing based on price movement
    - `spend_guard`: Drawdown-based spend limits with ML adjustment
    - `zombie_tag`: Identifies and manages underperforming trades
  - **ML Integration**: Recovery odds, confidence scoring, spend prediction
  - **BTC Market Filtering**: Market condition awareness
  - **Trade Health Evaluation**: Comprehensive trade state monitoring

#### 5. Machine Learning Pipeline (`/ml`) - **UPDATED**
- **Purpose**: Training and inference for various trading models
- **Components**:
  - **Confidence Models** (`/ml/confidence`): Trade confidence prediction
  - **DCA Spend Models** (`/ml/dca_spend`): DCA volume optimization
  - **Recovery Models** (`/ml/recovery`): Recovery probability prediction
  - **SAFU Models** (`/ml/safu`): Exit decision models
- **Data Processing**: 
  - Feature engineering
  - Dataset building
  - Model training pipelines
  - Real-time inference
- **Updated Models**:
  - `xgb_confidence_model.pkl`: Enhanced confidence scoring (157KB)
  - `xgb_recovery_model.pkl`: Recovery probability prediction (110KB)
  - `xgb_spend_model.pkl`: DCA spend optimization (202KB)
  - `safu_exit_model.pkl`: SAFU exit decisions (160KB)

#### 6. Dashboard System
- **Backend** (`/dashboard_backend`): FastAPI-based REST API
  - Real-time trade monitoring
  - Configuration management
  - ML model inference endpoints
  - Simulation and backtesting routes
- **Frontend** (`/dashboard_frontend`): React-based UI
  - Trade visualization
  - Configuration panels
  - Real-time metrics
  - Interactive charts

#### 7. Enhanced Data Processing (`/data`) - **NEW**
- **Purpose**: Multi-source data collection with leverage awareness
- **Components**:
  - `rolling_indicators_with_lev.py`: Leverage-aware technical indicators
  - `rolling_klines.py`: Multi-timeframe price data collection
  - `rolling_indicators.py`: Technical indicator calculation
- **Features**:
  - **Multi-Source Support**: Spot and futures data integration
  - **Auto-Detection**: Intelligent market source selection
  - **Leverage Awareness**: Perpetual futures symbol handling
  - **Redis Integration**: Real-time data caching

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Config Files  │    │   External      │    │   Market Data   │
│   (YAML)       │    │   APIs          │    │   (Binance)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Configuration Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  DCA Config    │  │  Leverage Config│  │  Strategy Config│ │
│  │  (Enhanced)    │  │  (NEW)          │  │  (Updated)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Processing Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Fork Runner    │  │  Leverage       │  │  ML Models      │ │
│  │  (Enhanced)     │  │  Engine (NEW)   │  │  (Updated)      │ │
│  │                 │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Redis Cache Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Trade Data     │  │  ML Scores      │  │  Market Status  │ │
│  │  (Spot + Lev)   │  │  (Enhanced)     │  │  (BTC + Lev)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Dashboard Backend                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  FastAPI        │  │  API Routes     │  │  ML Inference   │ │
│  │  (Enhanced)     │  │  (Updated)      │  │  (Enhanced)     │ │
│  │                 │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Dashboard Frontend                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  React App      │  │  Trade Views    │  │  Config Panels  │ │
│  │  (Enhanced)     │  │  (Spot + Lev)   │  │  (Enhanced)     │ │
│  │                 │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Services and Execution

#### Core Services

1. **Fork Detection Service** (`/fork/fork_runner.py`)
   - **Purpose**: Continuously scans for trading opportunities
   - **Execution**: Runs via `run_fork_safu.sh` script
   - **Output**: Sends signals to 3Commas trading bots

2. **Leverage Trading Service** (`/lev/run_lev.py`) - **NEW**
   - **Purpose**: Advanced leverage trading with long/short capabilities
   - **Execution**: Runs via `python3 lev/run_lev.py`
   - **Features**: Futures integration, enhanced risk management, ML integration

3. **Smart DCA Service** (`/dca/smart_dca_signal.py`) - **ENHANCED**
   - **Purpose**: Monitors active trades and makes DCA decisions with advanced guards
   - **Execution**: Runs continuously via cron or systemd
   - **Integration**: Connects to 3Commas API for trade execution
   - **Enhanced Features**: ML confidence scoring, advanced DCA guards, zombie detection

4. **ML Inference Service** (`/dashboard_backend/ml_confidence_api.py`)
   - **Purpose**: Real-time ML model inference
   - **Models**: Confidence, SAFU, recovery, spend prediction
   - **Cache**: Redis-based caching for performance

5. **Dashboard Backend** (`/dashboard_backend/main.py`)
   - **Purpose**: REST API for frontend and external integrations
   - **Framework**: FastAPI with CORS support
   - **Port**: Runs on port 8000 (configurable)

6. **Enhanced Data Collection Services** - **UPDATED**
   - **BTC Logger** (`/dashboard_backend/btc_logger.py`): Market condition monitoring
   - **Price Refresh** (`/dashboard_backend/refresh_price_api.py`): Real-time price updates
   - **Trade Metrics** (`/dashboard_backend/threecommas_metrics.py`): 3Commas integration
   - **Leverage Indicators** (`/data/rolling_indicators_with_lev.py`): Multi-source data processing

#### Configuration Management

- **Centralized Config**: All configurations managed via YAML files in `/config`
- **Dynamic Loading**: `config_loader.py` provides unified access to all paths and settings
- **Environment Support**: Separate configs for different environments (paper, live, leverage)
- **New Configs**:
  - `leverage_config.yaml`: Leverage trading parameters
  - `binance_futures_testnet.json`: Futures API credentials

#### Data Storage

- **Redis**: Real-time caching and inter-service communication
- **File System**: Historical data, snapshots, and ML datasets
- **3Commas API**: Trade execution and status tracking
- **Binance Futures API**: Leverage trading execution

### Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Production    │    │   Development   │    ┌   Monitoring    │
│   Environment   │    │   Environment   │    │   & Logging     │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │  Live     │  │    │  │  Paper    │  │    │  │  Logs     │  │
│  │  Trading  │  │    │  │  Trading  │  │    │  │  (Redis)  │  │
│  │  + Leverage│  │    │  │  + Leverage│  │    │  │           │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Systemd        │  │  Cron Jobs      │  │  Docker        │ │
│  │  Services       │  │  (Data Sync)    │  │  Containers    │ │
│  │  (Enhanced)     │  │  (Multi-source) │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Integration Points

1. **3Commas Integration**
   - Bot management via API
   - Trade signal execution
   - Real-time trade monitoring

2. **Binance Integration** - **ENHANCED**
   - **Spot Trading**: Market data collection and spot trading
   - **Futures Trading**: USDT-M perpetual futures for leverage
   - **Multi-Source Data**: Intelligent source selection (spot vs futures)

3. **TradingView Integration**
   - Screener data
   - Technical analysis
   - Market sentiment

4. **Redis Integration**
   - Inter-service communication
   - Real-time data caching
   - ML model inference caching

5. **Leverage Trading Integration** - **NEW**
   - **Futures Adapter**: Binance futures API integration
   - **Risk Management**: Liquidation buffer protection
   - **Position Management**: Long/short position handling

### Security Considerations

- **API Key Management**: Credentials stored in separate config files
- **CORS Configuration**: Configurable for production deployment
- **Rate Limiting**: Built into 3Commas and Binance API integration
- **Logging**: Comprehensive audit trails for all trading decisions
- **Risk Controls**: Enhanced leverage trading risk management

### Performance Characteristics

- **Real-time Processing**: Sub-second response times for ML inference
- **Scalability**: Redis-based caching for high-throughput scenarios
- **Reliability**: Fallback mechanisms and error handling throughout
- **Monitoring**: Built-in health checks and performance metrics
- **Multi-Source Data**: Efficient handling of spot and futures data streams

### New Features and Capabilities

#### Leverage Trading System
- **Long/Short Support**: Simultaneous long and short positions
- **Futures Integration**: USDT-M perpetual futures trading
- **Enhanced Risk Management**: Liquidation buffer protection
- **Direction-Aware Filtering**: BTC market condition filtering for both directions
- **ML Integration**: Recovery odds and confidence scoring for leverage decisions

#### Enhanced DCA Guards
- **Confidence DCA Guard**: ML confidence-based DCA protection
- **Step Repeat Guard**: Prevents redundant DCA steps
- **Trailing Step Guard**: Dynamic step spacing based on price movement
- **Spend Guard**: Drawdown-based spend limits with ML adjustment
- **Zombie Tag**: Identifies and manages underperforming trades

#### Advanced Data Processing
- **Multi-Source Support**: Spot and futures data integration
- **Auto-Detection**: Intelligent market source selection
- **Leverage Awareness**: Perpetual futures symbol handling
- **Enhanced Indicators**: Leverage-aware technical indicators

### Future Architecture Considerations

1. **Microservices**: Potential split into separate services for fork detection, DCA, leverage, and ML
2. **Message Queues**: Integration with RabbitMQ or Apache Kafka for better reliability
3. **Container Orchestration**: Kubernetes deployment for production scaling
4. **Multi-exchange Support**: Extensible adapter pattern for additional exchanges
5. **Advanced ML Pipeline**: MLOps integration with model versioning and A/B testing
6. **Leverage Expansion**: Additional leverage products and risk management tools
7. **Real-time Analytics**: Advanced analytics and reporting for leverage positions

---

*This architecture documentation reflects the current state of Market7 as of the latest commit, including all recent enhancements from the master branch merge. For specific implementation details, refer to the individual module documentation and source code.*
