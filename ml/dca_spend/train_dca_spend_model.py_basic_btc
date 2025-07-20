#!/usr/bin/env python3
import argparse
import json
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

def load_dataset(path):
    with open(path, "r") as f:
        data = []
        for line in f:
            if '"volume_sent"' not in line:
                continue
            try:
                obj = json.loads(line)
                data.append(obj)
            except json.JSONDecodeError:
                continue
    return pd.DataFrame(data)

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["btc_status"] = df["btc_status"].map({
        "SAFE": 1,
        "UNSAFE": 0,
        None: -1
    }).fillna(-1)
    return df

def main(input_path: str, output_path: str):
    print("[INFO] Loading dataset...")
    df = load_dataset(input_path)
    df = preprocess(df)

    features = [
        "entry_score", "current_score", "drawdown_pct", "safu_score", "macd_lift",
        "rsi", "rsi_slope", "adx", "tp1_shift", "recovery_odds", "confidence_score",
        "zombie_tagged", "btc_rsi", "btc_macd_histogram", "btc_adx", "btc_status"
    ]

    df = df.dropna(subset=["volume_sent"])
    df = df[df["volume_sent"] > 0]

    X = df[features]
    y = df["volume_sent"]

    print("[INFO] Training model...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        objective="reg:squarederror"
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)

    print(f"[INFO] R2 Score: {r2:.4f}")
    print(f"[INFO] MSE: {mse:.4f}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Saving model to: {output_path}")
    joblib.dump(model, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to dataset JSONL file")
    parser.add_argument("--output", required=True, help="Path to save the trained model")
    args = parser.parse_args()

    main(args.input, args.output)
