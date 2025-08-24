# Market7 ML Model Map

## Overview

This document maps all machine learning models (`.pkl` files) in the Market7 repository, including their file paths, loading locations, required features, and fallback/validation logic. The current master branch includes enhanced DCA guards, leverage trading capabilities, and updated ML model integrations.

## Model Files

### 1. `xgb_recovery_model.pkl` (110KB)
- **File Path**: `/ml/models/xgb_recovery_model.pkl`
- **Model Type**: XGBoost Classifier
- **Purpose**: Predicts recovery probability for DCA positions
- **Where Loaded**:
  - **Primary**: `dca/utils/recovery_odds_utils.py` - `predict_recovery_odds()`
  - **Simulation**: `sim/sandbox3/utils/sim_recovery_odds_utils.py` - `predict_recovery_odds()`
  - **Training**: `ml/recovery/train_recovery_model.py` - Output model
  - **Pipeline**: `ml/shells/run_recovery_pipeline.sh` - Training pipeline
- **Required Features**:
  ```python
  EXPECTED_FEATURES = [
      "step", "entry_score", "current_score", "drawdown_pct", "safu_score",
      "macd_lift", "rsi", "rsi_slope", "adx", "confidence_score", "tp1_shift",
      "safu_good_but_zombie", "snapshot_score_trend", "snapshot_rsi_trend",
      "snapshot_max_drawdown", "snapshot_min_score", "snapshot_min_rsi",
      "snapshot_time_to_max_drawdown_min"
  ]
  ```
- **Fallback/Validation Logic**:
  ```python
  # Load model with error handling
  try:
      model = joblib.load(RECOVERY_MODEL_PATH)
  except Exception as e:
      log.error(f"Failed to load recovery model: {e}")
      return None
  
  # Feature validation
  missing_features = set(EXPECTED_FEATURES) - set(features.keys())
  if missing_features:
      log.warning(f"Missing features for recovery prediction: {missing_features}")
      return None
  
  # Prediction with confidence
  try:
      prob = model.predict_proba([feature_vector])[0][1]
      return float(prob)
  except Exception as e:
      log.error(f"Recovery prediction failed: {e}")
      return None
  ```
- **Training Pipeline**: `ml/shells/run_recovery_pipeline.sh`
- **Feature Engineering**: Recovery-focused features including step progression, score trends, and snapshot analysis
- **Performance**: Binary classification for recovery probability (0.0-1.0)

### 2. `xgb_confidence_model.pkl` (154KB)
- **File Path**: `/ml/models/xgb_confidence_model.pkl`
- **Model Type**: XGBoost Classifier
- **Purpose**: Predicts confidence scores for DCA decisions
- **Where Loaded**:
  - **Primary**: `dca/utils/recovery_confidence_utils.py` - `predict_confidence_score()`
  - **Simulation**: `sim/sandbox3/utils/sim_confidence_utils.py` - `predict_confidence_score()`
  - **Legacy Simulation**: `sim/sandbox/simulate_dca_overlay.py_ML_working` - `predict_confidence_score()`
  - **Training**: `ml/confidence/train_confidence_model.py` - Output model
  - **Pipeline**: `ml/shells/run_confidence_pipeline.sh` - Training pipeline
  - **Auto Pipeline**: `ml/shells/auto_run_confidence_pipeline.sh` - Automated training
- **Required Features**:
  ```python
  FEATURE_COLUMNS = [
      "step", "entry_score", "current_score", "tp1_shift", "safu_score",
      "rsi", "macd_histogram", "adx", "macd_lift", "rsi_slope", "drawdown_pct",
      "snapshot_score_trend", "snapshot_rsi_trend", "snapshot_max_drawdown",
      "snapshot_min_score", "snapshot_min_rsi", "snapshot_time_to_max_drawdown_min"
  ]
  ```
- **Fallback/Validation Logic**:
  ```python
  # Model loading with validation
  try:
      model = joblib.load(MODEL_PATH)
  except Exception as e:
      log.error(f"Failed to load confidence model: {e}")
      return None
  
  # Feature validation and preprocessing
  missing_features = set(FEATURE_COLUMNS) - set(features.keys())
  if missing_features:
      log.warning(f"Missing confidence features: {missing_features}")
      return None
  
  # Prediction with error handling
  try:
      confidence = model.predict_proba([feature_vector])[0][1]
      return float(confidence)
  except Exception as e:
      log.error(f"Confidence prediction failed: {e}")
      return None
  ```
- **Training Pipeline**: `ml/shells/run_confidence_pipeline.sh`
- **Feature Engineering**: Confidence-focused features including step progression, score analysis, and snapshot trends
- **Performance**: Binary classification for confidence probability (0.0-1.0)

### 3. `xgb_spend_model.pkl` (202KB)
- **File Path**: `/ml/models/xgb_spend_model.pkl`
- **Model Type**: XGBoost Regressor
- **Purpose**: Predicts optimal DCA spend amounts based on market conditions
- **Where Loaded**:
  - **Primary**: `dca/utils/spend_predictor.py` - `predict_spend_volume()`
  - **Simulation**: `sim/sandbox3/utils/sim_spend_predictor.py` - `predict_spend_volume()`
  - **Training**: `ml/dca_spend/train_dca_spend_model.py` - Output model
  - **Pipeline**: `ml/shells/run_dca_spend_pipeline.sh` - Training pipeline
- **Required Features**:
  ```python
  BASE_FEATURES = [
      "entry_score", "current_score", "drawdown_pct", "safu_score", "macd_lift",
      "rsi", "rsi_slope", "adx", "tp1_shift", "recovery_odds", "confidence_score",
      "zombie_tagged", "btc_rsi", "btc_macd_histogram", "btc_adx"
  ]
  
  # One-hot encoding for BTC status
  BTC_STATUS_KEYS = [
      "btc_status_bullish", "btc_status_bearish", "btc_status_neutral", "btc_status_nan"
  ]
  ```
- **Fallback/Validation Logic**:
  ```python
  # Model loading with fallback
  try:
      model = joblib.load(MODEL_PATH)
  except Exception as e:
      log.error(f"Failed to load spend model: {e}")
      return None
  
  # Feature preprocessing with BTC status encoding
  feature_vector = []
  for feature in BASE_FEATURES:
      if feature in features:
          feature_vector.append(features[feature])
      else:
          feature_vector.append(0.0)
  
  # Add BTC status one-hot encoding
  btc_status = features.get("btc_status", "nan")
  for status_key in BTC_STATUS_KEYS:
      feature_vector.append(1.0 if status_key.endswith(btc_status) else 0.0)
  
  # Prediction with validation
  try:
      predicted_spend = model.predict([feature_vector])[0]
      return max(0.0, float(predicted_spend))
  except Exception as e:
      log.error(f"Spend prediction failed: {e}")
      return None
  ```
- **Training Pipeline**: `ml/shells/run_dca_spend_pipeline.sh`
- **Feature Engineering**: Spend optimization features including market conditions, BTC status, and position metrics
- **Performance**: Regression for spend amount prediction (continuous values)

### 4. `xgb_dca_spend_model.pkl` (202KB)
- **File Path**: `/ml/models/xgb_dca_spend_model.pkl`
- **Model Type**: XGBoost Regressor
- **Purpose**: Alternative DCA spend prediction model
- **Where Loaded**:
  - **Training**: `ml/dca_spend/train_dca_spend_model.py` - Output model
  - **Pipeline**: `ml/shells/run_dca_spend_pipeline.sh` - Training pipeline
- **Note**: This appears to be a duplicate/alternative to `xgb_spend_model.pkl`
- **Required Features**: Same as `xgb_spend_model.pkl`
- **Fallback/Validation Logic**: Same as `xgb_spend_model.pkl`
- **Training Pipeline**: `ml/shells/run_dca_spend_pipeline.sh`

### 5. `xgb_model.pkl` (147KB)
- **File Path**: `/ml/models/xgb_model.pkl`
- **Model Type**: XGBoost Classifier
- **Purpose**: General-purpose ML model for various predictions
- **Where Loaded**:
  - **Training**: `ml/preprocess/train_model.py` - Output model
  - **Legacy Simulation**: `sim/sandbox/simulate_dca_overlay.py_ML_working` - Recovery prediction
  - **Legacy Simulation**: `sim/sandbox/simulate_dca_overlay.py_FALLBACK_FULLBACKEND_EVAL` - Recovery prediction
- **Required Features**: Based on `ml/models/features_used.json`
- **Fallback/Validation Logic**: Basic model loading and prediction
- **Training Pipeline**: `ml/preprocess/train_model.py`
- **Note**: This appears to be a legacy model, possibly replaced by more specialized models

### 6. `safu_exit_model.pkl` (160KB)
- **File Path**: `/ml/safu/safu_exit_model.pkl`
- **Model Type**: XGBoost Classifier
- **Purpose**: Predicts SAFU (Safe Exit) decisions for risk management
- **Where Loaded**:
  - **Primary**: `dca/modules/fork_safu_evaluator.py` - SAFU evaluation
  - **Training**: `ml/safu/train_safu_classifier.py` - Output model
- **Required Features**: Dynamic feature loading based on available indicators
- **Fallback/Validation Logic**:
  ```python
  # Dynamic model loading
  try:
      model = joblib.load(MODEL_PATH)
  except Exception as e:
      log.error(f"Failed to load SAFU model: {e}")
      return None
  
  # Dynamic feature extraction
  available_features = []
  for feature_name in model.feature_names_in_:
      if feature_name in indicators:
          available_features.append(indicators[feature_name])
      else:
          available_features.append(0.0)
  
  # Prediction with validation
  try:
      safu_prob = model.predict_proba([available_features])[0][1]
      return float(safu_prob)
  except Exception as e:
      log.error(f"SAFU prediction failed: {e}")
      return None
  ```
- **Training Pipeline**: `ml/safu/train_safu_classifier.py`
- **Feature Engineering**: SAFU-specific features for exit decision making
- **Performance**: Binary classification for SAFU probability (0.0-1.0)

## Feature Definitions

### Common Features (from `ml/models/features_used.json`)
```json
[
  "ind_ema50", "ind_rsi", "ind_adx", "ind_atr",
  "ind_stoch_rsi_k", "ind_stoch_rsi_d",
  "ind_macd", "ind_macd_signal", "ind_macd_hist", "ind_macd_hist_prev",
  "ind_macd_lift", "btc_rsi", "btc_adx", "btc_macd_histogram",
  "btc_ema_50", "btc_ema_200", "btc_market_condition_num"
]
```

### Model-Specific Features

#### Recovery Model Features
- **Position Metrics**: `step`, `entry_score`, `current_score`, `drawdown_pct`
- **Risk Metrics**: `safu_score`, `safu_good_but_zombie`
- **Technical Indicators**: `macd_lift`, `rsi`, `rsi_slope`, `adx`
- **Snapshot Analysis**: `snapshot_score_trend`, `snapshot_rsi_trend`, `snapshot_max_drawdown`
- **Time Metrics**: `snapshot_time_to_max_drawdown_min`

#### Confidence Model Features
- **Position Metrics**: `step`, `entry_score`, `current_score`, `tp1_shift`
- **Risk Metrics**: `safu_score`
- **Technical Indicators**: `rsi`, `macd_histogram`, `adx`, `macd_lift`, `rsi_slope`
- **Snapshot Analysis**: `snapshot_score_trend`, `snapshot_rsi_trend`, `snapshot_max_drawdown`

#### Spend Model Features
- **Position Metrics**: `entry_score`, `current_score`, `drawdown_pct`, `tp1_shift`
- **Risk Metrics**: `safu_score`, `zombie_tagged`
- **Technical Indicators**: `macd_lift`, `rsi`, `rsi_slope`, `adx`
- **ML Predictions**: `recovery_odds`, `confidence_score`
- **BTC Context**: `btc_rsi`, `btc_macd_histogram`, `btc_adx`
- **BTC Status**: One-hot encoded status (bullish, bearish, neutral, nan)

## Model Integration Points

### DCA System Integration
- **Recovery Model**: Used in `dca/utils/recovery_odds_utils.py` for DCA decision making
- **Confidence Model**: Used in `dca/utils/recovery_confidence_utils.py` for confidence scoring
- **Spend Model**: Used in `dca/utils/spend_predictor.py` for spend optimization
- **SAFU Model**: Used in `dca/modules/fork_safu_evaluator.py` for exit decisions

### Leverage Trading Integration - **NEW**
- **Recovery Model**: Used in `lev/run_lev.py` for leverage DCA decisions
- **Confidence Model**: Used in `lev/run_lev.py` for leverage confidence scoring
- **Integration Pattern**:
  ```python
  # From lev/run_lev.py
  from dca.utils.recovery_odds_utils import predict_recovery_odds
  from dca.utils.recovery_confidence_utils import predict_confidence_score
  
  # Used in leverage decision making
  rec_odds = predict_recovery_odds(inds) or 0.0
  conf = predict_confidence_score(inds) or 0.0
  ```

### Simulation Integration
- **Recovery Model**: Used in simulation modules for backtesting
- **Confidence Model**: Used in simulation modules for confidence analysis
- **Spend Model**: Used in simulation modules for spend optimization

## Training Pipelines

### Recovery Model Pipeline
```bash
# ml/shells/run_recovery_pipeline.sh
python ml/recovery/train_recovery_model.py \
  --input "$DATASET_PATH" \
  --output "$MODEL_DIR/xgb_recovery_model.pkl"
```

### Confidence Model Pipeline
```bash
# ml/shells/run_confidence_pipeline.sh
python ml/confidence/train_confidence_model.py \
  --input "$DATASET_PATH" \
  --output "$MODELS_DIR/xgb_confidence_model.pkl"
```

### Spend Model Pipeline
```bash
# ml/shells/run_dca_spend_pipeline.sh
python ml/dca_spend/train_dca_spend_model.py \
  --input "$DATASET_PATH" \
  --output "$ML_BASE/models/xgb_dca_spend_model.pkl"
```

### SAFU Model Pipeline
```bash
# ml/safu/train_safu_classifier.py
python ml/safu/train_safu_classifier.py
# Outputs: safu_exit_model.pkl
```

## Model Performance and Validation

### Model Sizes
- **Recovery Model**: 110KB - Lightweight, fast inference
- **Confidence Model**: 154KB - Balanced performance
- **Spend Model**: 202KB - Feature-rich, comprehensive
- **SAFU Model**: 160KB - Risk-focused, specialized

### Validation Strategies
- **Feature Validation**: Check for missing required features
- **Type Validation**: Ensure feature types match expectations
- **Range Validation**: Validate feature value ranges
- **Fallback Logic**: Return None on prediction failures

### Error Handling
- **Model Loading**: Graceful fallback if models are missing
- **Feature Mismatch**: Warning logs for missing features
- **Prediction Errors**: Error logs with fallback values
- **Type Conversion**: Safe conversion to expected types

## Model Dependencies

### Data Dependencies
- **Indicator Data**: Technical indicators from `data/rolling_indicators.py`
- **BTC Context**: Market condition data from `conditions/btc_market_condition.py`
- **Position Data**: Trade data from DCA and fork systems
- **Snapshot Data**: Historical snapshots for trend analysis

### Configuration Dependencies
- **Model Paths**: Defined in `config/paths_config.yaml`
- **Feature Configs**: Feature engineering parameters
- **Training Configs**: Model training hyperparameters
- **Validation Configs**: Model validation thresholds

### Service Dependencies
- **DCA Services**: Primary consumers of ML predictions
- **Leverage Services**: **NEW** - Leverage trading decisions
- **Simulation Services**: Backtesting and analysis
- **Dashboard Services**: Real-time monitoring and display

## Future Enhancements

### Planned Model Updates
- **Leverage-Specific Models**: Models optimized for futures trading
- **Direction-Aware Models**: Separate models for long/short positions
- **Enhanced Feature Engineering**: More sophisticated technical indicators
- **Real-time Model Updates**: Dynamic model retraining

### Model Monitoring
- **Performance Metrics**: Track prediction accuracy over time
- **Feature Drift**: Monitor feature distribution changes
- **Model Drift**: Detect when models need retraining
- **A/B Testing**: Compare model versions in production

---

*This ML model map reflects the current state of Market7 as of the latest commit, including all recent enhancements from the master branch merge such as leverage trading ML integration and enhanced DCA guards. For specific implementation details, refer to the individual model files and their corresponding utility modules.*
