#!/usr/bin/env python3
"""
Create balanced train.jsonl and test.jsonl according to taxonomy
Uses existing data and balances all categories equally
"""

import json
import random
import yaml
from pathlib import Path
from collections import defaultdict

TARGET_SAMPLES_PER_CATEGORY = 800  # Target samples per category for training
TEST_SAMPLES_PER_CATEGORY = 200    # Target samples per category for testing

def load_jsonl(file_path):
    """Load JSONL file"""
    if not Path(file_path).exists():
        return []

    data = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except:
                pass
    return data

def save_jsonl(data, file_path):
    """Save to JSONL file"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def load_taxonomy():
    """Load taxonomy"""
    with open('data/taxonomy.yaml', 'r') as f:
        return yaml.safe_load(f)

def normalize_category(cat):
    """Normalize category to taxonomy ID format"""
    # Mapping from various formats to taxonomy IDs
    mappings = {
        'Income/Salary': 'income_salary',
        'Professional Services': 'professional_services',
        'Transfers/UPI': 'transfers_upi',
        'Transport': 'transport',
        'ATM/Cash': 'atm_cash',
        'Automotive': 'automotive',
        'Bills': 'bills',
        'Charity & Donations': 'charity_donations',
        'Education': 'education',
        'Electronics & Technology': 'electronics_technology',
        'Entertainment': 'entertainment',
        'Fees & Charges': 'fees_charges',
        'Food & Dining': 'food_dining',
        'Fuel': 'fuel',
        'Gifts & Special Occasions': 'gifts_occasions',
        'Groceries': 'groceries',
        'Health': 'health',
        'Home Improvement': 'home_improvement',
        'Insurance': 'insurance',
        'Investments': 'investments',
        'Kids & Family': 'kids_family',
        'Personal Care': 'personal_care',
        'Pets': 'pets',
        'Rent': 'rent',
        'Shopping': 'shopping',
        'Subscriptions & Memberships': 'subscriptions_memberships',
        'Taxes & Government': 'taxes_government',
        'Travel': 'travel',
    }

    return mappings.get(cat, cat.lower().replace(' ', '_').replace('/', '_').replace('&', '').replace('__', '_').strip('_'))

def main():
    print("=" * 80)
    print("CREATING BALANCED TRAIN/TEST DATASETS FROM TAXONOMY")
    print("=" * 80)
    print()

    # Load taxonomy
    taxonomy = load_taxonomy()
    valid_categories = {cat['id'] for cat in taxonomy['categories']}

    print(f"✓ Loaded taxonomy with {len(valid_categories)} categories:")
    for cat in sorted(valid_categories):
        print(f"  - {cat}")
    print()

    # Load existing data
    print("Loading existing data...")
    train_data = load_jsonl('data/train.jsonl')
    test_data = load_jsonl('data/test.jsonl')
    print(f"✓ Current train: {len(train_data)} samples")
    print(f"✓ Current test: {len(test_data)} samples")
    print()

    # Combine all data
    all_data = train_data + test_data
    print(f"✓ Total combined: {len(all_data)} samples")
    print()

    # Group by category
    by_category = defaultdict(list)
    unknown_count = 0

    for item in all_data:
        cat = item.get('label') or item.get('category', '')
        cat = normalize_category(cat) if cat else ''

        if cat in valid_categories:
            # Standardize format
            item['label'] = cat
            item['category'] = cat
            by_category[cat].append(item)
        else:
            unknown_count += 1

    if unknown_count > 0:
        print(f"⚠️  Skipped {unknown_count} samples with unknown/invalid categories")
        print()

    print("Category distribution BEFORE balancing:")
    print("-" * 60)
    for cat in sorted(valid_categories):
        count = len(by_category.get(cat, []))
        print(f"{cat:35s}: {count:5d} samples")
    print()

    # Balance each category
    print(f"Balancing to {TARGET_SAMPLES_PER_CATEGORY} training + {TEST_SAMPLES_PER_CATEGORY} test per category...")
    print()

    train_balanced = []
    test_balanced = []

    for cat in sorted(valid_categories):
        samples = by_category.get(cat, [])

        if not samples:
            print(f"⚠️  WARNING: No samples for '{cat}' - skipping")
            continue

        # Shuffle samples
        random.shuffle(samples)

        # Total needed
        total_needed = TARGET_SAMPLES_PER_CATEGORY + TEST_SAMPLES_PER_CATEGORY

        # If we have enough, sample directly
        if len(samples) >= total_needed:
            selected = random.sample(samples, total_needed)
        else:
            # Oversample by repeating
            selected = samples.copy()
            while len(selected) < total_needed:
                needed = total_needed - len(selected)
                selected.extend(random.sample(samples, min(len(samples), needed)))

        # Split into train/test
        train_balanced.extend(selected[:TARGET_SAMPLES_PER_CATEGORY])
        test_balanced.extend(selected[TARGET_SAMPLES_PER_CATEGORY:total_needed])

    # Shuffle final datasets
    random.shuffle(train_balanced)
    random.shuffle(test_balanced)

    print(f"✓ Balanced training: {len(train_balanced)} samples")
    print(f"✓ Balanced test: {len(test_balanced)} samples")
    print()

    # Save
    train_path = 'data/train.jsonl'
    test_path = 'data/test.jsonl'

    save_jsonl(train_balanced, train_path)
    save_jsonl(test_balanced, test_path)

    print("=" * 80)
    print("✅ BALANCED DATASETS CREATED")
    print("=" * 80)
    print(f"✓ Saved balanced train to: {train_path}")
    print(f"✓ Saved balanced test to: {test_path}")
    print()
    print(f"📊 Final distribution:")
    print(f"   - {len(train_balanced)} training samples ({TARGET_SAMPLES_PER_CATEGORY} per category)")
    print(f"   - {len(test_balanced)} test samples ({TEST_SAMPLES_PER_CATEGORY} per category)")
    print()


if __name__ == "__main__":
    random.seed(42)
    main()
