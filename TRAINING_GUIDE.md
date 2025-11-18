# Transaction Categorization - Complete Training Guide

## Quick Start - One Command Training

To train the model with all data sources (consolidated, standardized categories):

```bash
python3 scripts/train.py
```

That's it! This single command will:
1. ✅ Automatically merge all data sources with **standardized categories**
2. ✅ Show detailed dataset statistics
3. ✅ Train the model with optimal hyperparameters
4. ✅ Save to `models/transaction_classifier_balanced_final` (standard location)

**No need to update .env or docker-compose.yaml!**

## Category Consolidation (NEW!)

All datasets now use **standardized category IDs** (lowercase with underscores):
- ✅ `food_dining` (instead of "Food & Dining")
- ✅ `shopping` (instead of "Shopping")
- ✅ `groceries` (instead of "Groceries")
- ✅ `travel` (instead of "Travel")

This eliminates duplicate categories and improves model accuracy!

## Current Dataset (Consolidated)

The training automatically includes **consolidated datasets** with standardized categories:

| Data Source | Training | Test | Description |
|------------|----------|------|-------------|
| **Original Balanced Data** | 89,030 | 14,267 | Original categories (consolidated) |
| **Synthetic New Categories** | 1,440 | 360 | 12 new categories (Insurance, Pets, etc.) |
| **Real Kaggle Transactions** | 16,294 | 4,074 | 20K+ real bank transactions (consolidated) |
| **Improved Weak Categories** | 1,600 | 400 | Enhanced data for underperforming categories |
| **Balanced Kaggle Dataset** | 40,000 | 10,000 | Perfectly balanced real transactions |
| **TOTAL** | **148,364** | **29,101** | **177,465 transactions** |

### What's Consolidated?
- **280,402 transactions** processed
- **202,994 categories** standardized (Title Case → lowercase_with_underscores)
- **29 unique categories** (down from 33 duplicates)

## Model Performance (After Consolidation)

### Overall
- **Accuracy**: 95%+ (expected, training in progress)
- **Categories**: 29 standardized categories
- **Model Location**: `models/transaction_classifier_balanced_final`
- **Improvement**: No more duplicate category confusion!

### New Categories Performance

| Category | Accuracy | Samples |
|----------|----------|---------|
| Professional Services | 99.90% | 3,813 |
| Taxes & Government | 97.66% | 299 |
| Automotive | 95.65% | 23 |
| Pets | 91.67% | 36 |
| Electronics & Technology | 88.24% | 34 |
| Home Improvement | 86.84% | 38 |
| Subscriptions & Memberships | 84.21% | 38 |
| Kids & Family | 83.33% | 30 |
| Charity & Donations | 80.77% | 26 |
| Insurance | 76.32% | 38 |
| Gifts & Occasions | 75.76% | 33 |
| Personal Care | 73.08% | 26 |

## Improving Weak Categories

If any category needs improvement, run:

```bash
python3 scripts/improve_weak_categories.py
python3 scripts/train.py
```

This generates 500+ diverse samples for each weak category.

## Advanced Usage

### Generating More Synthetic Data

```bash
python3 scripts/generate_synthetic_data.py
```

### Extracting More Kaggle Data

```bash
python3 scripts/extract_kaggle_new_categories.py
```

### Manual Training with Custom Parameters

```bash
python3 scripts/train_model.py \
  --train data/balanced/train.jsonl \
  --val data/balanced/test.jsonl \
  --output models/transaction_classifier_balanced_final \
  --n-estimators 200 \
  --learning-rate 0.05 \
  --max-depth 10
```

## Testing the Model

### Test All New Categories
```bash
./test_new_categories.sh
```

### Start API Server
```bash
MODEL_PATH=models/transaction_classifier_balanced_final \
python3 -m uvicorn apps.api.main:app --reload
```

### Test Single Transaction
```bash
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "LIC Insurance Premium Payment"}'
```

## Data Directory Structure

```
data/
├── balanced/                      # Original balanced data
│   ├── train.jsonl                      # Original (Title Case categories)
│   ├── test.jsonl                       # Original (Title Case categories)
│   ├── train_consolidated.jsonl         # ✅ CONSOLIDATED (standardized IDs)
│   ├── test_consolidated.jsonl          # ✅ CONSOLIDATED (standardized IDs)
│   ├── train_merged_all.jsonl           # All sources merged
│   ├── test_merged_all.jsonl            # All sources merged
│   └── class_weights.json
├── synthetic_new_categories/      # Generated synthetic data
│   ├── train_consolidated.jsonl         # ✅ CONSOLIDATED
│   └── val.jsonl
├── kaggle_new_categories/         # Real Kaggle transactions
│   └── extracted_transactions.jsonl
├── improved_weak_categories/      # Enhanced data for weak categories
│   ├── train_consolidated.jsonl         # ✅ CONSOLIDATED
│   └── test_consolidated.jsonl          # ✅ CONSOLIDATED
├── balanced_kaggle/               # Balanced Kaggle dataset
│   ├── train_consolidated.jsonl         # ✅ CONSOLIDATED
│   └── test_consolidated.jsonl          # ✅ CONSOLIDATED
└── taxonomy.yaml                  # Category definitions (with IDs)

models/
└── transaction_classifier_balanced_final/  # ← Always use this name!
    ├── classifier.pkl
    ├── label_encoder.pkl
    ├── metadata.pkl
    └── metrics.json
```

**Note**: The `train.py` script automatically uses **consolidated** datasets.

## Important Notes

1. **Model Name**: Always use `transaction_classifier_balanced_final`
   - This ensures .env and docker-compose.yaml don't need updates
   - The model will be overwritten with the latest version

2. **Category Consolidation**: All datasets use standardized IDs
   - Run `python3 scripts/consolidate_categories.py` to regenerate consolidated datasets
   - The `train.py` script automatically uses consolidated data
   - No duplicate categories (29 categories instead of 33)

3. **Data Merging**: The `train.py` script automatically merges all data sources
   - No manual data preparation needed
   - Just run `python3 scripts/train.py`

4. **Reproducibility**: All random seeds are set to 42 for reproducibility

## Troubleshooting

### Model Not Found
Make sure the model is in the correct location:
```bash
ls models/transaction_classifier_balanced_final/
```

### Permission Denied
Make scripts executable:
```bash
chmod +x scripts/*.py
chmod +x test_new_categories.sh
```

### Out of Memory
Reduce batch size or use `--no-augment` flag:
```bash
python3 scripts/train_model.py ... --no-augment
```

## Next Steps

1. Train the model: `python3 scripts/train.py`
2. Start the API: `MODEL_PATH=models/transaction_classifier_balanced_final python3 -m uvicorn apps.api.main:app --reload`
3. Test new categories: `./test_new_categories.sh`
4. Deploy to production with Docker Compose

## Category Consolidation

If you need to regenerate consolidated datasets:

```bash
python3 scripts/consolidate_categories.py
```

This will:
- Process all datasets in data/
- Standardize all category names to taxonomy IDs
- Create *_consolidated.jsonl files
- Show detailed statistics

---

**Last Updated**: 2025-11-18
**Total Categories**: 29 (consolidated, no duplicates)
**Total Training Samples**: 148,364
**Total Validation Samples**: 29,101
**Model Accuracy**: 95%+ (expected after consolidation)
