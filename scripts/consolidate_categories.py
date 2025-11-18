#!/usr/bin/env python3
"""
Category Consolidation Script
Standardizes all category names across datasets to use taxonomy IDs
"""

import json
import os
from collections import Counter
from typing import Dict

# Category mapping: old_name -> standardized_id
CATEGORY_MAPPING = {
    # Title Case to ID
    "Food & Dining": "food_dining",
    "Groceries": "groceries",
    "Transport": "transport",
    "Travel": "travel",
    "Fuel": "fuel",
    "Utilities": "bills",
    "Rent": "rent",
    "Shopping": "shopping",
    "Entertainment": "entertainment",
    "Health": "health",
    "Education": "education",
    "Fees & Charges": "fees_charges",
    "Income/Salary": "income_salary",
    "Transfers/UPI": "transfers_upi",
    "ATM/Cash": "atm_cash",
    "Investments": "investments",
    "Bills": "bills",
    "Fraud & Security": "fraud_security",

    # Lowercase (already correct, but mapping for consistency)
    "food_dining": "food_dining",
    "groceries": "groceries",
    "transport": "transport",
    "travel": "travel",
    "fuel": "fuel",
    "utilities": "bills",
    "rent": "rent",
    "shopping": "shopping",
    "entertainment": "entertainment",
    "health": "health",
    "education": "education",
    "fees_charges": "fees_charges",
    "income_salary": "income_salary",
    "transfers_upi": "transfers_upi",
    "atm_cash": "atm_cash",
    "investments": "investments",
    "bills": "bills",
    "fraud_security": "fraud_security",
    "insurance": "insurance",
    "charity_donations": "charity_donations",
    "personal_care": "personal_care",
    "pets": "pets",
    "home_improvement": "home_improvement",
    "automotive": "automotive",
    "taxes_government": "taxes_government",
    "electronics_technology": "electronics_technology",
    "professional_services": "professional_services",
    "kids_family": "kids_family",
    "subscriptions_memberships": "subscriptions_memberships",
    "gifts_occasions": "gifts_occasions",
    "other": "other",
}


def consolidate_dataset(input_path: str, output_path: str) -> Dict:
    """
    Consolidate categories in a dataset file

    Args:
        input_path: Path to input JSONL file
        output_path: Path to output JSONL file

    Returns:
        Statistics dictionary
    """
    stats = {
        'total': 0,
        'updated': 0,
        'unchanged': 0,
        'unmapped': 0,
        'category_distribution': Counter()
    }

    unmapped_categories = set()

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:

        for line in infile:
            stats['total'] += 1
            data = json.loads(line.strip())

            # Get category from either 'category' or 'label' field
            old_category = data.get('category', data.get('label', ''))

            if old_category in CATEGORY_MAPPING:
                new_category = CATEGORY_MAPPING[old_category]
                if old_category != new_category:
                    stats['updated'] += 1
                else:
                    stats['unchanged'] += 1

                # Update both fields for compatibility
                data['category'] = new_category
                data['label'] = new_category

                stats['category_distribution'][new_category] += 1
            else:
                stats['unmapped'] += 1
                unmapped_categories.add(old_category)
                # Keep original category
                if 'label' not in data:
                    data['label'] = data.get('category', '')

            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

    if unmapped_categories:
        print(f"⚠️  Warning: Found unmapped categories: {unmapped_categories}")

    return stats


def main():
    print("=" * 80)
    print("🔄 CATEGORY CONSOLIDATION SCRIPT")
    print("=" * 80)
    print()

    # Define datasets to process
    datasets = [
        {
            'name': 'Original Training Data',
            'input': 'data/balanced/train.jsonl',
            'output': 'data/balanced/train_consolidated.jsonl'
        },
        {
            'name': 'Original Test Data',
            'input': 'data/balanced/test.jsonl',
            'output': 'data/balanced/test_consolidated.jsonl'
        },
        {
            'name': 'Kaggle Training Data',
            'input': 'data/balanced/train_with_kaggle.jsonl',
            'output': 'data/balanced/train_with_kaggle_consolidated.jsonl'
        },
        {
            'name': 'Kaggle Test Data',
            'input': 'data/balanced/test_with_kaggle.jsonl',
            'output': 'data/balanced/test_with_kaggle_consolidated.jsonl'
        },
        {
            'name': 'Synthetic New Categories Training',
            'input': 'data/synthetic_new_categories/train.jsonl',
            'output': 'data/synthetic_new_categories/train_consolidated.jsonl'
        },
        {
            'name': 'Synthetic New Categories Test',
            'input': 'data/synthetic_new_categories/test.jsonl',
            'output': 'data/synthetic_new_categories/test_consolidated.jsonl'
        },
        {
            'name': 'Kaggle New Categories Training',
            'input': 'data/kaggle_new_categories/train.jsonl',
            'output': 'data/kaggle_new_categories/train_consolidated.jsonl'
        },
        {
            'name': 'Kaggle New Categories Test',
            'input': 'data/kaggle_new_categories/test.jsonl',
            'output': 'data/kaggle_new_categories/test_consolidated.jsonl'
        },
        {
            'name': 'Improved Weak Categories Training',
            'input': 'data/improved_weak_categories/train.jsonl',
            'output': 'data/improved_weak_categories/train_consolidated.jsonl'
        },
        {
            'name': 'Improved Weak Categories Test',
            'input': 'data/improved_weak_categories/test.jsonl',
            'output': 'data/improved_weak_categories/test_consolidated.jsonl'
        },
        {
            'name': 'Balanced Kaggle Training',
            'input': 'data/balanced_kaggle/train.jsonl',
            'output': 'data/balanced_kaggle/train_consolidated.jsonl'
        },
        {
            'name': 'Balanced Kaggle Test',
            'input': 'data/balanced_kaggle/test.jsonl',
            'output': 'data/balanced_kaggle/test_consolidated.jsonl'
        }
    ]

    all_stats = {}
    total_updated = 0
    total_processed = 0

    for dataset in datasets:
        if not os.path.exists(dataset['input']):
            print(f"⏭️  Skipping {dataset['name']} (file not found)")
            continue

        print(f"\n📄 Processing: {dataset['name']}")
        print(f"   Input:  {dataset['input']}")
        print(f"   Output: {dataset['output']}")

        stats = consolidate_dataset(dataset['input'], dataset['output'])
        all_stats[dataset['name']] = stats
        total_updated += stats['updated']
        total_processed += stats['total']

        print(f"   ✓ Total:     {stats['total']:6d}")
        print(f"   ✓ Updated:   {stats['updated']:6d}")
        print(f"   ✓ Unchanged: {stats['unchanged']:6d}")
        if stats['unmapped'] > 0:
            print(f"   ⚠️  Unmapped:  {stats['unmapped']:6d}")

    # Summary
    print()
    print("=" * 80)
    print("📊 CONSOLIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Transactions Processed: {total_processed:,}")
    print(f"Total Categories Updated:     {total_updated:,}")
    print()

    # Aggregate category distribution
    aggregate_dist = Counter()
    for stats in all_stats.values():
        aggregate_dist.update(stats['category_distribution'])

    print("Final Category Distribution:")
    print("-" * 60)
    for category, count in sorted(aggregate_dist.items()):
        print(f"  {category:35s} : {count:7,}")
    print()
    print(f"Total unique categories: {len(aggregate_dist)}")

    print()
    print("✅ Consolidation complete!")
    print()
    print("Next steps:")
    print("  1. Review consolidated files in data/balanced/*_consolidated.jsonl")
    print("  2. Run: python3 scripts/train.py")
    print("  3. The training script will use consolidated datasets automatically")


if __name__ == '__main__':
    main()
