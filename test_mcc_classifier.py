#!/usr/bin/env python3
"""
Test script for MCC-based transaction categorization
Validates that MCC codes are properly mapped to categories
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from core.model.mcc_classifier import MCCClassifier


def test_mcc_classifier():
    """Test MCC classifier with various transaction scenarios"""

    print("=" * 70)
    print("Testing MCC-Based Transaction Categorization")
    print("=" * 70)

    classifier = MCCClassifier()

    # Test cases: (description, mcc_code, expected_category)
    test_cases = [
        ("Restaurant transaction", "5812", "Food & Dining"),
        ("Fast food purchase", "5814", "Food & Dining"),
        ("Grocery store", "5411", "Groceries"),
        ("Taxi ride", "4121", "Transport"),
        ("Airline ticket", "3004", "Travel"),
        ("Hotel booking", "7011", "Travel"),
        ("Fuel station", "5541", "Fuel"),
        ("Gas station automated", "5542", "Fuel"),
        ("Pharmacy", "5912", "Health"),
        ("Hospital visit", "8062", "Health"),
        ("University fees", "8220", "Education"),
        ("ATM withdrawal", "6011", "ATM/Cash"),
        ("Electronics store", "5732", "Shopping"),
        ("Department store", "5311", "Shopping"),
        ("Movie theater", "7832", "Entertainment"),
        ("Utility bill", "4900", "Bills"),  # MCC 4900 maps to Bills category
        ("Telecom service", "4814", "Bills"),  # MCC 4814 maps to Bills category
        ("Insurance premium", "6300", "Investments"),
        ("Unknown MCC", "9999", "Other"),
        ("No MCC", None, "Other"),
    ]

    passed = 0
    failed = 0

    for description, mcc, expected in test_cases:
        result = classifier.categorize(text=description, mcc=mcc)

        status = "✓" if result['category'] == expected else "✗"
        confidence = result['confidence']
        mcc_code = result.get('mcc_code', 'N/A')

        if result['category'] == expected:
            passed += 1
            print(f"{status} {description:30s} | MCC: {str(mcc_code):4s} | {result['category']:20s} | Conf: {confidence:.2f}")
        else:
            failed += 1
            print(f"{status} {description:30s} | MCC: {str(mcc_code):4s} | Expected: {expected:20s} | Got: {result['category']:20s} | Conf: {confidence:.2f}")

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Success rate: {passed/len(test_cases)*100:.1f}%")
    print("=" * 70)

    return failed == 0


def test_mcc_coverage():
    """Test MCC mapping coverage"""

    print("\n" + "=" * 70)
    print("MCC Mapping Coverage Analysis")
    print("=" * 70)

    classifier = MCCClassifier()

    # Group MCCs by category
    categories = {}
    for mcc, category in classifier.mcc_mapping.items():
        if category not in categories:
            categories[category] = []
        categories[category].append(mcc)

    print(f"\nTotal MCC codes mapped: {len(classifier.mcc_mapping)}")
    print(f"Total categories covered: {len(categories)}")
    print(f"\nMCCs per category:")
    print("-" * 70)

    for category in sorted(categories.keys()):
        mccs = categories[category]
        print(f"{category:25s}: {len(mccs):3d} MCCs")

    print("-" * 70)
    print(f"\nHigh-confidence MCCs: {len(classifier.high_confidence_mccs)}")

    # Show some examples
    print(f"\nSample high-confidence MCCs:")
    sample_high_conf = list(classifier.high_confidence_mccs)[:10]
    for mcc in sample_high_conf:
        category = classifier.mcc_mapping.get(mcc, "Unknown")
        print(f"  {mcc}: {category}")

    print("=" * 70)


if __name__ == "__main__":
    print("\n🧪 Starting MCC Classifier Tests\n")

    # Run tests
    test_passed = test_mcc_classifier()
    test_mcc_coverage()

    # Exit with appropriate code
    if test_passed:
        print("\n✅ All tests passed!\n")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!\n")
        sys.exit(1)
