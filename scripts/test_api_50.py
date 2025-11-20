#!/usr/bin/env python3
"""
Test API with 50 real-time transaction samples
"""

import json
import requests
import time
from collections import defaultdict


def test_api():
    api_url = "http://localhost:8000/categorize"

    print("\n" + "="*80)
    print("REAL-TIME API TEST - 50 TRANSACTIONS")
    print("="*80)
    print()

    # Load test data
    test_file = "data/realtime_test_50.jsonl"
    print(f"Loading test data from {test_file}...")

    test_data = []
    with open(test_file, 'r') as f:
        for line in f:
            test_data.append(json.loads(line.strip()))

    print(f"✓ Loaded {len(test_data)} test samples\n")

    # Test each transaction
    results = []
    correct = 0
    total = 0
    total_time = 0

    print("="*80)
    print("PREDICTIONS")
    print("="*80)
    print()

    for i, item in enumerate(test_data, 1):
        # Prepare request
        payload = {
            "text": item['text'],
            "amount": item.get('amount', 0.0),
            "currency": item.get('currency', 'USD'),
            "date": item.get('date', '2025-11-19')
        }

        # Make API call
        start_time = time.time()
        try:
            response = requests.post(api_url, json=payload, timeout=30)
            elapsed = time.time() - start_time
            total_time += elapsed

            if response.status_code == 200:
                result = response.json()
                pred_category = result['category']
                pred_confidence = result['confidence']
                expected = item.get('expected_category', 'unknown')

                is_correct = (pred_category == expected)
                if is_correct:
                    correct += 1
                total += 1

                # Display result
                status = "✓" if is_correct else "✗"
                print(f"{i:2d}. [{status}] {item['text'][:50]:50s}")
                print(f"    Expected:  {expected:30s}")
                print(f"    Predicted: {pred_category:30s} (conf: {pred_confidence:.2%}, {elapsed*1000:.0f}ms)")

                if not is_correct and 'alternate_categories' in result:
                    alts = [f"{c['category']} ({c['confidence']:.2%})" for c in result['alternate_categories'][:2]]
                    print(f"    Alternates: {', '.join(alts)}")

                results.append({
                    'text': item['text'],
                    'expected': expected,
                    'predicted': pred_category,
                    'confidence': pred_confidence,
                    'correct': is_correct,
                    'latency_ms': elapsed * 1000
                })

            else:
                print(f"{i:2d}. [ERROR] {item['text'][:50]:50s}")
                print(f"    HTTP {response.status_code}: {response.text}")
                total += 1

        except Exception as e:
            print(f"{i:2d}. [ERROR] {item['text'][:50]:50s}")
            print(f"    Exception: {e}")
            total += 1

        print()

    # Summary
    accuracy = correct / total if total > 0 else 0
    avg_latency = total_time / total if total > 0 else 0

    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Samples:     {total}")
    print(f"Correct:           {correct}")
    print(f"Incorrect:         {total - correct}")
    print(f"Accuracy:          {accuracy:.2%}")
    print(f"Avg Latency:       {avg_latency*1000:.0f}ms")
    print(f"Total Time:        {total_time:.1f}s")
    print()

    # Category-wise breakdown
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
        print(f"{cat:30s}: {stats['correct']:2d}/{stats['total']:2d} = {cat_acc:6.2%}")

    print()

    # Confidence statistics
    if results:
        confidences = [r['confidence'] for r in results]
        latencies = [r['latency_ms'] for r in results]

        print("="*80)
        print("CONFIDENCE & LATENCY STATISTICS")
        print("="*80)
        print(f"Avg Confidence:    {sum(confidences)/len(confidences):.2%}")
        print(f"Min Confidence:    {min(confidences):.2%}")
        print(f"Max Confidence:    {max(confidences):.2%}")
        print(f"Avg Latency:       {sum(latencies)/len(latencies):.0f}ms")
        print(f"Min Latency:       {min(latencies):.0f}ms")
        print(f"Max Latency:       {max(latencies):.0f}ms")
        print()

    # Save results
    output_file = "data/realtime_test_50_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total': total,
                'correct': correct,
                'accuracy': accuracy,
                'avg_confidence': sum(confidences)/len(confidences) if confidences else 0,
                'avg_latency_ms': avg_latency * 1000
            },
            'results': results,
            'category_stats': {k: dict(v) for k, v in category_stats.items()}
        }, f, indent=2)

    print(f"✓ Results saved to {output_file}")
    print()

    if accuracy >= 0.90:
        print("✅ PASS: Accuracy >= 90%")
    else:
        print("⚠️  WARNING: Accuracy < 90%")

    print()
    print("="*80)


if __name__ == "__main__":
    test_api()
