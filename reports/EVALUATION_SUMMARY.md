# Transaction Classifier - Evaluation Report

## Executive Summary

- **Model**: models/transaction_classifier
- **Test Dataset**: data/test.jsonl (5,588 samples)
- **Categories**: 28
- **Evaluation Date**: 2025-11-20
- **Requirement**: Macro F1-score ≥ 0.90
- **Status**: **✅ PASSED**

## Overall Performance

| Metric | Value | Status |
|--------|-------|--------|
| **Accuracy** | **0.9866** (98.66%) | ✅ |
| **Macro F1-Score** | **0.9867** | ✅ PASSED |
| Macro Precision | 0.9872 | |
| Macro Recall | 0.9868 | |
| Weighted F1-Score | 0.9866 | |
| Weighted Precision | 0.9871 | |
| Weighted Recall | 0.9866 | |
| Average Confidence | 0.9759 | |

## Per-Class Performance

| Category | Precision | Recall | F1-Score | Support |
|----------|-----------|--------|----------|----------|
| atm_cash | 0.9526 | 1.0000 | 0.9757 | 201 |
| automotive | 0.9674 | 1.0000 | 0.9834 | 178 |
| bills | 1.0000 | 1.0000 | 1.0000 | 181 |
| charity_donations | 1.0000 | 1.0000 | 1.0000 | 197 |
| education | 0.9591 | 1.0000 | 0.9791 | 211 |
| electronics_technology | 1.0000 | 1.0000 | 1.0000 | 218 |
| entertainment | 1.0000 | 1.0000 | 1.0000 | 182 |
| fees_charges | 0.9792 | 0.9038 | 0.9400 | 208 |
| food_dining | 1.0000 | 0.9851 | 0.9925 | 202 |
| fuel | 1.0000 | 1.0000 | 1.0000 | 205 |
| gifts_occasions | 0.9949 | 1.0000 | 0.9974 | 195 |
| groceries | 1.0000 | 0.9749 | 0.9873 | 199 |
| health | 0.9954 | 1.0000 | 0.9977 | 218 |
| home_improvement | 0.9567 | 1.0000 | 0.9779 | 199 |
| income_salary | 1.0000 | 0.9503 | 0.9745 | 181 |
| insurance | 1.0000 | 1.0000 | 1.0000 | 184 |
| investments | 1.0000 | 0.9865 | 0.9932 | 222 |
| kids_family | 1.0000 | 0.9948 | 0.9974 | 192 |
| personal_care | 0.9849 | 1.0000 | 0.9924 | 196 |
| pets | 1.0000 | 1.0000 | 1.0000 | 205 |
| professional_services | 1.0000 | 0.9519 | 0.9754 | 208 |
| rent | 0.9949 | 1.0000 | 0.9974 | 195 |
| shopping | 0.9901 | 0.9437 | 0.9663 | 213 |
| subscriptions_memberships | 1.0000 | 1.0000 | 1.0000 | 210 |
| taxes_government | 0.8969 | 0.9804 | 0.9368 | 204 |
| transfers_upi | 0.9706 | 1.0000 | 0.9851 | 198 |
| transport | 1.0000 | 1.0000 | 1.0000 | 192 |
| travel | 1.0000 | 0.9588 | 0.9789 | 194 |

## Error Analysis

### Categories with Misclassifications

| Category | Incorrect | Total | Accuracy |
|----------|-----------|-------|----------|
| fees_charges | 20 | 208 | 90.4% |
| shopping | 12 | 213 | 94.4% |
| income_salary | 9 | 181 | 95.0% |
| professional_services | 10 | 208 | 95.2% |
| travel | 8 | 194 | 95.9% |
| groceries | 5 | 199 | 97.5% |
| taxes_government | 4 | 204 | 98.0% |
| food_dining | 3 | 202 | 98.5% |
| investments | 3 | 222 | 98.6% |
| kids_family | 1 | 192 | 99.5% |

## Files Generated

- `evaluation_report.json` - Complete metrics in JSON format
- `confusion_matrix.csv` - Full confusion matrix
- `per_class_f1_scores.csv` - Per-category precision, recall, F1
- `predictions.jsonl` - All predictions with confidence scores
- `EVALUATION_SUMMARY.md` - This comprehensive report

## Reproducibility

```bash
# Train model
python3 scripts/train.py

# Generate evaluation reports
python3 scripts/evaluate_f1.py --model models/transaction_classifier --test data/test.jsonl
```
