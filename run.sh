#!/bin/bash

echo "🚀 Launching Market Scan 6.0"

# Navigate to the script's directory
cd "$(dirname "$0")"

# Ensure we run from inside the trades folder
cd trades

# Run the pipeline
python3 runner.py

echo "✅ Market6 run completed at $(date)"
