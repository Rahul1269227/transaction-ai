#!/usr/bin/env python3
"""
Test ensemble system performance on unseen data using the API endpoint.
"""
import requests
import json
import sys
from collections import defaultdict
from typing import Dict, List
import time

# Sample unseen test transactions (real-world examples)
TEST_TRANSACTIONS = [
    # Food & Dining
    "Starbucks coffee Grande", "McDonald's lunch meal", "Pizza Hut delivery",
    "Whole Foods grocery shopping", "Local farmers market",

    # Entertainment
    "Netflix monthly subscription", "Spotify Premium", "Movie tickets AMC",
    "PlayStation Store game purchase", "Steam summer sale",

    # Transport
    "Uber ride to airport", "Lyft downtown", "Metro card recharge",
    "Shell gas station", "Tesla Supercharger",

    # Shopping
    "Amazon Prime monthly", "Best Buy electronics", "Target groceries",
    "IKEA furniture", "Walmart shopping",

    # Bills & Utilities
    "Electric bill payment", "Water utility", "Internet service Comcast",
    "Phone bill AT&T", "Natural gas bill",

    # Healthcare
    "CVS Pharmacy prescription", "Doctor visit copay", "Dental cleaning",
    "Health insurance premium", "Emergency room visit",

    # Financial
    "Credit card payment", "Bank service charge", "Wire transfer fee",
    "Investment account deposit", "Savings account transfer",

    # Travel
    "United Airlines flight booking", "Hilton hotel reservation",
    "Airbnb accommodation", "Expedia travel package", "Car rental Enterprise",

    # Professional
    "LinkedIn Premium", "Adobe Creative Cloud", "Microsoft 365",
    "AWS cloud services", "Domain registration GoDaddy",

    # Personal Care
    "Gym membership", "Haircut salon", "Spa treatment",
    "Skincare products Sephora", "Vitamin supplements"
]


def test_transaction(text: str, api_url: str = "http://localhost:8000/categorize") -> Dict:
    """Test a single transaction through the API."""
    try:
        response = requests.post(
            api_url,
            json={"text": text},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "text": text}


def print_results(results: List[Dict]):
    """Print test results in a nice format."""
    print("\n" + "=" * 90)
    print("ENSEMBLE SYSTEM PERFORMANCE TEST - UNSEEN REAL-WORLD DATA")
    print("=" * 90)

    # Statistics
    total = len(results)
    errors = sum(1 for r in results if 'error' in r)
    successful = total - errors

    # Agreement stats
    full_agreement = sum(1 for r in results if r.get('ensemble_votes', {}).get('agreement_count', 0) == 3)
    partial_agreement = sum(1 for r in results if r.get('ensemble_votes', {}).get('agreement_count', 0) == 2)
    no_agreement = sum(1 for r in results if r.get('ensemble_votes', {}).get('agreement_count', 0) <= 1)

    # Method usage
    methods = defaultdict(int)
    for r in results:
        if 'method' in r:
            methods[r['method']] += 1

    # Review flags
    needs_review = sum(1 for r in results if r.get('requires_review', False))

    # Confidence stats
    confidences = [r.get('confidence', 0) for r in results if 'confidence' in r]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    high_conf = sum(1 for c in confidences if c > 0.8)
    medium_conf = sum(1 for c in confidences if 0.5 < c <= 0.8)
    low_conf = sum(1 for c in confidences if c <= 0.5)

    print(f"\nOverall Statistics:")
    print(f"  Total Transactions:      {total}")
    print(f"  Successfully Processed:  {successful} ({successful/total:.1%})")
    print(f"  Errors:                  {errors}")

    print(f"\nEnsemble Agreement:")
    print(f"  Full Agreement (3/3):    {full_agreement} ({full_agreement/successful:.1%})")
    print(f"  Partial Agreement (2/3): {partial_agreement} ({partial_agreement/successful:.1%})")
    print(f"  No Agreement (0-1/3):    {no_agreement} ({no_agreement/successful:.1%})")

    print(f"\nFinal Decision Method:")
    for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
        print(f"  {method.upper():8} {count:3} ({count/successful:.1%})")

    print(f"\nConfidence Distribution:")
    print(f"  High (>0.8):             {high_conf} ({high_conf/successful:.1%})")
    print(f"  Medium (0.5-0.8):        {medium_conf} ({medium_conf/successful:.1%})")
    print(f"  Low (<=0.5):             {low_conf} ({low_conf/successful:.1%})")
    print(f"  Average Confidence:      {avg_confidence:.1%}")

    print(f"\nReview Flags:")
    print(f"  Requires Review:         {needs_review} ({needs_review/successful:.1%})")

    print("\n" + "=" * 90)
    print("DETAILED RESULTS")
    print("=" * 90)
    print(f"{'Transaction':<35} {'Category':<20} {'Conf':>6} {'Method':>8} {'Agreement':>10}")
    print("-" * 90)

    for r in results:
        if 'error' in r:
            print(f"{r.get('text', 'Unknown'):<35} ERROR: {r['error']}")
        else:
            text = r.get('original_text', r.get('text', ''))[:35]
            category = r.get('category', 'Unknown')[:20]
            conf = r.get('confidence', 0)
            method = r.get('method', 'N/A')
            votes = r.get('ensemble_votes', {})
            agreement = f"{votes.get('agreement_count', 0)}/3"

            print(f"{text:<35} {category:<20} {conf:>5.0%} {method:>8} {agreement:>10}")

    print("=" * 90)


def main():
    print("Testing ensemble system with unseen real-world transactions...")
    print(f"Testing {len(TEST_TRANSACTIONS)} transactions")

    results = []
    start_time = time.time()

    for i, transaction in enumerate(TEST_TRANSACTIONS, 1):
        print(f"\rProgress: {i}/{len(TEST_TRANSACTIONS)}", end='', flush=True)
        result = test_transaction(transaction)
        results.append(result)
        time.sleep(0.1)  # Small delay to avoid overwhelming the server

    elapsed = time.time() - start_time
    print(f"\n\nCompleted in {elapsed:.1f}s ({elapsed/len(TEST_TRANSACTIONS):.2f}s per transaction)")

    print_results(results)

    # Save results
    output_file = "/tmp/ensemble_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to {output_file}")


if __name__ == '__main__':
    main()
