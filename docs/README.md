# 📚 Market7 Trading System Documentation

Welcome to the Market7 Trading System - a comprehensive, AI-powered trading platform designed for automated cryptocurrency trading with advanced risk management and machine learning capabilities.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git installed
- Basic understanding of cryptocurrency trading
- API keys for 3Commas and Binance (optional for testing)

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/market7.git
cd market7

# Start the system
./deploy.sh
```

### Access the Dashboard
- **Main Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Monitoring**: http://localhost:3001 (admin/admin123)

## 📖 Table of Contents

1. [Getting Started](#getting-started)
2. [User Interface Guide](#user-interface-guide)
3. [Trading Features](#trading-features)
4. [Configuration](#configuration)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)
8. [Advanced Usage](#advanced-usage)
9. [FAQ](#faq)
10. [Support](#support)

## 🎯 Getting Started

### What is Market7?

Market7 is an advanced cryptocurrency trading system that combines:
- **Smart DCA (Dollar-Cost Averaging)**: Intelligent trade rescue strategies
- **Machine Learning**: AI-powered market analysis and predictions
- **Risk Management**: Advanced SAFU (Safe Exit) mechanisms
- **Real-time Monitoring**: Comprehensive dashboards and alerts
- **Multi-Exchange Support**: 3Commas and Binance integration

### Key Features

#### 🤖 AI-Powered Trading
- Machine learning models for market prediction
- Automated trade analysis and decision making
- Confidence scoring for trade recommendations
- Adaptive strategies based on market conditions

#### 💰 Smart DCA System
- Intelligent trade rescue strategies
- Progressive volume scaling
- Zombie trade detection and management
- Profitability analysis and optimization

#### 🛡️ Risk Management
- SAFU (Safe Exit) system for risk mitigation
- Real-time portfolio monitoring
- Automated stop-loss mechanisms
- Market volatility analysis

#### 📊 Real-time Monitoring
- Live trading dashboard
- Performance analytics
- Alert system for critical events
- Historical data analysis

## 🖥️ User Interface Guide

### Main Dashboard

The main dashboard provides an overview of your trading system:

#### 📈 Account Summary
- **Balance**: Current account balance
- **Today's P&L**: Profit/Loss for today
- **Active Trades**: Number of currently active trades
- **Total Volume**: Trading volume for the period

#### 🔄 Active Trades Panel
- **Live Trades**: Real-time view of active positions
- **Trade Details**: Entry price, current price, P&L
- **DCA Status**: DCA attempts and success rates
- **Risk Level**: Current risk assessment

#### 📊 Performance Metrics
- **Success Rate**: Percentage of profitable trades
- **Average P&L**: Average profit/loss per trade
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Maximum loss from peak

### Navigation Menu

#### 🏠 Dashboard
- System overview and key metrics
- Quick access to important information
- Real-time status updates

#### 📈 Trading
- **Active Trades**: Current positions and status
- **Trade History**: Historical trade data
- **DCA Tracker**: DCA system performance
- **Strategy Builder**: Create and test strategies

#### 🤖 ML Monitor
- **Model Performance**: ML model accuracy and predictions
- **Feature Importance**: Key factors in predictions
- **Training Status**: Model training progress
- **Prediction Confidence**: Current market sentiment

#### ⚠️ BTC Risk Panel
- **Market Sentiment**: BTC market analysis
- **Risk Indicators**: Key risk metrics
- **Recommendations**: Trading recommendations
- **Market Conditions**: Current market state

#### 📚 Backtest Summary
- **Strategy Performance**: Historical strategy results
- **Risk Metrics**: Backtest risk analysis
- **Optimization Results**: Parameter optimization
- **Comparison Tools**: Strategy comparison

#### 🔍 Scan Review
- **Market Scans**: Automated market analysis
- **Filter Results**: Filtered trading opportunities
- **Score Analysis**: Opportunity scoring
- **Recommendations**: Trading recommendations

## 💼 Trading Features

### Smart DCA System

The Smart DCA system is designed to rescue profitable trades using intelligent strategies:

#### How It Works
1. **Trade Analysis**: Analyzes current trade performance
2. **Risk Assessment**: Evaluates risk factors and market conditions
3. **DCA Decision**: Determines if DCA is appropriate
4. **Volume Calculation**: Calculates optimal DCA volume
5. **Execution**: Executes DCA with monitoring

#### DCA Strategies
- **Progressive Scaling**: Increases volume based on confidence
- **Risk-Based**: Adjusts based on current risk level
- **Market-Adaptive**: Adapts to market conditions
- **Profit-Focused**: Prioritizes profitable rescues

#### Configuration Options
- **Max DCA Attempts**: Maximum number of DCA attempts
- **Volume Scaling**: How to scale DCA volume
- **Risk Thresholds**: Risk levels for DCA decisions
- **Profit Targets**: Target profit levels

### Machine Learning Integration

#### Model Types
- **SAFU Exit**: Binary classification for safe exit decisions
- **Recovery Odds**: Probability of trade recovery
- **Confidence Score**: Regression model for trade confidence
- **DCA Spend**: Optimal DCA volume prediction
- **Trade Success**: Binary classification for trade success

#### Features Used
- **Technical Indicators**: RSI, MACD, Bollinger Bands, etc.
- **Market Data**: Price, volume, volatility
- **Time Series**: Historical price patterns
- **External Data**: News sentiment, social media

#### Model Performance
- **Accuracy**: Model prediction accuracy
- **Precision**: True positive rate
- **Recall**: Sensitivity to positive cases
- **F1 Score**: Harmonic mean of precision and recall

### Risk Management

#### SAFU System
The SAFU (Safe Exit) system provides automated risk management:

- **Stop Loss**: Automatic stop-loss orders
- **Take Profit**: Profit-taking mechanisms
- **Risk Limits**: Maximum risk per trade
- **Portfolio Limits**: Overall portfolio risk management

#### Risk Indicators
- **Volatility**: Market volatility assessment
- **Correlation**: Asset correlation analysis
- **Liquidity**: Market liquidity indicators
- **Sentiment**: Market sentiment analysis

## ⚙️ Configuration

### Initial Setup

#### 1. API Configuration
```yaml
# config/credentials/3commas_default.json
{
  "api_key": "your_3commas_api_key",
  "api_secret": "your_3commas_api_secret",
  "account_id": "your_account_id"
}
```

#### 2. Trading Parameters
```yaml
# config/smart_dca_config.yaml
dca_config:
  max_attempts: 5
  base_volume: 100
  volume_scaling: 1.5
  risk_threshold: 0.7
  profit_target: 0.05
```

#### 3. ML Configuration
```yaml
# config/ml_pipeline_config.yaml
ml_config:
  model_types: ["safu_exit", "recovery_odds", "confidence_score"]
  training_interval: "1h"
  prediction_interval: "15m"
  confidence_threshold: 0.8
```

### Environment Variables

#### Required Variables
```bash
# Database
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=market7

# Redis
REDIS_PASSWORD=your_redis_password

# Monitoring
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

#### Optional Variables
```bash
# SMTP (for alerts)
SMTP_PASSWORD=your_smtp_password

# Slack (for notifications)
SLACK_WEBHOOK_URL=your_slack_webhook

# Domain (for remote access)
DOMAIN=your-domain.com
```

### Configuration Files

#### Paths Configuration
```yaml
# config/paths_config.yaml
base_path: "/workspace"
data_path: "/workspace/data"
logs_path: "/workspace/logs"
models_path: "/workspace/models"
```

#### Trading Pipeline Configuration
```yaml
# config/unified_pipeline_config.yaml
pipeline_config:
  tech_filter:
    min_score: 0.6
    indicators: ["rsi", "macd", "bollinger"]
  fork_scorer:
    weights: {"technical": 0.4, "sentiment": 0.3, "volume": 0.3}
  tv_adjuster:
    enabled: true
    weight: 0.2
```

## 📊 Monitoring & Alerts

### Dashboard Access

#### Grafana Dashboards
- **System Overview**: http://grafana.market7.local
- **Trading Metrics**: http://grafana.market7.local/d/market7-trading
- **ML Performance**: http://grafana.market7.local/d/ml-performance

#### Prometheus Metrics
- **Metrics Endpoint**: http://prometheus.market7.local
- **Target Status**: http://prometheus.market7.local/targets
- **Alert Rules**: http://prometheus.market7.local/alerts

### Alert Configuration

#### Critical Alerts
- **Service Down**: Backend/Frontend unavailable
- **Database Issues**: PostgreSQL/Redis connectivity
- **High Error Rate**: API error rate >5%
- **Low Disk Space**: Disk usage >90%

#### Warning Alerts
- **High Resource Usage**: CPU/Memory >80%
- **Trading Errors**: Trading error rate spikes
- **API Issues**: External API problems
- **Performance Issues**: Response time >2s

#### Alert Channels
- **Email**: admin@market7.local
- **Slack**: #trading-alerts channel
- **Webhook**: Custom webhook endpoints

### Monitoring Setup

#### Start Monitoring
```bash
cd monitoring
./setup_monitoring.sh
```

#### Test Monitoring
```bash
python3 monitoring/test_monitoring.py
```

#### View Logs
```bash
# All services
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f

# Specific service
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f grafana
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check Docker status
docker ps -a

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Check Redis status
docker-compose exec redis redis-cli ping
```

#### API Connection Issues
```bash
# Test 3Commas API
curl -X GET "http://localhost:8000/api/3commas/health"

# Test Binance API
curl -X GET "http://localhost:8000/api/binance/health"
```

#### Frontend Issues
```bash
# Check frontend build
cd dashboard_frontend
npm run build

# Check for errors
npm run lint
```

### Performance Issues

#### High CPU Usage
1. Check system resources: `docker stats`
2. Review active processes
3. Optimize configuration
4. Scale resources if needed

#### High Memory Usage
1. Check memory usage: `free -h`
2. Review Redis memory usage
3. Optimize data structures
4. Increase memory limits

#### Slow Response Times
1. Check database performance
2. Review API response times
3. Optimize queries
4. Check network latency

### Log Analysis

#### Log Locations
- **Application Logs**: `/workspace/logs/`
- **Docker Logs**: `docker-compose logs`
- **System Logs**: `/var/log/`

#### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

#### Log Rotation
```bash
# Configure log rotation
sudo logrotate -f /etc/logrotate.d/market7
```

## 📡 API Reference

### Authentication

#### API Key Authentication
```bash
curl -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/trades
```

#### JWT Token Authentication
```bash
# Get token
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer your_jwt_token" \
     http://localhost:8000/api/trades
```

### Endpoints

#### Trading Endpoints
```bash
# Get active trades
GET /api/trades/active

# Get trade history
GET /api/trades/history

# Get DCA status
GET /api/dca/status

# Execute DCA
POST /api/dca/execute
```

#### ML Endpoints
```bash
# Get model predictions
GET /api/ml/predictions

# Get model performance
GET /api/ml/performance

# Retrain model
POST /api/ml/retrain
```

#### System Endpoints
```bash
# Health check
GET /api/health

# System status
GET /api/status

# Metrics
GET /api/metrics
```

### Response Formats

#### Success Response
```json
{
  "status": "success",
  "data": {
    "trades": [...],
    "count": 10
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {...}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🚀 Advanced Usage

### Custom Strategies

#### Strategy Development
```python
# Create custom strategy
from market7.strategies import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def analyze(self, data):
        # Custom analysis logic
        return analysis_result
    
    def execute(self, signal):
        # Custom execution logic
        return execution_result
```

#### Strategy Testing
```python
# Backtest strategy
from market7.backtesting import Backtester

backtester = Backtester(strategy=MyCustomStrategy())
results = backtester.run(
    start_date="2023-01-01",
    end_date="2023-12-31",
    initial_capital=10000
)
```

### Custom Indicators

#### Indicator Development
```python
# Create custom indicator
from market7.indicators import BaseIndicator

class MyCustomIndicator(BaseIndicator):
    def calculate(self, data):
        # Custom calculation logic
        return indicator_values
```

#### Indicator Usage
```python
# Use custom indicator
indicator = MyCustomIndicator()
values = indicator.calculate(price_data)
```

### Data Analysis

#### Historical Data
```python
# Get historical data
from market7.data import DataManager

data_manager = DataManager()
data = data_manager.get_historical_data(
    symbol="BTCUSDT",
    timeframe="1h",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

#### Technical Analysis
```python
# Perform technical analysis
from market7.analysis import TechnicalAnalyzer

analyzer = TechnicalAnalyzer()
analysis = analyzer.analyze(data)
```

## ❓ FAQ

### General Questions

#### Q: What is Market7?
A: Market7 is an AI-powered cryptocurrency trading system that combines machine learning, smart DCA strategies, and advanced risk management for automated trading.

#### Q: Is Market7 free to use?
A: Market7 is open-source software. You can use it for free, but you'll need API keys for exchanges (3Commas, Binance) to trade with real money.

#### Q: What exchanges does Market7 support?
A: Market7 currently supports 3Commas and Binance exchanges through their APIs.

#### Q: Is Market7 safe to use?
A: Market7 includes comprehensive risk management features, but trading cryptocurrencies always involves risk. Use appropriate position sizing and never risk more than you can afford to lose.

### Technical Questions

#### Q: What are the system requirements?
A: Market7 requires Docker, Docker Compose, and at least 4GB RAM. For production use, 8GB+ RAM is recommended.

#### Q: Can I run Market7 on a VPS?
A: Yes, Market7 is designed to run on VPS providers like DigitalOcean, AWS, or Google Cloud.

#### Q: How do I update Market7?
A: Use `git pull` to get the latest code, then `docker-compose up -d` to restart with the new version.

#### Q: Can I customize the trading strategies?
A: Yes, Market7 is highly customizable. You can modify existing strategies or create your own.

### Trading Questions

#### Q: How does the DCA system work?
A: The DCA system analyzes trades and makes intelligent decisions about when to add to losing positions to improve average entry price.

#### Q: What is the SAFU system?
A: SAFU (Safe Exit) is a risk management system that automatically exits trades when certain risk conditions are met.

#### Q: How accurate are the ML predictions?
A: ML model accuracy varies by market conditions, but typically ranges from 60-80% for binary classifications.

#### Q: Can I paper trade first?
A: Yes, Market7 supports paper trading for testing strategies without real money.

### Troubleshooting Questions

#### Q: The system won't start. What should I do?
A: Check the logs with `docker-compose logs`, ensure all required services are running, and verify your configuration.

#### Q: I'm getting API errors. What's wrong?
A: Verify your API keys are correct, check your internet connection, and ensure you haven't exceeded API rate limits.

#### Q: The frontend is not loading. What should I do?
A: Check if the frontend container is running, verify port 3000 is accessible, and check the frontend logs.

#### Q: My trades aren't executing. Why?
A: Check your API permissions, verify your account has sufficient balance, and ensure the trading system is enabled.

## 🆘 Support

### Getting Help

#### Documentation
- **User Guide**: This documentation
- **API Reference**: http://localhost:8000/docs
- **Code Documentation**: Inline code comments

#### Community
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Wiki**: Community-maintained documentation

#### Professional Support
- **Email**: support@market7.local
- **Discord**: Join our Discord server
- **Telegram**: Join our Telegram group

### Contributing

#### How to Contribute
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

#### Development Setup
```bash
# Clone repository
git clone https://github.com/your-username/market7.git
cd market7

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
python main.py
```

#### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write comprehensive tests
- Document all functions and classes

### License

Market7 is licensed under the MIT License. See LICENSE file for details.

### Disclaimer

This software is for educational and research purposes. Trading cryptocurrencies involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Use at your own risk.

---

**Happy Trading! 🚀📈**

For the latest updates and news, follow us on GitHub and join our community discussions.