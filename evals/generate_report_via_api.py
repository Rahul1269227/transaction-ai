#!/usr/bin/env python3
"""
Generate evaluation report using the live API
Uses known transactions with expected categories
"""

import json
import time
import requests

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

API_URL = "http://localhost:8000/categorize"

def main():
    print("\n" + "="*80)
    print("TRANSACTION AI - EVALUATION REPORT (via API)")
    print("="*80)
    print()

    # Evaluate
    results = []
    correct = 0
    total = 0
    total_time = 0

    print("Evaluating transactions via API...")
    print("-" * 80)

    for i, item in enumerate(KNOWN_TRANSACTIONS, 1):
        start = time.time()

        try:
            response = requests.post(
                API_URL,
                json={"text": item["text"]},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            duration = time.time() - start

            predicted = result["category"]
            expected = item["expected"]
            confidence = result["confidence"]
            method = result.get("method", "unknown")
            is_correct = (predicted == expected)

            if is_correct:
                correct += 1
            total += 1
            total_time += duration

            status = "✓" if is_correct else "✗"
            print(f"{i:2d}. [{status}] {item['text'][:45]:45s}")
            print(f"    Expected: {expected:25s} | Predicted: {predicted:25s} (conf: {confidence:.2%}, {duration*1000:.0f}ms)")

            results.append({
                "transaction": item["text"],
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "correct": is_correct,
                "duration_ms": duration * 1000,
                "method": method,
            })
        except Exception as e:
            print(f"{i:2d}. [ERROR] {item['text'][:45]:45s}")
            print(f"    Error: {str(e)}")
            results.append({
                "transaction": item["text"],
                "expected": item["expected"],
                "predicted": "ERROR",
                "confidence": 0.0,
                "correct": False,
                "duration_ms": 0,
                "method": "error",
                "error": str(e)
            })

        print()

    # Calculate metrics
    accuracy = correct / total if total > 0 else 0
    avg_latency = (total_time / total) * 1000 if total > 0 else 0
    avg_confidence = sum(r["confidence"] for r in results) / len(results) if results else 0

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
    method_counts = Counter(r["method"] for r in results if "error" not in r)
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
            "api_url": API_URL,
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

    output_path = "evals/reports/api_evaluation_report.json"
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
