# Market7 Configuration Map

## Overview

This document maps all configuration files (YAML and JSON) in the Market7 repository, including their loader scripts, usage patterns, and critical configuration keys. The current master branch includes new leverage trading capabilities, enhanced DCA guards, and advanced risk management features.

## Configuration Files

### Core Configuration Files

#### 1. `config/paths_config.yaml`
- **Loader Script**: `config/config_loader.py`
- **Modules/Functions Using It**:
  - `config_loader.py` (PATHS global)
  - `dashboard_backend/main.py`
  - `dashboard_backend/ml_confidence_api.py`
  - `dashboard_backend/refresh_price_api.py`
  - `dashboard_backend/cache_writer.py`
  - `dashboard_backend/api_control_router.py`
  - `dashboard_backend/threecommas_metrics.py`
  - `dashboard_backend/unified_fork_metrics.py`
  - `dashboard_backend/dca_status.py`
  - `dashboard_backend/ml_confidence_cache_writer.py`
  - `dca/smart_dca_signal.py`
  - `dca/utils/zombie_utils.py`
  - `dca/utils/trade_health_evaluator.py`
  - `fork/fork_runner.py`
  - `fork/utils/entry_utils.py`
  - `fork/utils/fork_entry_utils.py`
  - `fork/modules/fork_safu_monitor.py`
  - `indicators/fork_score_filter.py`
  - `indicators/fork_pipeline_runner.py`
  - `indicators/tv_kicker.py`
  - `indicators/store_indicators.py`
  - `indicators/rrr_filter.py`
  - `indicators/rrr_filter/tv_puller.py`
  - `indicators/rrr_filter/generate_tv_screener_ratings.py`
  - `indicators/rrr_filter/tv_screener_score.py`
  - `data/rolling_klines.py`
  - `data/rolling_indicators.py`
  - `data/rolling_indicators_with_lev.py`
  - `data/volume_filter.py`
  - `sim/sandbox/modules/sim_core_engine.py`
  - `sim/dca/core.py`
  - `sim/sandbox/core.py`
  - `sim/sandbox/utils/core.py`
  - `sim/sandbox3/core/sim_dca_engine.py`
  - `sim/sandbox3/sim_dca_runner.py`
  - `ml/dca_spend/build_dca_spend_dataset.py`
  - `strat/runner/run_fork_strategy.py`
  - `lev/run_lev.py`
  - `lev/exchange/futures_adapter.py`
- **Critical Keys**:
  - `base_path`: Root project directory
  - `snapshots_path`: Data snapshots location
  - `fork_history_path`: Fork trade history
  - `btc_logs_path`: BTC market condition logs
  - `live_logs_path`: Live trading logs
  - `models_path`: ML model storage
  - `paper_cred_path`: Paper trading credentials
  - `dashboard_cache`: Dashboard cache directory
  - `dca_config`: DCA configuration path
  - `fork_safu_config`: SAFU configuration path

#### 2. `config/dca_config.yaml` - **ENHANCED**
- **Loader Script**: Direct YAML loading in `dca/smart_dca_signal.py`
- **Modules/Functions Using It**:
  - `dca/smart_dca_signal.py`
  - `dca/utils/trade_health_evaluator.py`
  - `dca/utils/zombie_utils.py`
  - `dashboard_backend/config_routes/dca_config_api.py`
  - `dashboard_frontend/src/components/ConfigPanels/DcaConfigPanel.jsx`
- **Critical Toggles/Keys**:
  - `max_trade_usdt`: Maximum trade size (2000)
  - `base_order_usdt`: Base order size (200)
  - `drawdown_trigger_pct`: DCA trigger threshold (1.2%)
  - `safu_score_threshold`: SAFU exit threshold (0.5)
  - `use_btc_filter`: BTC market filtering (false)
  - `use_ml_spend_model`: ML spend prediction (true)
  - `use_confidence_override`: Confidence override (true)
  - **NEW DCA Guards**:
    - `confidence_dca_guard`: ML confidence-based DCA protection
      - `safu_score_min`: 0.5
      - `macd_lift_min`: 5.0e-05
      - `rsi_slope_min`: 1
      - `confidence_score_min`: 0.75
      - `min_confidence_delta`: 0.1
      - `min_tp1_shift_gain_pct`: 1.5
    - `step_repeat_guard`: Prevents redundant DCA steps
      - `enabled`: true
      - `min_conf_delta`: 0.1
      - `min_tp1_delta`: 1.5
      - `min_price_delta_pct`: 0.5
    - `trailing_step_guard`: Dynamic step spacing
      - `enabled`: true
      - `min_pct_gap_from_last_dca`: 2.0
    - `spend_guard`: Drawdown-based spend limits
      - `enabled`: true
      - `drawdown_thresholds`: Progressive spend limits by drawdown %
    - `zombie_tag`: Identifies underperforming trades
      - `enabled`: true
      - `min_drawdown_pct`: 0.5
      - `max_drawdown_pct`: 5
      - `max_score`: 0.3
      - `require_zero_recovery_odds`: true
  - **Enhanced Features**:
    - `bottom_reversal_trigger`: Local reversal detection
    - `adaptive_step_spacing`: Dynamic step timing
    - `enforce_price_below_last_step`: Price validation

#### 3. `config/leverage_config.yaml` - **NEW**
- **Loader Script**: Direct YAML loading in `lev/run_lev.py`
- **Modules/Functions Using It**:
  - `lev/run_lev.py`
  - `lev/modules/lev_decision_engine.py`
  - `lev/exchange/futures_adapter.py`
- **Critical Toggles/Keys**:
  - **Trading Mode**:
    - `enabled`: true
    - `exchange`: binance_futures
    - `margin_mode`: isolated
    - `hedged_mode`: true (simultaneous long/short)
    - `max_leverage`: 5
    - `liquidation_buffer_pct`: 6.0
  - **Entry Source**:
    - `entry_source.mode`: manual/fork
    - `entry_source.tv_enabled`: false
    - `entry_source.backfill_days`: 0
  - **Short Entry Tuning**:
    - `short_entry.use_fork_inversion`: true
    - `short_entry.rsi_max`: 70
    - `short_entry.macd_hist_max`: 0.0000
    - `short_entry.ema_trend`: below_emas
  - **Risk Management**:
    - `max_trade_notional`: 10000
    - `max_account_notional`: 50000
    - `base_order_usdt`: 200
    - `so_notional_table`: [1000, 1500, 2500, 4000]
  - **DCA Gates**:
    - `drawdown_trigger_pct`: 1.2
    - `require_indicator_health`: true
    - `indicator_thresholds.rsi_min`: 35
    - `indicator_thresholds.macd_hist_min`: -0.0002
    - `indicator_thresholds.adx_min`: 10
  - **ML Integration**:
    - `use_trajectory_check`: false
    - `require_recovery_odds`: true
    - `min_recovery_probability`: 0.5
  - **Fork/TV Integration**:
    - `fork_gate`: true
    - `tv_gate`: true
    - `fork_min_long`: 0.60
    - `fork_max_short`: 0.40
    - `tv_bull`: ["buy"]
    - `tv_bear`: ["sell"]

#### 4. `config/binance_futures_testnet.json` - **NEW**
- **Loader Script**: Direct JSON loading in leverage modules
- **Modules/Functions Using It**:
  - `lev/exchange/futures_adapter.py`
  - `lev/run_lev.py`
- **Critical Keys**:
  - `api_key`: Binance futures API key
  - `api_secret`: Binance futures API secret
  - `testnet`: true
  - `type`: usdtm
  - `default_leverage`: 5
  - `is_cross_margin`: false

#### 5. `config/fork_score_config.yaml`
- **Loader Script**: Direct YAML loading in `indicators/fork_score_filter.py`
- **Modules/Functions Using It**:
  - `indicators/fork_score_filter.py`
  - `dashboard_backend/config_routes/fork_score_config_api.py`
  - `core/fork_scorer.py`
- **Critical Toggles/Keys**:
  - `min_score`: Minimum fork score (0.85)
  - `weights`: Scoring weights for indicators
    - `macd_histogram`: 0.2
    - `rsi_recovery`: 0.2
    - `ema_price_reclaim`: 0.15
    - `mean_reversion_score`: 0.2
  - `options.use_stoch_ob_penalty`: Stochastic overbought penalty (true)
  - `options.use_volume_penalty`: Volume penalty (true)

#### 6. `config/fork_safu_config.yaml`
- **Loader Script**: Direct YAML loading in `dca/modules/fork_safu_evaluator.py`
- **Modules/Functions Using It**:
  - `dca/modules/fork_safu_evaluator.py`
  - `fork/modules/fork_safu_monitor.py`
  - `dashboard_backend/config_routes/safu_config_api.py`
  - `sim/sandbox3/utils/sim_safu_utils.py`
- **Critical Toggles/Keys**:
  - `min_score`: Minimum SAFU score (0.4)
  - `telegram_alerts`: Alert notifications (false)
  - `auto_close`: Automatic position closing (false)
  - `safu_reentry.enabled`: Re-entry after SAFU (true)
  - `safu_reentry.cooldown_minutes`: Re-entry cooldown (30)
  - `weights`: SAFU scoring weights for various conditions

#### 7. `config/tv_screener_config.yaml`
- **Loader Script**: Direct YAML loading in `indicators/tv_kicker.py`
- **Modules/Functions Using It**:
  - `indicators/tv_kicker.py`
  - `fork/fork_runner.py`
  - `dashboard_backend/config_routes/tv_screener_config_api.py`
- **Critical Toggles/Keys**:
  - `tv_screener.enabled`: TradingView screener (true)
  - `disable_if_btc_unhealthy`: BTC health dependency (true)
  - `score_threshold`: Minimum screener score (0.73)
  - `weights`: Rating weights
    - `strong_buy`: 0.5
    - `buy`: 0.25
    - `sell`: -0.2
    - `strong_sell`: -0.3

#### 8. `config/fork_filter_config.yaml`
- **Loader Script**: Direct YAML loading in `indicators/fork_score_filter.py`
- **Modules/Functions Using It**:
  - `indicators/fork_score_filter.py`
- **Critical Toggles/Keys**:
  - `min_score`: Minimum filter score (3)
  - `weights`: Filter weights
    - `macd_near_signal`: 1
    - `macd_hist_rising`: 1
    - `rsi_recovery`: 2
    - `stoch_oversold`: 2

#### 9. `config/default_dca_config.yaml`
- **Loader Script**: Direct YAML loading in simulation modules
- **Modules/Functions Using It**:
  - `sim/sandbox/modules/sim_core_engine.py`
  - `sim/dca/core.py`
  - `sim/sandbox/core.py`
  - `sim/sandbox3/sim_dca_runner.py`
- **Critical Toggles/Keys**: Same as `dca_config.yaml`

### Leverage-Specific Configuration Files

#### 10. `lev/signals/config/fork_config.yaml` - **NEW**
- **Loader Script**: Direct YAML loading in leverage fork modules
- **Modules/Functions Using It**:
  - `lev/signals/fork_score_filter.py`
  - `lev/signals/fork_runner.py`
- **Critical Toggles/Keys**:
  - **Long/Short Scoring**:
    - `min_score_long`: 0.35
    - `min_score_short`: 0.35
  - **Direction-Specific Weights**:
    - `weights_long`: Optimized for long positions
    - `weights_short`: Inverted weights for short positions
  - **Options**:
    - `use_volume_penalty`: true
    - `use_btc_multiplier`: true

#### 11. `lev/signals/config/tv_screener_config.yaml` - **NEW**
- **Loader Script**: Direct YAML loading in leverage TV modules
- **Modules/Functions Using It**:
  - `lev/signals/tv_kicker_lev.py`
  - `lev/run_lev.py`
- **Critical Toggles/Keys**:
  - **Side-Specific Weights**:
    - `weights_long`: Optimized for long signals
    - `weights_short`: Inverted for short signals
  - **Thresholds**:
    - `score_threshold_long`: 0.45
    - `score_threshold_short`: 0.35
  - **Data Source**:
    - `default_tv_file`: TV screener raw data path

#### 12. `lev/signals/config/leverage_config.yaml`
- **Loader Script**: Direct YAML loading in leverage modules
- **Modules/Functions Using It**:
  - `lev/modules/lev_decision_engine.py`
- **Critical Toggles/Keys**: Same as main `leverage_config.yaml`

### Strategy Configuration Files

#### 13. `strat/strategies/example_strategy.yaml`
- **Loader Script**: `strat/utils/strategy_loader.py`
- **Modules/Functions Using It**:
  - `strat/utils/strategy_loader.py`
  - `strat/runner/run_fork_strategy.py`
- **Critical Toggles/Keys**:
  - `min_score`: Strategy score threshold (0.73)
  - `weights`: Strategy-specific indicator weights
  - `options`: Strategy options and penalties

#### 14. `strat/strategies/rawtest_strategy.yaml`
- **Loader Script**: `strat/utils/strategy_loader.py`
- **Modules/Functions Using It**:
  - `strat/utils/strategy_loader.py`
- **Critical Toggles/Keys**:
  - `min_score`: Strategy score threshold (0.7)
  - `weights`: Simple weight structure
    - `MACD_Histogram`: 0.5
    - `RSI14`: 0.3
    - `StochRSI_K`: 0.2

### Ideas/Experimental Configuration Files

#### 15. `ideas/config/confidence_safeguard.yaml`
- **Loader Script**: `ideas/strategy_loader.py`
- **Modules/Functions Using It**:
  - `ideas/smart_dca_signal.py`
  - `ideas/back_test/back_test_runner.py`
  - `ideas/fork_score/run_fork_strategy.py`
  - `ideas/fork_score/fork_score_filter.py`
- **Critical Toggles/Keys**:
  - `indicators`: Minimum indicator thresholds
  - `trajectory.use`: Trajectory checking (true)
  - `safu.min_score`: SAFU threshold (0.6)
  - `ml_rules.use_confidence`: ML confidence (true)
  - `tp1.require_feasibility`: TP1 feasibility (true)
  - `zombie_protection`: Zombie protection (true)

### Empty/Placeholder Configuration Files

#### 16. `config/strategy_config.yaml`
- **Status**: Empty file
- **Purpose**: Placeholder for strategy configuration

#### 17. `config/fork_config.yaml`
- **Status**: Empty file
- **Purpose**: Placeholder for fork configuration

## Configuration Loading Patterns

### Primary Loaders

#### `config/config_loader.py`
- **Purpose**: Centralized path configuration management
- **Usage**: Imported as `PATHS` global variable
- **Scope**: All modules requiring file paths

#### `strat/utils/strategy_loader.py`
- **Purpose**: Strategy configuration loading
- **Usage**: Loads strategy YAML files from `/strat/strategies/`
- **Scope**: Strategy execution and backtesting

### Direct YAML Loading
Many modules load their specific configs directly:
```python
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)
```

### Configuration API Routes
Dashboard backend provides API endpoints for config management:
- `dca_config_api.py`: DCA configuration CRUD
- `fork_score_config_api.py`: Fork scoring configuration
- `safu_config_api.py`: SAFU configuration
- `tv_screener_config_api.py`: TradingView screener configuration

## Critical Configuration Dependencies

### DCA System Dependencies
- **DCA Config** → **Smart DCA Signal** → **Trade Execution**
- **Enhanced DCA Guards** → **Risk Management** → **Capital Protection**
- **Fork SAFU Config** → **Exit Decisions** → **Risk Management**
- **BTC Filter Config** → **Market Condition Filtering**

### Fork Detection Dependencies
- **Fork Score Config** → **Entry Filtering** → **Signal Generation**
- **TV Screener Config** → **External Signal Integration**
- **Fork Filter Config** → **Secondary Filtering**

### Leverage Trading Dependencies - **NEW**
- **Leverage Config** → **Futures Trading** → **Position Management**
- **Leverage Fork Config** → **Direction-Aware Scoring** → **Long/Short Signals**
- **Leverage TV Config** → **Direction-Aware TV Signals** → **Entry Decisions**
- **Futures Credentials** → **API Access** → **Trade Execution**

### ML Pipeline Dependencies
- **Paths Config** → **Dataset Locations** → **Model Training**
- **Model Paths** → **Inference Services** → **Real-time Scoring**

## Configuration Validation

### Required Fields
- **DCA Config**: `max_trade_usdt`, `base_order_usdt`, `drawdown_trigger_pct`
- **Fork Score Config**: `min_score`, `weights`
- **Paths Config**: `base`, `snapshots`, `models`, `btc_logs`
- **Leverage Config**: `enabled`, `exchange`, `max_leverage`, `liquidation_buffer_pct`

### Default Values
- **DCA Config**: Uses `default_dca_config.yaml` as fallback
- **Strategy Config**: Uses `example_strategy.yaml` as template
- **Paths Config**: Hardcoded defaults in `config_loader.py`
- **Leverage Config**: Testnet defaults for development

## Environment-Specific Configurations

### Production vs Development
- **Paper Trading**: Uses `paper_cred.json` for API credentials
- **Live Trading**: Uses live API credentials
- **Simulation**: Uses `sim/config/` directory for test configurations
- **Leverage Trading**: Uses `binance_futures_testnet.json` for futures API

### Configuration Overrides
- **DCA Config**: Multiple variants (`_move_trade`, `_no_respect`)
- **Strategy Config**: Dynamic loading based on strategy name
- **Simulation Config**: Separate configs for different simulation scenarios
- **Leverage Config**: Side-specific configurations for long/short

## Security Considerations

### Credential Files
- **`paper_cred.json`**: API keys for paper trading
- **`dca/config/cred.json`**: DCA-specific credentials
- **`binance_futures_testnet.json`**: **NEW** - Futures API credentials
- **`.gitignore`**: Prevents credential files from being committed

### Configuration Access
- **Dashboard API**: Provides secure config management
- **File Permissions**: Config files should have restricted access
- **Environment Variables**: Sensitive configs can use env vars

## Configuration Management Best Practices

### Version Control
- **Template Files**: Keep example configs in version control
- **Credential Files**: Never commit actual credentials
- **Config Variants**: Use descriptive suffixes for different environments
- **Leverage Configs**: Separate configs for different trading directions

### Validation
- **Schema Validation**: Consider adding YAML schema validation
- **Required Fields**: Document and validate required configuration keys
- **Type Checking**: Ensure configuration values match expected types
- **Direction Validation**: Validate long/short specific configurations

### Monitoring
- **Config Changes**: Log configuration changes for audit trails
- **Validation Errors**: Alert on configuration validation failures
- **Runtime Updates**: Support hot-reloading of configuration changes
- **Leverage Monitoring**: Monitor leverage-specific configuration changes

## New Features and Capabilities

### Enhanced DCA Guards
- **Confidence DCA Guard**: ML confidence-based DCA protection
- **Step Repeat Guard**: Prevents redundant DCA steps
- **Trailing Step Guard**: Dynamic step spacing based on price movement
- **Spend Guard**: Drawdown-based spend limits with ML adjustment
- **Zombie Tag**: Identifies and manages underperforming trades

### Leverage Trading System
- **Long/Short Support**: Direction-aware configurations
- **Futures Integration**: Binance USDT-M perpetual futures
- **Risk Management**: Liquidation buffer protection
- **ML Integration**: Recovery odds and confidence scoring
- **Direction-Aware Filtering**: BTC market condition filtering for both directions

### Multi-Source Data Processing
- **Spot and Futures**: Intelligent source selection
- **Auto-Detection**: Optimal market source identification
- **Leverage Awareness**: Perpetual futures symbol handling
- **Enhanced Indicators**: Leverage-aware technical indicators

---

*This configuration map reflects the current state of Market7 as of the latest commit, including all recent enhancements from the master branch merge such as leverage trading capabilities and enhanced DCA guards. For specific implementation details, refer to the individual configuration files and their corresponding loader scripts.*
