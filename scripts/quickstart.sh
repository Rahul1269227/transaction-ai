#!/bin/bash
# Quick start script for Transaction AI Categorization

set -e

echo "🚀 Transaction AI Categorization - Quick Start"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python 3 detected"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models data/datasets data/feedback evals/reports

# Generate synthetic training data
echo "🎲 Generating synthetic training data..."
python scripts/generate_dataset.py \
    --num-samples 10000 \
    --output data/datasets/synthetic_train.jsonl \
    --taxonomy data/taxonomy.yaml \
    --gazetteer data/gazetteer/merchant_aliases.csv

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. (Optional) Train ML classifier:"
echo "   python scripts/train_model.py \\"
echo "     --train data/datasets/synthetic_train.jsonl \\"
echo "     --val data/datasets/synthetic_val.jsonl \\"
echo "     --output models/classifier"
echo ""
echo "2. Start the API server:"
echo "   python apps/api/main.py"
echo ""
echo "3. Test the API:"
echo "   curl -X POST http://localhost:8000/categorize \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"text\": \"UPI-ZOMATO\", \"amount\": 249}'"
echo ""
echo "4. View API docs: http://localhost:8000/docs"
echo ""
