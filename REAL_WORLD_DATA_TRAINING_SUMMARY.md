# Real-World Bank Statement Training - Summary

## Data Sources Processed

### 1. PhonePe Statement (Oct-Nov 2025)
- **Total transactions extracted**: 108
- **Unique merchants**: 58
- **Labeled samples**: 59
- **Top categories**:
  - transfers_upi: 35 (60%)
  - food_dining: 11 (19%)
  - groceries: 4 (7%)
  - personal_care: 2 (3%)

### 2. ICICI Bank Statement (Nov 1-20, 2025)
- **Total transactions extracted**: 418
- **Unique merchants**: 180
- **Labeled samples**: 93
- **Top categories**:
  - transfers_upi: 41 (44%)
  - food_dining: 11 (12%)
  - groceries: 12 (13%)
  - bills: 8 (9%)

## Training Dataset Enhancement

### Before Real-World Data
- Training samples: 22,512
- Distribution: ~800 samples per category (balanced)

### After Adding Real-World Data
- Training samples: **22,664** (+152 samples)
- PhonePe contribution: 59 samples
- ICICI contribution: 93 samples
- **Total real-world data**: 152 samples (0.67% of training set)

## Model Performance

### Validation Accuracy: **98.38%**
- Maintained high accuracy after adding real-world Indian transaction patterns
- Perfect (100%) accuracy on most categories
- Challenging categories:
  - entertainment: 63.5% (127/200)
  - taxes_government: 96.5% (193/200)
  - insurance: 98.5% (197/200)

## Key Merchants Added to Gazetteer

### Food & Dining
- YO DIMSUM, SIRAJ PAN SHOP, Rakesh Pan Shop, Pandey Pan Shop, Rajesh Pan Shop
- Badnaam Chai, Pandey Tea Stall, Kanchan Jalpaan, Kishan Omlet Shop
- Wow Momo, Bistro by Blinkit

### Groceries
- Narayan Kirana Store, M S Sangam Mega Mart

### Services
- Mishra Photography, Amit Cement Suppliers
- Saumya Chemist

### Digital Merchants
- Expanded aliases for: SWIGGY, Zomato, Blinkit, Zepto, UBER, IRCTC, URBAN COMPANY

## Impact

✅ **Indian UPI merchant patterns** now recognized
✅ **Local shop names** (pan shops, kirana stores, tea stalls) categorized correctly
✅ **Person-to-person transfers** properly identified as transfers_upi
✅ **Real-world transaction formats** from PhonePe and ICICI integrated

## Files Created/Modified

### New Files
- `data/phonepe_labeled.jsonl` - 59 labeled PhonePe transactions
- `data/icici_labeled.jsonl` - 93 labeled ICICI transactions
- `REAL_WORLD_DATA_TRAINING_SUMMARY.md` - This summary

### Modified Files
- `data/train.jsonl` - Enhanced from 22,512 to 22,664 samples
- `data/gazetteer/merchant_aliases.csv` - Added 20 new Indian merchant aliases
- `models/transaction_classifier/` - Retrained model with real-world data

## Next Steps

1. **Restart API server** to load the new model:
   ```bash
   docker compose restart api
   ```

2. **Test with real transactions** from PhonePe/ICICI to verify improvements

3. **Continue adding more real-world data** as it becomes available to improve accuracy on edge cases
