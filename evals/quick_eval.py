#!/usr/bin/env python3
"""
Quick evaluation script with known transactions
Generates a comprehensive report for submission
"""

import json
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.model.ensemble_router import EnsembleRouter

# Known test transactions with expected categories
KNOWN_TRANSACTIONS = [
    {"text": "Netflix subscription", "expected": "entertainment"},
    {"text": "Starbucks coffee", "expected": "food_dining"},
    {"text": "Uber ride to airport", "expected": "transportation"},
    {"text": "Amazon shopping", "expected": "shopping"},
    {"text": "CVS Pharmacy medicines", "expected": "healthcare"},
    {"text": "Shell gas station", "expected": "automotive"},
    {"text": "Verizon monthly bill", "expected": "bills_utilities"},
    {"text": "Whole Foods groceries", "expected": "groceries"},
    {"text": "Planet Fitness gym", "expected": "fitness"},
    {"text": "Chase bank fee", "expected": "fees_charges"},
    {"text": "Salary deposit", "expected": "income_salary"},
    {"text": "Target shopping", "expected": "shopping"},
    {"text": "McDonald's lunch", "expected": "food_dining"},
    {"text": "Walmart groceries", "expected": "groceries"},
    {"text": "Delta Airlines flight", "expected": "travel"},
    {"text": "Marriott Hotel", "expected": "travel"},
    {"text": "AT&T phone bill", "expected": "bills_utilities"},
    {"text": "Spotify premium", "expected": "entertainment"},
    {"text": "Apple Store purchase", "expected": "electronics_technology"},
    {"text": "Rent payment", "expected": "rent_mortgage"},
]

def main():
    print("\n" + "="*80)
    print("TRANSACTION AI - EVALUATION REPORT")
    print("="*80)
    print()

    # Initialize router
    print("Initializing ensemble router...")
    router = EnsembleRouter(
        taxonomy_path="data/taxonomy.yaml",
        gazetteer_path="data/gazetteer/merchant_aliases.csv",
        ml_model_path="models/transaction_classifier",
        rule_weight=0.25,
        ml_weight=0.30,
        llm_weight=0.00,  # Disable LLM for quick evaluation
    )
    print("✓ Router initialized\n")

    # Evaluate
    results = []
    correct = 0
    total = 0
    total_time = 0

    print("Evaluating transactions...")
    print("-" * 80)

    for i, item in enumerate(KNOWN_TRANSACTIONS, 1):
        start = time.time()
        result = router.categorize({"text": item["text"]})
        duration = time.time() - start

        predicted = result.category
        expected = item["expected"]
        is_correct = (predicted == expected)

        if is_correct:
            correct += 1
        total += 1
        total_time += duration

        status = "✓" if is_correct else "✗"
        print(f"{i:2d}. [{status}] {item['text'][:45]:45s}")
        print(f"    Expected: {expected:20s} | Predicted: {predicted:20s} (conf: {result.confidence:.2%}, {duration*1000:.0f}ms)")

        results.append({
            "transaction": item["text"],
            "expected": expected,
            "predicted": predicted,
            "confidence": result.confidence,
            "correct": is_correct,
            "duration_ms": duration * 1000,
            "method": result.method,
        })
        print()

    # Calculate metrics
    accuracy = correct / total
    avg_latency = (total_time / total) * 1000
    avg_confidence = sum(r["confidence"] for r in results) / len(results)

    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Transactions:    {total}")
    print(f"Correct Predictions:   {correct}")
    print(f"Incorrect Predictions: {total - correct}")
    print(f"Accuracy:              {accuracy:.2%}")
    print(f"Average Confidence:    {avg_confidence:.2%}")
    print(f"Average Latency:       {avg_latency:.0f}ms")
    print(f"Total Duration:        {total_time:.1f}s")
    print()

    # Method breakdown
    from collections import Counter
    method_counts = Counter(r["method"] for r in results)
    print("=" * 80)
    print("METHOD BREAKDOWN")
    print("=" * 80)
    for method, count in method_counts.most_common():
        pct = (count / total) * 100
        print(f"{method:20s}: {count:2d} ({pct:5.1f}%)")
    print()

    # Save report
    report = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_transactions": total,
            "model_path": "models/transaction_classifier",
            "router_config": {
                "rule_weight": 0.25,
                "ml_weight": 0.30,
                "llm_weight": 0.00,
                "use_ensemble": True,
            }
        },
        "summary": {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "avg_confidence": avg_confidence,
            "avg_latency_ms": avg_latency,
            "total_duration_s": total_time,
        },
        "method_breakdown": dict(method_counts),
        "results": results,
    }

    output_path = "evals/reports/quick_evaluation_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✓ Report saved to {output_path}")
    print()

    if accuracy >= 0.90:
        print("✅ PASS: Accuracy >= 90%")
    else:
        print("⚠️  WARNING: Accuracy < 90%")

    print()


if __name__ == "__main__":
    main()
