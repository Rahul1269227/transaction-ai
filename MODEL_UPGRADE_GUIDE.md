# Model Upgrade Guide: Using the Balanced Model

## Overview

The transaction categorization system now uses a **balanced model** by default, which provides significantly better performance across all transaction categories.

## What Changed?

### Old Model (`models/classifier`)
- Trained on imbalanced data (9,192:1 ratio)
- Heavily biased toward ATM/Cash and Investments
- Poor performance on minority classes (Food, Shopping, Entertainment, etc.)

### New Model (`models/transaction_classifier_balanced`)
- Trained on balanced data (2.8:1 ratio)
- Excellent performance across all 17 categories
- 99.78% validation accuracy
- No category bias

## Configuration Update

The `.env` file has been updated to use the balanced model:

```bash
# Old (don't use)
MODEL_PATH=models/classifier

# New (now default)
MODEL_PATH=models/transaction_classifier_balanced
```

## How to Use

### Option 1: Use Default Configuration (Recommended)

The `.env` file is already configured to use the balanced model. Just start the API:

```bash
# Start the API
python apps/api/main.py

# Or with Docker
docker-compose up
```

### Option 2: Explicitly Specify Model Path

If you're using the routers directly in code:

```python
from core.model import HybridRouter

# Use balanced model
router = HybridRouter(
    taxonomy_path="data/taxonomy.yaml",
    model_path="models/transaction_classifier_balanced",
    auto_accept_threshold=0.85,
    review_threshold=0.60
)
```

### Option 3: Environment Variable Override

```bash
# Set environment variable
export MODEL_PATH=models/transaction_classifier_balanced

# Start your application
python apps/api/main.py
```

## Performance Comparison

### Old Model Results
```
UPI-SWIGGY-RESTAURANT → ATM/Cash (65.6%) ✗ WRONG
NETFLIX SUBSCRIPTION  → Income/Salary (81.2%) ✗ WRONG
IRCTC TICKET BOOKING  → ATM/Cash (63.8%) ✗ WRONG
ZERODHA TRADING       → ATM/Cash (78.2%) ✗ WRONG
```

### Balanced Model Results
```
UPI-SWIGGY-RESTAURANT → Food & Dining (100%) ✓ CORRECT
NETFLIX SUBSCRIPTION  → Entertainment (100%) ✓ CORRECT
IRCTC TICKET BOOKING  → Travel (100%) ✓ CORRECT
ZERODHA TRADING       → Investments (94.4%) ✓ CORRECT
UBER TRIP PAYMENT     → Transport (100%) ✓ CORRECT
SCHOOL FEE PAYMENT    → Education (100%) ✓ CORRECT
HOUSE RENT PAYMENT    → Rent (100%) ✓ CORRECT
```

## Category Coverage

The balanced model now supports all 17 categories:

1. ATM/Cash
2. Bills
3. Education
4. Entertainment
5. Fees & Charges
6. **Food & Dining** (new, improved)
7. **Fuel** (new)
8. **Groceries** (new)
9. **Health** (new)
10. Income/Salary
11. Investments
12. **Rent** (improved)
13. **Shopping** (improved)
14. Transfers/UPI
15. **Transport** (improved)
16. Travel
17. Utilities

## Migration Guide

### For Production Deployments

1. **Backup Current Model** (optional):
   ```bash
   cp -r models/classifier models/classifier_backup
   ```

2. **Update Environment**:
   - Ensure `.env` has `MODEL_PATH=models/transaction_classifier_balanced`
   - Or set `export MODEL_PATH=models/transaction_classifier_balanced`

3. **Restart Application**:
   ```bash
   # Stop current instance
   docker-compose down

   # Start with new model
   docker-compose up -d
   ```

4. **Verify**:
   ```bash
   # Health check
   curl http://localhost:8000/health

   # Test categorization
   curl -X POST http://localhost:8000/categorize \
     -H "Content-Type: application/json" \
     -d '{"text": "UPI-SWIGGY-RESTAURANT", "amount": 250}'
   ```

### For Development

1. **Pull Latest Changes**:
   ```bash
   git pull origin main
   ```

2. **Copy Environment**:
   ```bash
   cp .env.example .env
   # The .env.example now uses the balanced model by default
   ```

3. **Start Development Server**:
   ```bash
   python apps/api/main.py
   ```

## Rollback (If Needed)

If you need to rollback to the old model:

```bash
# In .env file
MODEL_PATH=models/classifier

# Or environment variable
export MODEL_PATH=models/classifier
```

**Note**: Rollback is **not recommended** as the old model has significant bias issues.

## Training New Models

If you want to retrain or update the balanced model:

```bash
python3 scripts/train_model.py \
  --train data/balanced/train.jsonl \
  --val data/balanced/val.jsonl \
  --output models/transaction_classifier_balanced \
  --class-weights data/balanced/class_weights.json \
  --n-estimators 300 \
  --learning-rate 0.05 \
  --max-depth 12 \
  --no-balance
```

## Questions?

See the following documentation:
- **IMBALANCE_SOLUTION.md** - Detailed explanation of the class imbalance problem and solution
- **TRAINING_SUMMARY.md** - Training process and metrics
- **README.md** - General system documentation

## Summary

**Action Required**: None if using the latest code. The balanced model is now the default.

**Benefit**: Improved accuracy across all transaction categories with no bias.

**When**: Effective immediately for all new deployments.
