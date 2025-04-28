#!/bin/bash
set -e

# === Prompt for date input ===
read -p "📅 Enter date [YYYY-MM-DD] (default: UTC yesterday): " INPUT_DATE

# === Default to UTC yesterday if empty ===
if [ -z "$INPUT_DATE" ]; then
  DATE=$(date -u --date="yesterday" +%Y-%m-%d)
else
  DATE="$INPUT_DATE"
fi

ML_BASE="/home/signal/market7/ml"

echo ""
echo "🚀 Running DCA Spend Pipeline for $DATE"
echo "------------------------------------------------------"

# === 1. Build Daily Dataset ===
echo "📦 Building DCA Spend dataset..."
python3 $ML_BASE/dca_spend/build_dca_spend_dataset.py --date $DATE
echo "------------------------------------------------------"

# === 2. Merge Historical Training Files ===
echo "📚 Merging historical DCA Spend datasets..."
python3 $ML_BASE/dca_spend/merge_dca_spend_training.py
echo "------------------------------------------------------"

# === 3. Train Model ===
echo "🧠 Training DCA Spend model..."
python3 $ML_BASE/dca_spend/train_dca_spend_model.py \
  --input $ML_BASE/datasets/dca_spend_merged.jsonl \
  --output $ML_BASE/models/xgb_dca_spend_model.pkl
echo "------------------------------------------------------"

echo "✅ DCA Spend ML pipeline completed for $DATE"
