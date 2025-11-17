#!/usr/bin/env python3
"""
Evaluate trained model on test set with comprehensive metrics.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import joblib
import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support
)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.model.classifier import EmbeddingClassifier


def load_test_data(test_path: str) -> Tuple[List[str], List[str]]:
    """Load test data from JSONL file."""
    texts = []
    labels = []

    with open(test_path, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                texts.append(data['text'])
                # Support both 'label' and 'category' keys
                labels.append(data.get('label', data.get('category')))

    return texts, labels


def evaluate_model(model_path: str, test_path: str) -> Dict:
    """Evaluate model on test set."""
    print(f"Loading model from {model_path}...")
    classifier = EmbeddingClassifier()
    classifier.load(model_path)

    print(f"Loading test data from {test_path}...")
    texts, true_labels = load_test_data(test_path)
    print(f"Loaded {len(texts)} test examples")

    # Get predictions
    print("\nRunning predictions...")
    predictions = []
    confidences = []

    for text in texts:
        result = classifier.predict(text)
        predictions.append(result['category'])
        confidences.append(result['confidence'])

    # Calculate metrics
    accuracy = accuracy_score(true_labels, predictions)
    precision, recall, f1, support = precision_recall_fscore_support(
        true_labels, predictions, average='weighted', zero_division=0
    )

    # Per-class metrics
    class_report = classification_report(
        true_labels, predictions, output_dict=True, zero_division=0
    )

    # Confidence statistics
    avg_confidence = np.mean(confidences)

    # Count correct predictions by confidence level
    correct_high_conf = sum(1 for i, pred in enumerate(predictions)
                           if pred == true_labels[i] and confidences[i] > 0.8)
    correct_medium_conf = sum(1 for i, pred in enumerate(predictions)
                             if pred == true_labels[i] and 0.5 < confidences[i] <= 0.8)
    correct_low_conf = sum(1 for i, pred in enumerate(predictions)
                          if pred == true_labels[i] and confidences[i] <= 0.5)

    return {
        'accuracy': accuracy,
        'weighted_precision': precision,
        'weighted_recall': recall,
        'weighted_f1': f1,
        'avg_confidence': avg_confidence,
        'total_examples': len(texts),
        'correct_predictions': sum(1 for i in range(len(predictions)) if predictions[i] == true_labels[i]),
        'correct_high_conf': correct_high_conf,
        'correct_medium_conf': correct_medium_conf,
        'correct_low_conf': correct_low_conf,
        'class_report': class_report,
        'predictions': predictions,
        'true_labels': true_labels,
        'confidences': confidences
    }


def print_results(results: Dict):
    """Print evaluation results in a nice format."""
    print("\n" + "=" * 70)
    print("MODEL EVALUATION RESULTS")
    print("=" * 70)

    print(f"\nOverall Metrics:")
    print(f"  Total Examples:     {results['total_examples']}")
    print(f"  Correct:            {results['correct_predictions']}")
    print(f"  Accuracy:           {results['accuracy']:.2%}")
    print(f"  Weighted Precision: {results['weighted_precision']:.2%}")
    print(f"  Weighted Recall:    {results['weighted_recall']:.2%}")
    print(f"  Weighted F1:        {results['weighted_f1']:.2%}")
    print(f"  Avg Confidence:     {results['avg_confidence']:.2%}")

    print(f"\nPredictions by Confidence Level:")
    print(f"  High (>0.8):   {results['correct_high_conf']} correct")
    print(f"  Medium (0.5-0.8): {results['correct_medium_conf']} correct")
    print(f"  Low (<=0.5):   {results['correct_low_conf']} correct")

    print(f"\nPer-Category Performance:")
    print(f"{'Category':<30} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("-" * 70)

    class_report = results['class_report']
    for category in sorted(class_report.keys()):
        if category not in ['accuracy', 'macro avg', 'weighted avg']:
            metrics = class_report[category]
            print(f"{category:<30} {metrics['precision']:>9.2%} {metrics['recall']:>9.2%} "
                  f"{metrics['f1-score']:>9.2%} {metrics['support']:>10.0f}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Evaluate transaction classifier')
    parser.add_argument('--model', required=True, help='Path to trained model directory')
    parser.add_argument('--test', required=True, help='Path to test JSONL file')
    parser.add_argument('--output', help='Optional path to save results JSON')

    args = parser.parse_args()

    # Evaluate
    results = evaluate_model(args.model, args.test)

    # Print results
    print_results(results)

    # Save results if requested
    if args.output:
        # Remove non-serializable fields
        save_results = {k: v for k, v in results.items()
                       if k not in ['predictions', 'true_labels', 'confidences']}
        with open(args.output, 'w') as f:
            json.dump(save_results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
