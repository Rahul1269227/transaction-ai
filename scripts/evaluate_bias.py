"""
Bias and Fairness Evaluation Script

This script evaluates the transaction categorization model for potential biases
across different transaction attributes (e.g., amount ranges).
"""

import argparse
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import classification_report, f1_score, confusion_matrix
from typing import Dict, List, Any
import sys
import os

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.model import EnsembleRouter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data(path: str) -> List[Dict[str, Any]]:
    data = []
    with open(path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def analyze_bias(
    model_path: str,
    test_data_path: str,
    taxonomy_path: str,
    output_path: str = "reports/bias_report.md"
):
    logger.info("Loading test data...")
    test_data = load_data(test_data_path)
    df = pd.DataFrame(test_data)
    
    # Ensure amount is float
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    else:
        df['amount'] = 0.0

    logger.info("Initializing Ensemble Router...")
    # Initialize without LLM for speed in this check, or with if needed
    # Assuming we want to test the full ensemble's bias
    router = EnsembleRouter(
        ml_model_path=model_path,
        taxonomy_path=taxonomy_path,
        # Disable LLM for faster batch evaluation unless strictly necessary
        llm_weight=0.0, 
        enable_parallel=False # simpler debugging
    )
    
    logger.info(f"Running predictions on {len(df)} transactions...")
    
    predictions = []
    true_labels = []
    
    # Batch prediction would be faster, but let's do simple loop for control
    for _, row in df.iterrows():
        text = row.get('text', row.get('description', ''))
        amount = row.get('amount')
        true_cat = row.get('category')
        
        result = router.categorize(text=text, amount=amount)
        
        predictions.append(result.category)
        true_labels.append(true_cat)
        
    df['predicted_category'] = predictions
    df['correct'] = df['predicted_category'] == df['category']
    
    # --- Bias Analysis ---
    
    report_lines = []
    report_lines.append("# Transaction AI - Fairness & Bias Report")
    report_lines.append(f"Date: {pd.Timestamp.now()}\n")
    
    overall_acc = df['correct'].mean()
    report_lines.append(f"**Overall Accuracy**: {overall_acc:.2%}\n")
    
    # 1. Bias by Amount Range
    report_lines.append("## Performance by Transaction Amount")
    
    # Define bins: Small (<100), Medium (100-1000), Large (>1000)
    # Adjust currency/bins as appropriate
    bins = [-float('inf'), 100, 1000, float('inf')]
    labels = ['Small (<100)', 'Medium (100-1000)', 'Large (>1000)']
    df['amount_range'] = pd.cut(df['amount'], bins=bins, labels=labels)
    
    amount_perf = df.groupby('amount_range')['correct'].agg(['count', 'mean']).reset_index()
    amount_perf.columns = ['Amount Range', 'Count', 'Accuracy']
    
    report_lines.append("| Amount Range | Count | Accuracy |")
    report_lines.append("|---|---|---|")
    for _, row in amount_perf.iterrows():
        report_lines.append(f"| {row['Amount Range']} | {row['Count']} | {row['Accuracy']:.2%} |")
    
    # Check for significant disparity
    accuracies = amount_perf['Accuracy'].values
    if len(accuracies) > 0:
        max_diff = np.max(accuracies) - np.min(accuracies)
        report_lines.append(f"\n**Max Disparity**: {max_diff:.2%}")
        if max_diff > 0.10:
            report_lines.append("⚠️ **Warning**: Significant performance disparity across amount ranges detected.")
        else:
            report_lines.append("✅ **Pass**: Performance is relatively consistent across amount ranges.")

    # 2. Bias by Category (Representation)
    report_lines.append("\n## Performance by Category (Minority Classes)")
    cat_perf = df.groupby('category')['correct'].agg(['count', 'mean']).reset_index()
    cat_perf.columns = ['Category', 'Count', 'Accuracy']
    cat_perf = cat_perf.sort_values('Count')
    
    report_lines.append("| Category | Count | Accuracy |")
    report_lines.append("|---|---|---|")
    for _, row in cat_perf.iterrows():
        report_lines.append(f"| {row['Category']} | {row['Count']} | {row['Accuracy']:.2%} |")
        
    # Check if minority classes (< 10 samples) have significantly lower accuracy
    minority_classes = cat_perf[cat_perf['Count'] < 20]
    if not minority_classes.empty:
        avg_minority_acc = minority_classes['Accuracy'].mean()
        report_lines.append(f"\n**Average Accuracy on Minority Classes (<20 samples)**: {avg_minority_acc:.2%}")
        if avg_minority_acc < overall_acc - 0.15:
             report_lines.append("⚠️ **Warning**: Minority classes are significantly underperforming.")
    
    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
        
    logger.info(f"Bias report saved to {output_path}")
    print(f"Bias report saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate model bias/fairness")
    parser.add_argument("--model", required=True, help="Path to trained model directory")
    parser.add_argument("--test", required=True, help="Path to test JSONL")
    parser.add_argument("--taxonomy", default="data/taxonomy.yaml", help="Path to taxonomy")
    parser.add_argument("--output", default="reports/bias_report.md", help="Output report path")
    
    args = parser.parse_args()
    
    analyze_bias(args.model, args.test, args.taxonomy, args.output)
