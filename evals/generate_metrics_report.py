"""
Generate Enhanced Metrics Report with Confusion Matrix and F1 Scores
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np


def calculate_f1_scores(confusion_matrix, categories):
    """Calculate precision, recall, and F1 scores for each category"""
    metrics = {}

    for category in categories:
        # True Positives: correctly predicted as this category
        tp = confusion_matrix.get(category, {}).get(category, 0)

        # False Positives: predicted as this category but was something else
        fp = sum(confusion_matrix.get(other, {}).get(category, 0)
                 for other in categories if other != category)

        # False Negatives: actually this category but predicted as something else
        fn = sum(confusion_matrix.get(category, {}).get(other, 0)
                 for other in categories if other != category)

        # True Negatives: not relevant for multi-class classification

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        metrics[category] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'support': tp + fn,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn
        }

    return metrics


def generate_confusion_matrix_text(confusion_matrix, categories):
    """Generate a text-based confusion matrix visualization"""
    # Sort categories for consistent display
    sorted_cats = sorted(categories)

    # Calculate column widths
    max_cat_len = max(len(cat) for cat in sorted_cats)
    col_width = max(max_cat_len, 6) + 2

    # Header
    lines = []
    header = " " * (max_cat_len + 2) + "PREDICTED →"
    lines.append(header)
    lines.append(" " * (max_cat_len + 2) + "".join(f"{cat[:col_width-2]:>{col_width}}" for cat in sorted_cats))
    lines.append("ACTUAL ↓" + " " * (max_cat_len - 6))
    lines.append("-" * (max_cat_len + 2 + len(sorted_cats) * col_width))

    # Rows
    for true_cat in sorted_cats:
        row = f"{true_cat:>{max_cat_len}}  "
        for pred_cat in sorted_cats:
            count = confusion_matrix.get(true_cat, {}).get(pred_cat, 0)
            row += f"{count:>{col_width}}"
        lines.append(row)

    return "\n".join(lines)


def generate_report(evaluation_json_path):
    """Generate enhanced metrics report from evaluation JSON"""

    # Load evaluation results
    with open(evaluation_json_path, 'r') as f:
        eval_data = json.load(f)

    # Extract data
    confusion = eval_data.get('confusion_matrix', {})
    overall = eval_data.get('overall', {})
    by_category = eval_data.get('by_category', {})
    by_method = eval_data.get('by_method', {})

    # Get all categories
    categories = list(confusion.keys())

    # Calculate F1 scores
    f1_metrics = calculate_f1_scores(confusion, categories)

    # Calculate macro F1
    macro_f1 = np.mean([m['f1_score'] for m in f1_metrics.values()])
    macro_precision = np.mean([m['precision'] for m in f1_metrics.values()])
    macro_recall = np.mean([m['recall'] for m in f1_metrics.values()])

    # Calculate weighted F1 (weighted by support)
    total_support = sum(m['support'] for m in f1_metrics.values())
    weighted_f1 = sum(m['f1_score'] * m['support'] for m in f1_metrics.values()) / total_support if total_support > 0 else 0

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE EVALUATION REPORT")
    report.append("Transaction AI Categorization System")
    report.append("=" * 80)
    report.append("")

    # Overall Metrics
    report.append("📊 OVERALL METRICS")
    report.append("-" * 80)
    report.append(f"Total Samples:          {overall.get('total_samples', 0)}")
    report.append(f"Overall Accuracy:       {overall.get('accuracy', 0):.4f} ({overall.get('accuracy', 0)*100:.2f}%)")
    report.append(f"Macro F1 Score:         {macro_f1:.4f} ({macro_f1*100:.2f}%)")
    report.append(f"Weighted F1 Score:      {weighted_f1:.4f} ({weighted_f1*100:.2f}%)")
    report.append(f"Macro Precision:        {macro_precision:.4f}")
    report.append(f"Macro Recall:           {macro_recall:.4f}")
    report.append(f"Average Confidence:     {overall.get('avg_confidence', 0):.4f}")
    report.append(f"Review Rate:            {overall.get('review_rate', 0):.2%}")
    report.append("")

    # Per-Category F1 Scores
    report.append("📈 PER-CATEGORY METRICS (sorted by F1 score)")
    report.append("-" * 80)
    report.append(f"{'Category':<30} {'Precision':<12} {'Recall':<12} {'F1 Score':<12} {'Support':<10}")
    report.append("-" * 80)

    # Sort by F1 score descending
    sorted_metrics = sorted(f1_metrics.items(), key=lambda x: x[1]['f1_score'], reverse=True)
    for category, metrics in sorted_metrics:
        report.append(
            f"{category:<30} "
            f"{metrics['precision']:<12.4f} "
            f"{metrics['recall']:<12.4f} "
            f"{metrics['f1_score']:<12.4f} "
            f"{metrics['support']:<10}"
        )
    report.append("")

    # Per-Method Performance
    report.append("🔧 PER-METHOD ACCURACY")
    report.append("-" * 80)
    for method, metrics in sorted(by_method.items(), key=lambda x: x[1]['accuracy'], reverse=True):
        report.append(
            f"{method:<30}: {metrics['accuracy']:.4f} "
            f"({metrics['correct']}/{metrics['total']})"
        )
    report.append("")

    # Confusion Matrix
    report.append("🎯 CONFUSION MATRIX")
    report.append("-" * 80)
    report.append(generate_confusion_matrix_text(confusion, categories))
    report.append("")

    # Top Confusions
    report.append("⚠️  TOP 10 MISCLASSIFICATIONS")
    report.append("-" * 80)
    top_confusions = eval_data.get('top_confusions', [])
    for i, conf in enumerate(top_confusions[:10], 1):
        report.append(f"{i:2}. {conf['true']:<25} → {conf['pred']:<25} ({conf['count']} errors)")
    report.append("")

    # Category-wise breakdown
    report.append("📋 DETAILED CATEGORY BREAKDOWN")
    report.append("-" * 80)
    for category in sorted(categories):
        metrics = f1_metrics[category]
        report.append(f"\n{category}:")
        report.append(f"  F1 Score: {metrics['f1_score']:.4f}")
        report.append(f"  Precision: {metrics['precision']:.4f} (TP={metrics['true_positives']}, FP={metrics['false_positives']})")
        report.append(f"  Recall: {metrics['recall']:.4f} (TP={metrics['true_positives']}, FN={metrics['false_negatives']})")
        report.append(f"  Support: {metrics['support']} samples")

    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    return "\n".join(report)


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_metrics_report.py <evaluation_report.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Generate report
    report = generate_report(input_path)

    # Print to console
    print(report)

    # Save to file
    output_path = input_path.parent / f"{input_path.stem}_detailed.txt"
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\n✅ Detailed report saved to: {output_path}")


if __name__ == '__main__':
    main()
