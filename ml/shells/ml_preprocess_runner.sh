#!/bin/bash
set -e

# === Determine default date (1 day behind UTC) ===
DEFAULT_DATE=$(date -u -d "yesterday" +%F)

# === Prompt for date ===
echo -n "📅 Enter date to preprocess ML data (YYYY-MM-DD) [default: $DEFAULT_DATE]: "
read INPUT_DATE
DATE=${INPUT_DATE:-$DEFAULT_DATE}

echo ""
echo "➡️  Running ML preprocess pipeline for $DATE"
echo "------------------------------------------------------"

BASE_PATH="/home/signal/market7/ml/preprocess"

# === Step 1: Pull golden paper trades ===
echo "[📃] python3 $BASE_PATH/pull_paper_trade_golden.py --date $DATE"
python3 "$BASE_PATH/pull_paper_trade_golden.py" --date "$DATE"
echo "------------------------------------------------------"

# === Step 2: Scrub enriched logs ===
echo "[🧼] python3 $BASE_PATH/scrubbed_enriched.py --date $DATE"
python3 "$BASE_PATH/scrubbed_enriched.py" --date "$DATE"
echo "------------------------------------------------------"

# === Step 3: Scrub fork history ===
echo "[📜] python3 $BASE_PATH/scrub_fork_history.py --date $DATE"
python3 "$BASE_PATH/scrub_fork_history.py" --date "$DATE"
echo "------------------------------------------------------"

# === Step 4: Clean paper trades ===
echo "[🧹] python3 $BASE_PATH/paper_scrubber.py --date $DATE"
python3 "$BASE_PATH/paper_scrubber.py" --date "$DATE"
echo "------------------------------------------------------"

echo "✅ ML Preprocess pipeline completed for $DATE"
