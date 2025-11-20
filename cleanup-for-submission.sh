#!/bin/bash
# Transaction AI - Pre-Submission Cleanup Script
# Removes unnecessary files before submitting GitHub link

echo "🧹 Transaction AI - Cleanup for Submission"
echo "=========================================="
echo ""

# Get current directory size
BEFORE_SIZE=$(du -sh . 2>/dev/null | awk '{print $1}')
echo "📊 Current project size: $BEFORE_SIZE"
echo ""

# Confirm before proceeding
read -p "⚠️  This will delete node_modules, logs, PDFs, and dev notes. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo ""
echo "🗑️  Deleting unnecessary files..."
echo ""

# 1. Delete node_modules (403MB - can be reinstalled)
if [ -d "ui/node_modules" ]; then
    echo "  ✓ Deleting ui/node_modules/ (403MB)"
    rm -rf ui/node_modules/
fi

# 2. Delete personal/sensitive PDFs
echo "  ✓ Deleting personal PDFs"
rm -f PhonePe_Statement*.pdf 2>/dev/null
rm -f OpTransactionHistory*.pdf 2>/dev/null

# 3. Delete development logs
echo "  ✓ Deleting log files"
rm -f *.log 2>/dev/null
rm -f logs/*.log 2>/dev/null

# 4. Delete temporary test files
echo "  ✓ Deleting temporary test files"
rm -f test_*.sh 2>/dev/null
rm -f /tmp/phonepe_*.json 2>/dev/null
rm -f /tmp/test_*.log 2>/dev/null

# 5. Delete development notes (optional - comment out if you want to keep)
echo "  ✓ Deleting development notes"
rm -f ACCURACY_FIXES_SUMMARY.md 2>/dev/null
rm -f DATABASE_FIX_NOTE.md 2>/dev/null
rm -f PATTERN_BASED_IMPROVEMENTS.md 2>/dev/null
rm -f REAL_WORLD_DATA_TRAINING_SUMMARY.md 2>/dev/null
rm -f REAL_WORLD_TEST_RESULTS.md 2>/dev/null
rm -f ROOT_CAUSE_ANALYSIS.md 2>/dev/null
rm -f TAXONOMY_FIXES_SUMMARY.md 2>/dev/null
rm -f TEST_RESULTS_ANALYSIS.md 2>/dev/null
rm -f FINAL_RESULTS_FIXED.log 2>/dev/null
rm -f test_results_*.log 2>/dev/null
rm -f CONFIGURATION.md 2>/dev/null
rm -f TRAINING_GUIDE.md 2>/dev/null

# 6. Clean Python cache
echo "  ✓ Cleaning Python cache"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# 7. Clean macOS files
echo "  ✓ Cleaning macOS files"
find . -name ".DS_Store" -delete 2>/dev/null

echo ""
echo "✅ Cleanup complete!"
echo ""

# Show new size
AFTER_SIZE=$(du -sh . 2>/dev/null | awk '{print $1}')
echo "📊 Project size after cleanup: $AFTER_SIZE (was $BEFORE_SIZE)"
echo ""

# Show what's left
echo "📁 Remaining structure:"
echo "  ✅ apps/ - Core API code"
echo "  ✅ core/ - ML models and logic"
echo "  ✅ scripts/ - Training/evaluation scripts"
echo "  ✅ data/ - Taxonomy, gazetteer, training data"
echo "  ✅ models/ - Trained ML models"
echo "  ✅ docs/ - Comprehensive documentation (15 files)"
echo "  ✅ infra/ - Docker/Kubernetes configs"
echo "  ✅ ui/ - Frontend (without node_modules)"
echo "  ✅ README.md - Main documentation"
echo "  ✅ PROJECT_TECHNICAL_DOCUMENTATION.md - Submission doc"
echo ""

echo "🎯 Next steps:"
echo "  1. Review changes: git status"
echo "  2. Test that everything still works"
echo "  3. Commit: git add . && git commit -m 'Clean up for submission'"
echo "  4. Push: git push origin main"
echo "  5. Submit GitHub link"
echo ""

echo "💡 To restore node_modules: cd ui && npm install"
echo ""
