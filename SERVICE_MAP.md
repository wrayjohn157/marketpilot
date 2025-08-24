# Market7 Service Map

## Overview

This document maps all systemd services and their configurations for the Market7 trading system. While no actual `.service` files are present in the repository, the system is designed to run as systemd services as evidenced by the management scripts. The current master branch includes new leverage trading capabilities and enhanced DCA services.

## Service Definitions

Based on the analysis of `restart_all.sh` and `multilog.sh`, the following services are expected to be running:

| Unit | Type | ExecStart/OnCalendar | Script Path | Env Files | Log Target |
|------|------|---------------------|-------------|-----------|------------|
| `fork_score_filter.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/indicators/fork_score_filter.py` | `/home/signal/market7/indicators/fork_score_filter.py` | `/home/signal/market7/.env` | `journalctl -u fork_score_filter.service` |
| `generate_tv_screener_ratings.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/indicators/rrr_filter/generate_tv_screener_ratings.py` | `/home/signal/market7/indicators/rrr_filter/generate_tv_screener_ratings.py` | `/home/signal/market7/.env` | `journalctl -u generate_tv_screener_ratings.service` |
| `market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/dashboard_backend/main.py` | `/home/signal/market7/dashboard_backend/main.py` | `/home/signal/market7/.env` | `journalctl -u market7.service` |
| `ml_confidence_cache_market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/dashboard_backend/ml_confidence_cache_writer.py` | `/home/signal/market7/dashboard_backend/ml_confidence_cache_writer.py` | `/home/signal/market7/.env` | `journalctl -u ml_confidence_cache_market7.service` |
| `btc_logger.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/dashboard_backend/btc_logger.py` | `/home/signal/market7/dashboard_backend/btc_logger.py` | `/home/signal/market7/.env` | `journalctl -u btc_logger.service` |
| `fork_metrics.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/dashboard_backend/metrics_fork_3commas.py` | `/home/signal/market7/dashboard_backend/metrics_fork_3commas.py` | `/home/signal/market7/.env` | `journalctl -u fork_metrics.service` |
| `fork_safu_monitor.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/fork/modules/fork_safu_monitor.py` | `/home/signal/market7/fork/modules/fork_safu_monitor.py` | `/home/signal/market7/.env` | `journalctl -u fork_safu_monitor.service` |
| `rolling_indicators_market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/data/rolling_indicators.py` | `/home/signal/market7/data/rolling_indicators.py` | `/home/signal/market7/.env` | `journalctl -u rolling_indicators_market7.service` |
| `rolling_klines_market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/data/rolling_klines.py` | `/home/signal/market7/data/rolling_klines.py` | `/home/signal/market7/.env` | `journalctl -u rolling_klines_market7.service` |
| `smart_dca_market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/dca/smart_dca_signal.py` | `/home/signal/market7/dca/smart_dca_signal.py` | `/home/signal/market7/.env` | `journalctl -u smart_dca_market7.service` |
| `tv_kicker_market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/indicators/tv_kicker.py` | `/home/signal/market7/indicators/tv_kicker.py` | `/home/signal/market7/.env` | `journalctl -u tv_kicker_market7.service` |
| `fork_runner.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/fork/fork_runner.py` | `/home/signal/market7/fork/fork_runner.py` | `/home/signal/market7/.env` | `journalctl -u fork_runner.service` |

## New Services (Master Branch)

The following services have been added in the recent master branch merge and should be considered for systemd integration:

| Unit | Type | ExecStart/OnCalendar | Script Path | Env Files | Log Target |
|------|------|---------------------|-------------|-----------|------------|
| `leverage_trading_market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/lev/run_lev.py` | `/home/signal/market7/lev/run_lev.py` | `/home/signal/market7/.env` | `journalctl -u leverage_trading_market7.service` |
| `rolling_indicators_with_lev_market7.service` | Service | `ExecStart=/usr/bin/python3 /home/signal/market7/data/rolling_indicators_with_lev.py` | `/home/signal/market7/data/rolling_indicators_with_lev.py` | `/home/signal/market7/.env` | `journalctl -u rolling_indicators_with_lev_market7.service` |

## Service Categories

### Core Trading Services
- **`fork_runner.service`**: Main fork detection and signal generation
- **`smart_dca_market7.service`**: Intelligent DCA decision making with enhanced guards
- **`fork_safu_monitor.service`**: SAFU exit monitoring and decisions
- **`leverage_trading_market7.service`**: **NEW** - Advanced leverage trading with long/short capabilities

### Data Collection Services
- **`btc_logger.service`**: BTC market condition logging
- **`rolling_indicators_market7.service`**: Technical indicator calculation
- **`rolling_klines_market7.service`**: Price data collection and processing
- **`rolling_indicators_with_lev_market7.service`**: **NEW** - Multi-source leverage-aware indicators
- **`fork_metrics.service`**: Fork performance metrics collection

### Analysis Services
- **`fork_score_filter.service`**: Fork candidate filtering and scoring
- **`generate_tv_screener_ratings.service`**: TradingView screener rating generation
- **`tv_kicker_market7.service`**: TradingView signal processing

### Dashboard Services
- **`market7.service`**: Main dashboard backend API
- **`ml_confidence_cache_market7.service`**: ML confidence score caching

## Service Management

### Restart All Services
```bash
./restart_all.sh
```

### Monitor All Service Logs
```bash
./multilog.sh
```

### Individual Service Management
```bash
# Restart specific service
sudo service <service_name> restart

# Check service status
sudo systemctl status <service_name>

# View service logs
sudo journalctl -u <service_name> -f

# Enable service on boot
sudo systemctl enable <service_name>
```

### New Leverage Service Management
```bash
# Start leverage trading service
sudo systemctl start leverage_trading_market7.service

# Monitor leverage service logs
sudo journalctl -u leverage_trading_market7.service -f

# Check leverage service status
sudo systemctl status leverage_trading_market7.service
```

## Environment Configuration

All services expect environment variables to be loaded from:
- `/home/signal/market7/.env` (if exists)
- System environment variables
- Configuration files in `/home/signal/market7/config/`
- **New**: Leverage-specific configs in `/home/signal/market7/config/leverage_config.yaml`

## Dependencies

### System Dependencies
- Python 3.11+
- Redis server
- systemd
- Virtual environment (optional, can use system Python)

### Python Dependencies
- All requirements specified in `requirements.txt`
- Additional ML libraries for specific services
- **New**: Binance futures API libraries for leverage trading

### New Leverage Dependencies
- **Binance Futures API**: For leverage trading execution
- **Enhanced ML Models**: Updated confidence and recovery models
- **Multi-Source Data**: Support for both spot and futures data streams

## Service Lifecycle

### Startup Order
1. **Data Services First**: `rolling_klines_market7`, `rolling_indicators_market7`, `rolling_indicators_with_lev_market7`
2. **Core Services**: `fork_runner`, `smart_dca_market7`, `fork_safu_monitor`, `leverage_trading_market7`
3. **Analysis Services**: `fork_score_filter`, `tv_kicker_market7`
4. **Dashboard Services**: `market7`, `ml_confidence_cache_market7`

### Health Checks
Each service should implement health check endpoints or signals:
- Redis connectivity
- API endpoint availability
- Data freshness validation
- **New**: Leverage position health monitoring
- **New**: Multi-source data stream validation

## Monitoring and Logging

### Log Locations
- **System Logs**: `journalctl -u <service_name>`
- **Application Logs**: `/home/signal/market7/logs/`
- **DCA Logs**: `/home/signal/market7/dca/logs/`
- **ML Logs**: `/home/signal/market7/ml/logs/`
- **New**: Leverage Logs: `/home/signal/market7/lev/logs/`

### Key Metrics
- Service uptime
- Error rates
- Processing latency
- Resource usage (CPU, memory, disk)
- **New**: Leverage position metrics
- **New**: Multi-source data stream health

## New Leverage Trading Features

### Leverage Service Capabilities
- **Long/Short Support**: Simultaneous long and short positions
- **Futures Integration**: USDT-M perpetual futures trading
- **Enhanced Risk Management**: Liquidation buffer protection
- **ML Integration**: Recovery odds and confidence scoring
- **BTC Market Filtering**: Direction-aware market condition filtering

### Enhanced DCA Guards
- **Confidence DCA Guard**: ML confidence-based DCA protection
- **Step Repeat Guard**: Prevents redundant DCA steps
- **Trailing Step Guard**: Dynamic step spacing based on price movement
- **Spend Guard**: Drawdown-based spend limits with ML adjustment
- **Zombie Tag**: Identifies and manages underperforming trades

## Troubleshooting

### Common Issues
1. **Service fails to start**: Check Python path and dependencies
2. **Redis connection errors**: Verify Redis server is running
3. **Permission issues**: Ensure proper file permissions and user access
4. **Memory issues**: Monitor Python memory usage, especially for ML services
5. **New**: Leverage API errors: Check Binance futures API credentials and limits
6. **New**: Multi-source data issues: Verify spot and futures data availability

### Debug Commands
```bash
# Check service configuration
sudo systemctl cat <service_name>

# Test service manually
sudo systemctl stop <service_name>
sudo -u <user> /usr/bin/python3 <script_path>

# Check service dependencies
sudo systemctl list-dependencies <service_name>

# New: Test leverage service
cd /home/signal/market7/lev
python3 run_lev.py --dry-run --once

# New: Test leverage indicators
cd /home/signal/market7/data
INDICATOR_KLINE_SOURCE=futures python3 rolling_indicators_with_lev.py --once
```

### Leverage-Specific Debugging
```bash
# Check leverage configuration
cat config/leverage_config.yaml

# Verify futures API connectivity
python3 -c "from lev.exchange import futures_adapter as fa; print('Futures API OK')"

# Test leverage decision engine
python3 -c "from lev.modules.lev_decision_engine import should_add_to_position; print('Decision Engine OK')"
```

---

*Note: This service map reflects the current master branch state after the recent merge, including new leverage trading capabilities. Actual `.service` files should be created in `/etc/systemd/system/` or `/etc/systemd/user/` for proper systemd integration. The new leverage services are recommended additions to the existing service infrastructure.*
