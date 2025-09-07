import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

#!/usr/bin/env python3
# === CONFIG ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "ml/datasets"
MODEL_DIR = PROJECT_ROOT / "ml/models"


def load_data(path: Any) -> Any:
    with open(path, "r") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return pd.json_normalize(records, sep=".")


def prepare_features(df: Any) -> Any:
    indicator_cols = [
        "ind_ema50",
        "ind_rsi",
        "ind_adx",
        "ind_atr",
        "ind_stoch_rsi_k",
        "ind_stoch_rsi_d",
        "ind_macd",
        "ind_macd_signal",
        "ind_macd_hist",
        "ind_macd_hist_prev",
        "ind_macd_lift",
        "btc_rsi",
        "btc_adx",
        "btc_macd_histogram",
        "btc_ema_50",
        "btc_ema_200",
    ]

    if "btc_market_condition" in df.columns:
        df["btc_market_condition_num"] = df["btc_market_condition"].map(
            {"bullish": 2, "neutral": 1, "bearish": 0}
        )
        indicator_cols.append("btc_market_condition_num")

    # Detect available columns
    available_cols = [col for col in indicator_cols if col in df.columns]
    missing = [col for col in indicator_cols if col not in df.columns]
    if missing:
        print(f"⚠️ Missing columns skipped: {missing}")

    for col in available_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fallback label if not present
    if "label" not in df.columns and "pnl_pct" in df.columns:
        df["label"] = (df["pnl_pct"] > 0.5).astype(int)

    df_clean = df.dropna(subset=available_cols + ["label"])

    X = df_clean[available_cols]
    y = df_clean["label"].astype(int)
    return X, y, available_cols


def train_model(X: Any, y: Any, feature_names: Any, shap_out_path: Any) -> Any:
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_val_scaled)
    print("📊 Classification Report:")
    print(classification_report(y_val, y_pred, target_names=["Fail", "Pass"]))

    explainer = shap.Explainer(model)
    shap_values = explainer(X_val_scaled)
    plt.figure()
    shap.summary_plot(
        shap_values, X_val, feature_names=feature_names, plot_type="bar", show=False
    )
    plt.tight_layout()
    plt.savefig(shap_out_path)
    plt.close()
    print(f"📈 SHAP summary plot saved to: {shap_out_path}")

    return model, scaler


def main() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Path to master_data.jsonl")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"[ERROR] Dataset not found: {dataset_path}")
        return

    date_tag = datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    shap_out_path = MODEL_DIR / f"shap_summary_{date_tag}.png"
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
