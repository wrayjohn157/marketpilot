#!/bin/bash
set -e

# === Setup ===
SCRIPT_DIR="/home/signal/market7/ml/recovery"
DATASET_DIR="/home/signal/market7/ml/datasets"
MODEL_DIR="/home/signal/market7/ml/models"

# === Prompt for target date (default: today UTC) ===
read -p "📅 Enter date to build recovery set (YYYY-MM-DD) [default: today]: " DATE_INPUT
DATE=${DATE_INPUT:-$(date +%F)}

echo ""
echo "➡️  Running Recovery ML Pipeline for $DATE"
echo "------------------------------------------------------"

# === Step 1: Build daily recovery dataset ===
echo "[📃] Building daily recovery dataset..."
python3 "$SCRIPT_DIR/build_recovery_set.py" --date "$DATE"
echo "------------------------------------------------------"

# === Step 2: Merge all historical recovery files ===
echo "[📦] Merging recovery training data..."
python3 "$SCRIPT_DIR/merge_recovery_training.py" \
  --input-dir "$DATASET_DIR/recovery_training" \
  --output "$DATASET_DIR/recovery_training_merged.jsonl"
echo "------------------------------------------------------"

# === Step 3: Train the recovery model ===
echo "[🤖] Training recovery model..."
python3 "$SCRIPT_DIR/train_recovery_model.py" \
  --input "$DATASET_DIR/recovery_training_merged.jsonl" \
  --output "$MODEL_DIR/xgb_recovery_model.pkl"
echo "------------------------------------------------------"

echo "✅ Recovery ML pipeline completed for $DATE"
