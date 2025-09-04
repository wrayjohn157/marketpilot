from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging

import pandas as pd

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
import argparse
import joblib

from
 xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def train_model(input_path: Any, output_path: Any) -> Any:
    logging.info(f"📂 Loading dataset: {input_path}")
    with open(input_path, 'r') as f:
        data = [json.loads(line) for line in f if line.strip()]

    df = pd.DataFrame(data)

    # Drop non-numeric or irrelevant fields
    drop_cols = ["symbol", "deal_id", "status", "exit_time", "pnl_pct"]
    df = df.drop(columns=[col for col in drop_cols if col in df.columns])

    # Split features and label
    X = df.drop(columns=["recovery_label"])
    y = df["recovery_label"]

    logging.info(f"✅ Dataset loaded: {len(df)} samples, {X.shape[1]} features.")

    # Label distribution
    pos_count = sum(y == 1)
    neg_count = sum(y == 0)
    logging.info(f"📊 Label distribution → Recovered: {pos_count}, Not recovered: {neg_count}")

    # Rebalance class weights
    scale_pos_weight = (neg_count / pos_count) if pos_count > 0 else 1.0
    logging.info(f"⚖️  Using scale_pos_weight: {scale_pos_weight:.2f}")

    # Split for validation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)

    # Train XGBoost
    logging.info("🧠 Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        objective="binary:logistic",
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric="logloss"
    )
    model.fit(X_train, y_train)

    # Evaluate
    logging.info("🧪 Evaluating model...")
    y_pred = model.predict(X_test)
    print("\n📊 Classification Report:\n", classification_report(y_test, y_pred, digits=3))
    print("📉 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    # Save model
    joblib.dump(model, output_path)
    logging.info(f"✅ Model saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to merged recovery dataset (JSONL)")
    parser.add_argument("--output", default="/home/signal/market7/ml/models/xgb_recovery_model.pkl", help="Output path")
    args = parser.parse_args()

    train_model(args.input, args.output)
