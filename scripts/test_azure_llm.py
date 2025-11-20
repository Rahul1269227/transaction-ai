#!/usr/bin/env python3
"""
Test Azure GPT-5 LLM integration
"""

import os
import sys
import time
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_URL = "http://localhost:8000/categorize"

# Test transactions - choose ones that will trigger LLM
test_cases = [
    {"text": "Apple Inc Dividend Payment", "expected": "investments"},
    {"text": "State Farm Auto Insurance Premium", "expected": "insurance"},
    {"text": "Geico Home Insurance Monthly", "expected": "insurance"},
    {"text": "Fidelity 401k Contribution", "expected": "investments"},
    {"text": "Law Office Consultation Fee", "expected": "professional_services"},
]

def test_single_transaction(text: str, expected: str):
    """Test a single transaction"""
    print(f"\n{'='*80}")
    print(f"Testing: {text}")
    print(f"Expected: {expected}")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        response = requests.post(
            API_URL,
            json={"text": text},
            timeout=60
        )

        latency = (time.time() - start_time) * 1000

        if response.status_code != 200:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

        result = response.json()
        predicted = result.get("category")
        confidence = result.get("confidence", 0)
        reasoning = result.get("reasoning", {})

        print(f"\nPredicted: {predicted}")
        print(f"Confidence: {confidence:.2%}")
        print(f"Latency: {latency:.0f}ms")

        if "llm_reasoning" in reasoning:
            print(f"\nLLM Reasoning: {reasoning['llm_reasoning']}")

        if "method" in result:
            print(f"Method: {result['method']}")

        match = predicted == expected
        print(f"\n{'✅ PASS' if match else '❌ FAIL'}")

        return match

    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("\nIs the API running? Try: docker ps | grep txn-api")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("="*80)
    print("AZURE GPT-5 LLM TEST")
    print("="*80)

    # Check API is running
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ API Health: {health.status_code}")
    except Exception as e:
        print(f"❌ API not available: {e}")
        print("\nStart the API with:")
        print("  docker-compose -f infra/docker-compose.yaml up api")
        return

    # Run tests
    results = []
    for test in test_cases:
        passed = test_single_transaction(test["text"], test["expected"])
        results.append(passed)
        time.sleep(1)  # Brief pause between tests

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")

    if all(results):
        print("\n✅ All tests passed! Azure GPT-5 is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
