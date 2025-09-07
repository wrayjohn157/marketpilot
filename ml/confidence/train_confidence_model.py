import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

#!/usr/bin/env python3
# === Setup Logging ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# === Default Paths ===
PROJECT_ROOT = Path("/home/signal/market7").resolve()
ML_BASE = PROJECT_ROOT / "ml"

DEFAULT_INPUT = ML_BASE / "datasets/recovery_training_conf_merged.jsonl"
DEFAULT_OUTPUT = ML_BASE / "models/xgb_confidence_model.pkl"

REQUIRED_FIELDS = [
    "step",
    "entry_score",
    "current_score",
    "tp1_shift",
    "safu_score",
    "rsi",
    "macd_histogram",
    "adx",
    "macd_lift",
    "rsi_slope",
    "drawdown_pct",
    "snapshot_score_trend",
    "snapshot_rsi_trend",
    "snapshot_max_drawdown",
    "snapshot_min_score",
    "snapshot_min_rsi",
    "snapshot_time_to_max_drawdown_min",
]


def load_dataset(path: Any, target: Any) -> Any:
    df = pd.read_json(path, lines=True)
    df = df[[*REQUIRED_FIELDS, target]].dropna()
    logger.info(f"Using {len(df)} rows with non-null '{target}'")
    X = df[REQUIRED_FIELDS]
    y = df[target]
    return X, y


def main(input_path: Any, output_path: Any, target_field: Any) -> Any:
    logger.info("Loading dataset...")
    X, y = load_dataset(input_path, target_field)

    logger.info("Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info("Training XGBoost model...")
    model = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=100,
        max_depth=4,
        random_state=42,  # Optional for reproducibility
    )
    model.fit(X_train, y_train)

    logger.info("Evaluating model...")
    y_pred = model.predict(X_test)
    logger.info("R2 Score: %.4f", r2_score(y_test, y_pred))
    logger.info("MSE: %.4f", mean_squared_error(y_test, y_pred))

    logger.info(f"Saving model to: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT, help="Input JSONL file"
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Output model path"
    )
    parser.add_argument("--target", default="confidence_score_ml", help="Target field")
    args = parser.parse_args()

    main(args.input.resolve(), args.output.resolve(), args.target)
