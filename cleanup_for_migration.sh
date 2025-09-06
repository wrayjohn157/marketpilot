#!/bin/bash
# Cleanup script for VPS migration
# Removes test files, fix scripts, and other temporary files

echo "🧹 Cleaning up for VPS migration..."

# Remove test files
echo "Removing test files..."
find . -name "test_*.py" -not -path "./venv/*" -not -path "./tests/*" -delete
find . -name "*_test.py" -not -path "./venv/*" -not -path "./tests/*" -delete
find . -name "test_*.py" -path "./simulation/*" -delete

# Remove fix scripts
echo "Removing fix scripts..."
find . -name "fix_*.py" -delete
find . -name "*_fix.py" -delete
find . -name "*fix*.py" -not -path "./venv/*" -not -path "./tests/*" -delete

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.log" -delete
find . -name "*.tmp" -delete

# Remove backup files
echo "Removing backup files..."
find . -name "*.bak" -delete
find . -name "*.backup" -delete
find . -name "*_backup.*" -delete

# Remove old main files (keep only the working ones)
echo "Removing old main files..."
rm -f main_fixed.py
rm -f threecommas_metrics_fixed.py

# Remove migration scripts
echo "Removing migration scripts..."
rm -f migrate_*.py
rm -f update_*.py

# Remove install scripts
echo "Removing install scripts..."
rm -f install_dependencies.py

# Remove orchestrator files
echo "Removing orchestrator files..."
rm -f main_orchestrator.py

# Remove refactor scripts
echo "Removing refactor scripts..."
rm -f refactor_script.py

# Remove comprehensive fix scripts
echo "Removing comprehensive fix scripts..."
rm -f comprehensive_*.py
rm -f perfect_*.py
rm -f aggressive_*.py
rm -f final_*.py

echo "✅ Cleanup complete!"
echo "📁 Remaining files are ready for migration"
