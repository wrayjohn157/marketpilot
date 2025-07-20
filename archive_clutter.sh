#!/bin/bash

ARCHIVE_DIR="archive"
mkdir -p "$ARCHIVE_DIR"

# Tier 1: Stale or Duplicated
mv dca/smart_dca_signal.py_update_in_progresss "$ARCHIVE_DIR/" 2>/dev/null
mv dashboard_backend/config_routes/gpt_code_editor_api.py_annoyiing "$ARCHIVE_DIR/" 2>/dev/null
mv dashboard_backend/config_routes/gpt_code_editor_api.py_dumbasfuck "$ARCHIVE_DIR/" 2>/dev/null
mv dashboard_backend/config_routes/gpt_code_editor_api.py_doer_noBrain "$ARCHIVE_DIR/" 2>/dev/null
mv dashboard_frontend/src/pages/GptCodeEditor.jsx_no_brain "$ARCHIVE_DIR/" 2>/dev/null
mv dashboard_frontend/src/pages/GptCodeEditor.jsx_no_tree_access "$ARCHIVE_DIR/" 2>/dev/null
mv ml/preprocess/build_unified_ml_dataset.py_old_way "$ARCHIVE_DIR/" 2>/dev/null
mv ml/recovery/train_recovery_model.py_low_odds "$ARCHIVE_DIR/" 2>/dev/null
mv ml/preprocess/train_model.py_M6 "$ARCHIVE_DIR/" 2>/dev/null

# Tier 2: Dev/Test Utilities
mv dca/test_adjusted_spend.py "$ARCHIVE_DIR/" 2>/dev/null
mv dca/test_predict_spend_volume.py "$ARCHIVE_DIR/" 2>/dev/null
mv dca/debug_dca_diagnostic.py "$ARCHIVE_DIR/" 2>/dev/null
mv ml/recovery/train_recovery_model.py_parse_error "$ARCHIVE_DIR/" 2>/dev/null
mv ml/recovery/build_recovery_training_dataset.py_not_sysd_ready "$ARCHIVE_DIR/" 2>/dev/null
mv ml/preprocess/clean_and_flatten_for_ml.py_signle_day "$ARCHIVE_DIR/" 2>/dev/null

echo "✅ Selected files moved to ./$ARCHIVE_DIR/"
