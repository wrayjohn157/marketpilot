import json
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# === Load labeled SAFU snapshot data ===
INPUT_PATH = "/home/signal/market7/ml/datasets/safu_analysis/labeled_safu_dca.jsonl"
df = pd.read_json(INPUT_PATH, lines=True)

# === Encode labels ===
df["label"] = df["safu_label"].map({"recovered": 1, "not_recovered": 0})

# === Feature columns ===
feature_cols = [
    "entry_score",
    "current_score",
    "safu_score",
    "recovery_odds",
    "confidence_score",
    "tp1_shift",
    "be_improvement",
    "rsi",
    "macd_histogram",
    "adx",
    "macd_lift",
    "rsi_slope",
    "drawdown_pct",
]

X = df[feature_cols]
y = df["label"]

# === Train/test split ===
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# === Train XGBoost classifier ===
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric="logloss",
)
model.fit(X_train, y_train)

# === Evaluate ===
print("📊 Classification Report:")
print(classification_report(y_test, model.predict(X_test)))

# === Save model ===
joblib.dump(model, "safu_exit_model.pkl")
print("✅ Saved model to safu_exit_model.pkl")

# === SHAP Feature Importance Plot ===
explainer = shap.Explainer(model)
shap_values = explainer(X_test)

print("📈 Generating SHAP summary plot...")
shap.summary_plot(shap_values, X_test, show=False)
plt.tight_layout()
plt.savefig("safu_shap_summary.png")
print("✅ Saved SHAP plot to safu_shap_summary.png")
