#!/usr/bin/env python3
import os
import json
import argparse
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
import shap
import matplotlib.pyplot as plt

# === CONFIG ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/market7
DATA_DIR = PROJECT_ROOT / "ml/datasets"
MODEL_DIR = PROJECT_ROOT / "ml/models"

def load_data(path):
    with open(path, "r") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return pd.json_normalize(records, sep='.')

def prepare_features(df):
    indicator_cols = [
        "fork_score.indicators.EMA50",
        "fork_score.indicators.EMA200",
        "fork_score.indicators.RSI14",
        "fork_score.indicators.ADX14",
        "fork_score.indicators.QQE",
        "fork_score.indicators.PSAR",
        "fork_score.indicators.ATR",
        "fork_score.indicators.StochRSI_K",
        "fork_score.indicators.StochRSI_D",
        "fork_score.indicators.MACD",
        "fork_score.indicators.MACD_signal",
        "fork_score.indicators.MACD_diff",
        "fork_score.indicators.MACD_Histogram",
        "fork_score.indicators.MACD_Histogram_Prev",
        "fork_score.indicators.MACD_lift",
        "btc_entry.rsi",
        "btc_entry.adx",
        "btc_entry.macd_histogram",
        "btc_entry.ema_50",
        "btc_entry.ema_200"
    ]

    if "btc_entry.market_condition" in df.columns:
        df["btc_entry.market_condition_num"] = df["btc_entry.market_condition"].map({
            "bullish": 2, "neutral": 1, "bearish": 0
        })
        indicator_cols.append("btc_entry.market_condition_num")

    for col in indicator_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df_clean = df.dropna(subset=indicator_cols + ["label"])

    X = df_clean[indicator_cols]
    y = df_clean["label"].astype(int)
    return X, y, indicator_cols

def train_model(X, y, feature_names, shap_out_path):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_val_scaled)
    print("📊 Classification Report:")
    print(classification_report(y_val, y_pred, target_names=["Fail", "Pass"]))

    explainer = shap.Explainer(model)
    shap_values = explainer(X_val_scaled)
    plt.figure()
    shap.summary_plot(shap_values, X_val, feature_names=feature_names, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(shap_out_path)
    plt.close()
    print(f"📈 SHAP summary plot saved to: {shap_out_path}")

    return model, scaler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to ml_training_set.jsonl")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"[ERROR] Dataset not found: {dataset_path}")
        return

    date_folder = dataset_path.parent.name
    shap_out_path = MODEL_DIR / f"shap_summary_{date_folder}.png"
    model_out_path = MODEL_DIR / "xgb_model.pkl"
    scaler_out_path = MODEL_DIR / "scaler.pkl"
    features_out_path = MODEL_DIR / "features_used.json"

    print(f"📂 Loading dataset: {dataset_path}")
    df = load_data(dataset_path)
    X, y, features = prepare_features(df)
    print(f"✅ Prepared {len(X)} samples, {len(features)} features.")

    model, scaler = train_model(X, y, features, shap_out_path)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out_path)
    joblib.dump(scaler, scaler_out_path)
    with open(features_out_path, "w") as f:
        json.dump(features, f, indent=2)

    print(f"💾 Model saved to: {model_out_path}")
    print(f"💾 Scaler saved to: {scaler_out_path}")
    print(f"🧠 Features saved to: {features_out_path}")

if __name__ == "__main__":
    main()
