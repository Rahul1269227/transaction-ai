"""
Simple test script to demonstrate API usage
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_single_categorization():
    """Test single transaction categorization"""
    print("🎯 Testing single transaction categorization...")

    transaction = {
        "text": "UPI-1234567890-ZOMATO PAY*ABCD",
        "amount": 249.00,
        "date": "2025-11-10",
        "currency": "INR"
    }

    response = requests.post(
        f"{BASE_URL}/categorize",
        json=transaction
    )

    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Category: {result['category']}")
    print(f"Subcategory: {result['subcategory']}")
    print(f"Confidence: {result['confidence']:.4f}")
    print(f"Method: {result['method']}")
    print(f"Explanations: {result['explanations']}")
    print()

def test_batch_categorization():
    """Test batch categorization"""
    print("📦 Testing batch categorization...")

    transactions = [
        {"text": "UPI-ZOMATO", "amount": 249.00},
        {"text": "POS HPCL KANPUR", "amount": 1200.00},
        {"text": "ATM WDL 1234", "amount": 5000.00},
        {"text": "UPI-BIGBASKET", "amount": 1850.00},
        {"text": "NETFLIX SUBSCRIPTION", "amount": 649.00}
    ]

    response = requests.post(
        f"{BASE_URL}/categorize/batch",
        json={"transactions": transactions}
    )

    print(f"Status: {response.status_code}")
    result = response.json()

    print(f"\nResults:")
    for i, txn_result in enumerate(result['results']):
        print(f"{i+1}. {txn_result['original_text']:40s} -> {txn_result['category']:20s} ({txn_result['confidence']:.2f})")

    print(f"\nStats:")
    print(f"  Total: {result['stats']['total']}")
    print(f"  Avg Confidence: {result['stats']['avg_confidence']:.4f}")
    print(f"  Requires Review: {result['stats']['requires_review']}")
    print()

def test_merchant_search():
    """Test merchant search"""
    print("🔍 Testing merchant search...")

    response = requests.post(
        f"{BASE_URL}/merchants",
        json={"query": "zomato", "limit": 5}
    )

    print(f"Status: {response.status_code}")
    result = response.json()

    print(f"Query: {result['query']}")
    print(f"Matches:")
    for match in result['matches']:
        print(f"  - {match['canonical_name']:20s} (similarity: {match['similarity_score']:.2f})")
    print()

def main():
    """Run all tests"""
    print("=" * 60)
    print("Transaction AI Categorization - API Test")
    print("=" * 60)
    print()

    try:
        test_health()
        test_single_categorization()
        test_batch_categorization()
        test_merchant_search()

        print("✅ All tests passed!")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Is it running?")
        print("Start the API with: python apps/api/main.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
