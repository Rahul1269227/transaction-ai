#!/usr/bin/env python3
"""
Test LightGBM model on 50 real-time transaction samples
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.model.classifier import TransactionClassifier
from core.preprocessing.normalizer import TransactionNormalizer
from core.features.extractor import FeatureExtractor


def main():
    print("\n" + "="*80)
    print("REAL-TIME TRANSACTION TEST - 50 SAMPLES")
    print("="*80)
    print()

    # Load model
    model_path = "models/transaction_classifier"
    print(f"Loading model from {model_path}...")
    classifier = TransactionClassifier(model_path=model_path)
    print(f"✓ Model loaded\n")

    # Load test data
    test_file = "data/realtime_test_50.jsonl"
    print(f"Loading test data from {test_file}...")

    test_data = []
    with open(test_file, 'r') as f:
        for line in f:
            test_data.append(json.loads(line.strip()))

    print(f"✓ Loaded {len(test_data)} test samples\n")

    # Initialize normalizer
    normalizer = TransactionNormalizer(
        taxonomy_path="data/taxonomy.yaml",
        gazetteer_path="data/gazetteer/merchant_aliases.csv"
    )

    # Test each transaction
    results = []
    correct = 0
    total = 0

    print("="*80)
    print("PREDICTIONS")
    print("="*80)
    print()

    for i, item in enumerate(test_data, 1):
        # Normalize
        normalized = normalizer.normalize(
            text=item['text'],
            amount=item.get('amount', 0.0),
            date=item.get('date', '2025-11-19')
        )

        # Extract features
        features = FeatureExtractor.extract_features(normalized)

        # Predict
        predictions = classifier.predict(
            texts=[item['text']],
            handcrafted_features=[features],
            top_k=3
        )

        pred_category = predictions[0]['category']
        pred_confidence = predictions[0]['confidence']
        expected = item.get('expected_category', 'unknown')

        is_correct = (pred_category == expected)
        if is_correct:
            correct += 1
        total += 1

        # Display result
        status = "✓" if is_correct else "✗"
        print(f"{i:2d}. [{status}] {item['text'][:50]:50s}")
        print(f"    Expected: {expected:30s} | Predicted: {pred_category:30s} (conf: {pred_confidence:.2%})")

        if not is_correct:
            print(f"    Top 3: ", end="")
            for p in predictions[:3]:
                print(f"{p['category']} ({p['confidence']:.2%}), ", end="")
            print()

        print()

        results.append({
            'text': item['text'],
            'expected': expected,
            'predicted': pred_category,
            'confidence': pred_confidence,
            'correct': is_correct
        })

    # Summary
    accuracy = correct / total

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Samples:     {total}")
    print(f"Correct:           {correct}")
    print(f"Incorrect:         {total - correct}")
    print(f"Accuracy:          {accuracy:.2%}")
    print()

    # Category-wise breakdown
    from collections import defaultdict
    category_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

    for r in results:
        cat = r['expected']
        category_stats[cat]['total'] += 1
        if r['correct']:
            category_stats[cat]['correct'] += 1

    print("="*80)
    print("CATEGORY-WISE ACCURACY")
    print("="*80)
    for cat in sorted(category_stats.keys()):
        stats = category_stats[cat]
        cat_acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        print(f"{cat:30s}: {stats['correct']:2d}/{stats['total']:2d} = {cat_acc:.2%}")

    print()
    print("="*80)

    # Confidence distribution
    confidences = [r['confidence'] for r in results]
    avg_confidence = sum(confidences) / len(confidences)
    min_confidence = min(confidences)
    max_confidence = max(confidences)

    print("CONFIDENCE STATISTICS")
    print("="*80)
    print(f"Average Confidence: {avg_confidence:.2%}")
    print(f"Min Confidence:     {min_confidence:.2%}")
    print(f"Max Confidence:     {max_confidence:.2%}")
    print()

    # Save results
    output_file = "data/realtime_test_50_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total': total,
                'correct': correct,
                'accuracy': accuracy,
                'avg_confidence': avg_confidence
            },
            'results': results,
            'category_stats': dict(category_stats)
        }, f, indent=2)

    print(f"✓ Results saved to {output_file}")
    print()

    if accuracy >= 0.90:
        print("✅ PASS: Accuracy >= 90%")
    else:
        print("⚠️  WARNING: Accuracy < 90%")

    print()


if __name__ == "__main__":
    main()
