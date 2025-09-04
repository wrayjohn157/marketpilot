#!/usr/bin/env python3
"""
Integrated ML Pipeline Runner - Uses Unified ML Pipeline
Replaces old fragmented ML approach with new unified system
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from config.unified_config_manager import get_path, get_config
from ml.unified_ml_pipeline import MLPipelineManager, ModelType, TrainingConfig
from utils.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class IntegratedMLManager:
    """Integrated ML Manager using Unified ML Pipeline"""
    
    def __init__(self):
        self.ml_manager = None
        self.redis_manager = get_redis_manager()
        self.config = None
        self._load_config()
        self._initialize_ml_manager()
    
    def _load_config(self):
        """Load ML pipeline configuration"""
        try:
            config_data = get_config("ml_pipeline_config")
            self.config = TrainingConfig(
                test_size=config_data.get("test_size", 0.2),
                random_state=config_data.get("random_state", 42),
                n_estimators=config_data.get("n_estimators", 100),
                max_depth=config_data.get("max_depth", 6),
                learning_rate=config_data.get("learning_rate", 0.1)
            )
            logger.info("ML pipeline configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML configuration: {e}")
            # Use default config
            self.config = TrainingConfig()
    
    def _initialize_ml_manager(self):
        """Initialize the ML Pipeline Manager"""
        try:
            self.ml_manager = MLPipelineManager()
            logger.info("ML Pipeline Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML Manager: {e}")
            raise
    
    def train_all_models(self) -> Dict[str, Any]:
        """Train all ML models"""
        logger.info("🚀 Starting Integrated ML Training")
        logger.info("=" * 50)
        
        try:
            results = {
                "models_trained": 0,
                "models_failed": 0,
                "training_results": {},
                "errors": []
            }
            
            # Define models to train
            models_to_train = [
                ModelType.SAFU_EXIT,
                ModelType.RECOVERY_ODDS,
                ModelType.CONFIDENCE_SCORE,
                ModelType.DCA_SPEND,
                ModelType.TRADE_SUCCESS
            ]
            
            for model_type in models_to_train:
                try:
                    logger.info(f"Training {model_type.value} model...")
                    
                    # Train model
                    training_result = self.ml_manager.train_model(
                        model_type=model_type,
                        config=self.config
                    )
                    
                    if training_result.success:
                        results["models_trained"] += 1
                        results["training_results"][model_type.value] = {
                            "accuracy": training_result.accuracy,
                            "precision": training_result.precision,
                            "recall": training_result.recall,
                            "f1_score": training_result.f1_score,
                            "model_path": training_result.model_path
                        }
                        logger.info(f"✅ {model_type.value} model trained successfully")
                    else:
                        results["models_failed"] += 1
                        results["errors"].append(f"{model_type.value}: {training_result.error}")
                        logger.error(f"❌ {model_type.value} model training failed: {training_result.error}")
                    
                except Exception as e:
                    results["models_failed"] += 1
                    results["errors"].append(f"{model_type.value}: {str(e)}")
                    logger.error(f"❌ {model_type.value} model training failed: {e}")
                    continue
            
            # Log results
            logger.info(f"✅ ML Training Complete:")
            logger.info(f"   Models Trained: {results['models_trained']}")
            logger.info(f"   Models Failed: {results['models_failed']}")
            logger.info(f"   Errors: {len(results['errors'])}")
            
            # Save results
            self._save_training_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"ML training failed: {e}")
            raise
    
    def predict_with_models(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions using trained models"""
        try:
            predictions = {}
            
            # Get model types to predict with
            model_types = [
                ModelType.SAFU_EXIT,
                ModelType.RECOVERY_ODDS,
                ModelType.CONFIDENCE_SCORE,
                ModelType.DCA_SPEND,
                ModelType.TRADE_SUCCESS
            ]
            
            for model_type in model_types:
                try:
                    # Make prediction
                    prediction = self.ml_manager.predict(
                        model_type=model_type,
                        data=data
                    )
                    
                    if prediction.success:
                        predictions[model_type.value] = {
                            "prediction": prediction.prediction,
                            "confidence": prediction.confidence,
                            "probability": prediction.probability
                        }
                        logger.debug(f"✅ {model_type.value} prediction: {prediction.prediction}")
                    else:
                        logger.warning(f"⚠️ {model_type.value} prediction failed: {prediction.error}")
                        predictions[model_type.value] = {
                            "error": prediction.error
                        }
                    
                except Exception as e:
                    logger.warning(f"⚠️ {model_type.value} prediction failed: {e}")
                    predictions[model_type.value] = {
                        "error": str(e)
                    }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {}
    
    def run_inference_cycle(self) -> Dict[str, Any]:
        """Run a complete ML inference cycle"""
        logger.info("🚀 Starting ML Inference Cycle")
        logger.info("=" * 50)
        
        try:
            # Get data for inference (this would come from your data sources)
            inference_data = self._get_inference_data()
            
            results = {
                "processed": 0,
                "predictions_made": 0,
                "errors": 0,
                "predictions": []
            }
            
            for data_point in inference_data:
                try:
                    # Make predictions
                    predictions = self.predict_with_models(data_point)
                    
                    result = {
                        "symbol": data_point.get("symbol", "unknown"),
                        "timestamp": int(datetime.utcnow().timestamp()),
                        "predictions": predictions
                    }
                    
                    results["predictions"].append(result)
                    results["processed"] += 1
                    results["predictions_made"] += len([p for p in predictions.values() if "error" not in p])
                    
                except Exception as e:
                    logger.error(f"Error processing data point: {e}")
                    results["errors"] += 1
                    continue
            
            # Log results
            logger.info(f"✅ ML Inference Complete:")
            logger.info(f"   Processed: {results['processed']}")
            logger.info(f"   Predictions Made: {results['predictions_made']}")
            logger.info(f"   Errors: {results['errors']}")
            
            # Save results
            self._save_inference_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"ML inference cycle failed: {e}")
            raise
    
    def _get_inference_data(self) -> List[Dict[str, Any]]:
        """Get data for ML inference"""
        try:
            # This would get data from your data sources
            # For now, return sample data
            sample_data = [
                {
                    "symbol": "BTCUSDT",
                    "price": 45000.0,
                    "volume": 1000.0,
                    "rsi": 65.5,
                    "macd": 0.001,
                    "adx": 25.3
                }
            ]
            return sample_data
        except Exception as e:
            logger.error(f"Failed to get inference data: {e}")
            return []
    
    def _save_training_results(self, results: Dict[str, Any]) -> None:
        """Save training results to file"""
        try:
            results_file = get_path("models") / f"training_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Training results saved to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save training results: {e}")
    
    def _save_inference_results(self, results: Dict[str, Any]) -> None:
        """Save inference results to file"""
        try:
            results_file = get_path("models") / f"inference_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Inference results saved to {results_file}")
        except Exception as e:
            logger.error(f"Failed to save inference results: {e}")

def main():
    """Main function - run the integrated ML system"""
    try:
        # Initialize ML manager
        ml_manager = IntegratedMLManager()
        
        # Choose mode: training or inference
        import sys
        mode = sys.argv[1] if len(sys.argv) > 1 else "inference"
        
        if mode == "train":
            # Run training
            results = ml_manager.train_all_models()
        else:
            # Run inference
            results = ml_manager.run_inference_cycle()
        
        logger.info("🎉 Integrated ML System complete")
        return results
        
    except Exception as e:
        logger.error(f"Integrated ML System failed: {e}")
        raise

if __name__ == "__main__":
    main()