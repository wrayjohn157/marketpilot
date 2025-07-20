#!/bin/bash
set -e

# === Determine default date (1 day behind UTC) ===
DEFAULT_DATE=$(date -u -d "yesterday" +%F)

# === Prompt only if run interactively ===
if [ -t 0 ]; then
  echo -n "📅 Enter date to build confidence set (YYYY-MM-DD) [default: $DEFAULT_DATE]: "
  read INPUT_DATE
  DATE=${INPUT_DATE:-$DEFAULT_DATE}
else
  DATE=$DEFAULT_DATE
fi

# === Base Paths ===
PROJECT_ROOT="/home/signal/market7"
CONFIDENCE_DIR="$PROJECT_ROOT/ml/confidence"
DATASETS_DIR="$PROJECT_ROOT/ml/datasets"
MODELS_DIR="$PROJECT_ROOT/ml/models"

echo ""
echo "➡️  Running confidence ML pipeline for $DATE"
echo "------------------------------------------------------"

# === Step 1: Build confidence dataset for selected date ===
echo "[📃] python3 build_confidence_dataset_full.py $DATE"
python3 "$CONFIDENCE_DIR/build_confidence_dataset_full.py" "$DATE"
echo "------------------------------------------------------"

# === Step 2: Merge all confidence training data ===
echo "[📦] python3 merge_confidence_training.py"
python3 "$CONFIDENCE_DIR/merge_confidence_training.py"
echo "------------------------------------------------------"

# === Step 3: Train the confidence model ===
echo "[🤖] python3 train_confidence_model.py"
python3 "$CONFIDENCE_DIR/train_confidence_model.py" \
  --input "$DATASETS_DIR/recovery_training_conf_merged.jsonl" \
  --output "$MODELS_DIR/xgb_confidence_model.pkl" \
  --target confidence_score_ml
echo "------------------------------------------------------"

echo "✅ Confidence ML pipeline completed for $DATE"
