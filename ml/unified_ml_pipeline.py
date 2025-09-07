#!/usr/bin/env python3

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import classification_report, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

from config.unified_config_manager import (  # ML Libraries
    ML,
    Infrastructure,
    Learning,
    Machine,
    Pipeline,
    Replaces,
    SAAS-Ready,
    Unified,
    """,
    -,
    fragmented,
    from,
    get_3commas_credentials,
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
    import,
    multi-tenant,
    scalable,
    scripts,
    sklearn.metrics,
    system,
    unified,
    utils.credential_manager,
    with,
)


# Configuration
class ModelType(Enum):
    SAFU_EXIT = "safu_exit"
    RECOVERY_ODDS = "recovery_odds"
    CONFIDENCE_SCORE = "confidence_score"
    DCA_SPEND = "dca_spend"
    TRADE_SUCCESS = "trade_success"


class DataSource(Enum):
    THREECOMMAS = "3commas"
    REDIS = "redis"
    FILE = "file"
    API = "api"


@dataclass
class ModelConfig:
    model_type: ModelType
    tenant_id: str
    features: List[str]
    target_column: str
    model_params: Dict[str, Any]
    validation_split: float = 0.2
    test_split: float = 0.2
    random_state: int = 42
    enable_shap: bool = True
    enable_cross_validation: bool = True


@dataclass
class TrainingResult:
    model_id: str
    model_type: ModelType
    tenant_id: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    r2_score: Optional[float] = None
    mse: Optional[float] = None
    feature_importance: Dict[str, float] = None
    training_time: float = 0.0
    created_at: datetime = None


@dataclass
class DataQualityReport:
    total_rows: int
    missing_values: Dict[str, int]
    data_types: Dict[str, str]
    outliers: Dict[str, int]
    quality_score: float
    issues: List[str]


class DataValidator:
    """Comprehensive data validation for ML pipelines"""

    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame, required_columns: List[str]
    ) -> DataQualityReport:
        """Validate DataFrame and return quality report"""
        issues = []

        # Check required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")

        # Check data types
        data_types = df.dtypes.to_dict()

        # Check missing values
        missing_values = df.isnull().sum().to_dict()

        # Check outliers (using IQR method)
        outliers = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers[col] = len(df[(df[col] < lower_bound) | (df[col] > upper_bound)])

        # Calculate quality score
        quality_score = 1.0
        if missing_cols:
            quality_score -= 0.3
        if any(missing_values.values()):
            quality_score -= 0.2
        if any(outliers.values()):
            quality_score -= 0.1

        quality_score = max(0.0, quality_score)

        return DataQualityReport(
            total_rows=len(df),
            missing_values=missing_values,
            data_types=data_types,
            outliers=outliers,
            quality_score=quality_score,
            issues=issues,
        )

    @staticmethod
    def clean_data(df: pd.DataFrame, config: ModelConfig) -> pd.DataFrame:
        """Clean and preprocess data for training"""
        df_clean = df.copy()

        # Remove rows with missing target values
        df_clean = df_clean.dropna(subset=[config.target_column])

        # Handle missing values in features
        for col in config.features:
            if col in df_clean.columns:
                if df_clean[col].dtype in ["object", "category"]:
                    df_clean[col] = df_clean[col].fillna("unknown")
                else:
                    df_clean[col] = df_clean[col].fillna(df_clean[col].median())

        # Remove outliers for numerical columns
        for col in config.features:
            if col in df_clean.columns and df_clean[col].dtype in ["int64", "float64"]:
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_clean = df_clean[
                    (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
                ]

        return df_clean


class DataManager:
    """Unified data management for ML pipelines"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.base_path = Path(get_path("base")) / "ml" / "datasets" / tenant_id
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def pull_3commas_data(
        self, bot_id: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Pull data from 3Commas API"""
        try:
            creds = get_3commas_credentials()
            # Implementation would go here
            # For now, return empty DataFrame
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Failed to pull 3Commas data: {e}")
            return pd.DataFrame()

    async def load_dataset(
        self, dataset_name: str, version: str = "latest"
    ) -> pd.DataFrame:
        """Load dataset from storage"""
        dataset_path = self.base_path / f"{dataset_name}_{version}.jsonl"

        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        try:
            data = []
            with open(dataset_path, "r") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))

            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"Failed to load dataset {dataset_name}: {e}")
            return pd.DataFrame()

    async def save_dataset(
        self, df: pd.DataFrame, dataset_name: str, version: str = None
    ) -> str:
        """Save dataset to storage"""
        if version is None:
            version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        dataset_path = self.base_path / f"{dataset_name}_{version}.jsonl"

        try:
            df.to_json(dataset_path, orient="records", lines=True, date_format="iso")
            return str(dataset_path)
        except Exception as e:
            logging.error(f"Failed to save dataset {dataset_name}: {e}")
            raise


class FeatureStore:
    """Feature store for ML pipelines"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.feature_path = Path(get_path("base")) / "ml" / "features" / tenant_id
        self.feature_path.mkdir(parents=True, exist_ok=True)

    def compute_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute technical indicators as features"""
        df_features = df.copy()

        # RSI features
        if "rsi" in df.columns:
            df_features["rsi_oversold"] = (df["rsi"] < 30).astype(int)
            df_features["rsi_overbought"] = (df["rsi"] > 70).astype(int)
            df_features["rsi_momentum"] = df["rsi"].diff()

        # MACD features
        if "macd_histogram" in df.columns:
            df_features["macd_bullish"] = (df["macd_histogram"] > 0).astype(int)
            df_features["macd_momentum"] = df["macd_histogram"].diff()

        # ADX features
        if "adx" in df.columns:
            df_features["adx_strong"] = (df["adx"] > 25).astype(int)
            df_features["adx_weak"] = (df["adx"] < 20).astype(int)

        # Price features
        if "current_price" in df.columns and "avg_entry_price" in df.columns:
            df_features["price_ratio"] = df["current_price"] / df["avg_entry_price"]
            df_features["price_deviation"] = (
                df["current_price"] - df["avg_entry_price"]
            ) / df["avg_entry_price"]

        return df_features

    def get_feature_list(self, model_type: ModelType) -> List[str]:
        """Get feature list for specific model type"""
        base_features = [
            "entry_score",
            "current_score",
            "safu_score",
            "recovery_odds",
            "confidence_score",
            "rsi",
            "macd_histogram",
            "adx",
            "tp1_shift",
            "be_improvement",
            "drawdown_pct",
            "macd_lift",
            "rsi_slope",
        ]

        if model_type == ModelType.SAFU_EXIT:
            return base_features + ["btc_rsi", "btc_adx", "btc_macd_histogram"]
        elif model_type == ModelType.DCA_SPEND:
            return base_features + ["zombie_tagged", "btc_status"]
        else:
            return base_features


class ModelRegistry:
    """Model registry for versioning and management"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.registry_path = Path(get_path("base")) / "ml" / "models" / tenant_id
        self.registry_path.mkdir(parents=True, exist_ok=True)

    def register_model(
        self, model: Any, config: ModelConfig, result: TrainingResult
    ) -> str:
        """Register model in registry"""
        model_id = f"{config.model_type.value}_{config.tenant_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        # Save model
        model_path = self.registry_path / f"{model_id}.pkl"
        joblib.dump(model, model_path)

        # Save metadata
        metadata = {
            "model_id": model_id,
            "model_type": config.model_type.value,
            "tenant_id": config.tenant_id,
            "config": asdict(config),
            "result": asdict(result),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model_path": str(model_path),
        }

        metadata_path = self.registry_path / f"{model_id}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return model_id

    def get_model(self, model_id: str) -> Tuple[Any, Dict[str, Any]]:
        """Get model and metadata from registry"""
        metadata_path = self.registry_path / f"{model_id}_metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Model {model_id} not found")

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        model_path = Path(metadata["model_path"])
        model = joblib.load(model_path)

        return model, metadata


class MLPipeline:
    """Unified ML pipeline for all model types"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.data_manager = DataManager(tenant_id)
        self.feature_store = FeatureStore(tenant_id)
        self.model_registry = ModelRegistry(tenant_id)
        self.validator = DataValidator()

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format=f"%(asctime)s [%(levelname)s] {tenant_id}: %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    async def train_model(
        self, config: ModelConfig, dataset_name: str
    ) -> TrainingResult:
        """Train model with unified pipeline"""
        start_time = datetime.now(timezone.utc)

        try:
            # Load data
            self.logger.info(f"Loading dataset: {dataset_name}")
            df = await self.data_manager.load_dataset(dataset_name)

            if df.empty:
                raise ValueError("Empty dataset")

            # Compute features
            self.logger.info("Computing features")
            df_features = self.feature_store.compute_technical_features(df)

            # Validate data
            self.logger.info("Validating data")
            quality_report = self.validator.validate_dataframe(
                df_features, config.features
            )

            if quality_report.quality_score < 0.5:
                raise ValueError(
                    f"Data quality too low: {quality_report.quality_score}"
                )

            # Clean data
            self.logger.info("Cleaning data")
            df_clean = self.validator.clean_data(df_features, config)

            # Prepare features and target
            X = df_clean[config.features]
            y = df_clean[config.target_column]

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_split, random_state=config.random_state
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            self.logger.info("Training model")
            if config.model_type in [
                ModelType.SAFU_EXIT,
                ModelType.RECOVERY_ODDS,
                ModelType.TRADE_SUCCESS,
            ]:
                model = xgb.XGBClassifier(**config.model_params)
            else:
                model = xgb.XGBRegressor(**config.model_params)

            model.fit(X_train_scaled, y_train)

            # Evaluate model
            self.logger.info("Evaluating model")
            y_pred = model.predict(X_test_scaled)

            # Calculate metrics
            if config.model_type in [
                ModelType.SAFU_EXIT,
                ModelType.RECOVERY_ODDS,
                ModelType.TRADE_SUCCESS,
            ]:
                    accuracy_score,
                    f1_score,
                    precision_score,
                    recall_score,
                )

                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average="weighted")
                recall = recall_score(y_test, y_pred, average="weighted")
                f1 = f1_score(y_test, y_pred, average="weighted")
                r2_score_val = None
                mse = None
            else:
                accuracy = None
                precision = None
                recall = None
                f1 = None
                r2_score_val = r2_score(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)

            # Feature importance
            feature_importance = dict(zip(config.features, model.feature_importances_))

            # Create result
            result = TrainingResult(
                model_id="",  # Will be set by registry
                model_type=config.model_type,
                tenant_id=self.tenant_id,
                accuracy=accuracy or 0.0,
                precision=precision or 0.0,
                recall=recall or 0.0,
                f1_score=f1 or 0.0,
                r2_score=r2_score_val,
                mse=mse,
                feature_importance=feature_importance,
                training_time=(datetime.now(timezone.utc) - start_time).total_seconds(),
                created_at=datetime.now(timezone.utc),
            )

            # Register model
            model_id = self.model_registry.register_model(model, config, result)
            result.model_id = model_id

            self.logger.info(f"Model training completed: {model_id}")
            return result

        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            raise

    async def predict(self, model_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using trained model"""
        try:
            model, metadata = self.model_registry.get_model(model_id)

            # Prepare features
            feature_df = pd.DataFrame([features])
            feature_df = self.feature_store.compute_technical_features(feature_df)

            # Select required features
            required_features = metadata["config"]["features"]
            X = feature_df[required_features]

            # Scale features (would need to load scaler)
            # For now, assume features are already scaled

            # Make prediction
            prediction = model.predict(X)[0]
            probability = None

            if hasattr(model, "predict_proba"):
                probability = model.predict_proba(X)[0].tolist()

            return {
                "prediction": prediction,
                "probability": probability,
                "model_id": model_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            raise


class MLPipelineManager:
    """Manager for multiple ML pipelines across tenants"""

    def __init__(self):
        self.pipelines = {}
        self.logger = logging.getLogger(__name__)

    def get_pipeline(self, tenant_id: str) -> MLPipeline:
        """Get or create pipeline for tenant"""
        if tenant_id not in self.pipelines:
            self.pipelines[tenant_id] = MLPipeline(tenant_id)
        return self.pipelines[tenant_id]

    async def train_model(
        self, tenant_id: str, config: ModelConfig, dataset_name: str
    ) -> TrainingResult:
        """Train model for specific tenant"""
        pipeline = self.get_pipeline(tenant_id)
        return await pipeline.train_model(config, dataset_name)

    async def predict(
        self, tenant_id: str, model_id: str, features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make prediction for specific tenant"""
        pipeline = self.get_pipeline(tenant_id)
        return await pipeline.predict(model_id, features)


# Example usage and configuration
async def main():
    """Example usage of unified ML pipeline"""

    # Initialize pipeline manager
    manager = MLPipelineManager()

    # Example configuration for SAFU exit model
    config = ModelConfig(
        model_type=ModelType.SAFU_EXIT,
        tenant_id="tenant_001",
        features=[
            "entry_score",
            "current_score",
            "safu_score",
            "recovery_odds",
            "confidence_score",
            "rsi",
            "macd_histogram",
            "adx",
            "tp1_shift",
            "be_improvement",
            "drawdown_pct",
            "macd_lift",
            "rsi_slope",
        ],
        target_column="safu_label",
        model_params={
            "n_estimators": 100,
            "max_depth": 4,
            "learning_rate": 0.1,
            "random_state": 42,
        },
    )

    # Train model
    result = await manager.train_model("tenant_001", config, "safu_training_data")
    print(f"Model trained: {result.model_id}")
    print(f"Accuracy: {result.accuracy:.4f}")

    # Make prediction
    features = {
        "entry_score": 0.8,
        "current_score": 0.6,
        "safu_score": 0.7,
        "recovery_odds": 0.75,
        "confidence_score": 0.8,
        "rsi": 45,
        "macd_histogram": 0.001,
        "adx": 25,
        "tp1_shift": 2.5,
        "be_improvement": 1.5,
        "drawdown_pct": 3.0,
        "macd_lift": 0.0005,
        "rsi_slope": 1.2,
    }

    prediction = await manager.predict("tenant_001", result.model_id, features)
    print(f"Prediction: {prediction}")


if __name__ == "__main__":
    asyncio.run(main())
