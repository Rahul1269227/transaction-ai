# Model Performance Summary

## Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Accuracy** | **0.9866** (98.66%) | ✅ Exceptional |
| **Macro F1-Score** | **0.9867** | ✅ **PASSED** (≥0.90) |
| **Weighted F1-Score** | 0.9866 | ✅ Outstanding |
| Macro Precision | 0.9872 | ✅ |
| Macro Recall | 0.9868 | ✅ |
| Average Confidence | 0.9759 | ✅ High |

## Submission Requirement

**Requirement**: Deliver a macro F1-score of **at least 0.90**

**Result**: ✅ **PASSED** with 0.9867

**Margin**: +9.6% above target

## Highlights

- ✨ **9 categories** achieved perfect 100% F1-score
- ✨ **16 categories** achieved ≥99% F1-score
- ✨ Only **75 misclassifications** out of 5,588 test samples
- ✨ Error rate: **1.34%**

## Artifacts

- `validation_metrics.json` - Complete metrics in JSON format
- `confusion_matrix.png` - Confusion matrix heatmap (28×28)
- `f1_scores_by_category.png` - Per-category F1 scores bar chart
- `PERFORMANCE_SUMMARY.md` - This summary document

## Reproducibility

```bash
# Train model
python3 scripts/train.py

# Generate evaluation reports
python3 scripts/evaluate_f1.py --model models/transaction_classifier --test data/test.jsonl

# Generate artifacts
python3 /tmp/generate_artifacts.py
```
