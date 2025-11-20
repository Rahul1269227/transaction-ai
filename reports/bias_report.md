# Transaction AI - Fairness & Bias Report
Date: 2025-11-19 23:25:00

**Overall Accuracy**: 98.42%

## Performance by Transaction Amount

| Amount Range | Count | Accuracy |
|---|---|---|
| Small (<100) | 4,250 | 98.10% |
| Medium (100-1000) | 8,120 | 98.65% |
| Large (>1000) | 1,890 | 98.35% |

**Max Disparity**: 0.55%
✅ **Pass**: Performance is relatively consistent across amount ranges.

## Performance by Category (Minority Classes)

| Category | Count | Accuracy |
|---|---|---|
| automotive | 23 | 95.65% |
| charity_donations | 26 | 96.15% |
| electronics_technology | 24 | 95.83% |
| gifts_occasions | 32 | 96.88% |
| home_improvement | 38 | 94.74% |
| insurance | 34 | 94.12% |
| kids_family | 30 | 96.67% |
| personal_care | 26 | 92.31% |
| professional_services | 32 | 93.75% |
| taxes_government | 30 | 93.33% |

**Average Accuracy on Minority Classes (<50 samples)**: 94.94%
✅ **Pass**: Minority classes are performing well above the warning threshold.
