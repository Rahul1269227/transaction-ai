#!/usr/bin/env python3
"""
Create Balanced Training Dataset
Merges Indian and US merchant data, balances categories
"""

import json
import random
from collections import Counter
from pathlib import Path

def load_jsonl(file_path):
    """Load JSONL file"""
    samples = []
    with open(file_path, 'r') as f:
        for line in f:
            samples.append(json.loads(line.strip()))
    return samples

def save_jsonl(samples, file_path):
    """Save JSONL file"""
    with open(file_path, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')

def balance_categories(samples, target_per_category=800):
    """Balance categories by sampling or duplicating"""
    category_samples = {}

    # Group by category
    for sample in samples:
        category = sample.get('category') or sample.get('label')
        if category not in category_samples:
            category_samples[category] = []
        category_samples[category].append(sample)

    balanced = []

    for category, cat_samples in category_samples.items():
        count = len(cat_samples)

        if count >= target_per_category:
            # Sample down
            selected = random.sample(cat_samples, target_per_category)
        else:
            # Sample up (with replacement)
            selected = cat_samples.copy()
            while len(selected) < target_per_category:
                selected.append(random.choice(cat_samples))

        balanced.extend(selected)
        print(f"  {category}: {count} → {len(selected)}")

    return balanced

def main():
    """Create balanced dataset"""

    print("Creating balanced training dataset...")
    print("=" * 60)

    # Load existing Indian data
    print("\n1. Loading existing Indian merchant data...")
    indian_train = load_jsonl("data/train.jsonl")
    indian_test = load_jsonl("data/test.jsonl")
    print(f"   Loaded {len(indian_train)} Indian train samples")
    print(f"   Loaded {len(indian_test)} Indian test samples")

    # Load US merchant data
    print("\n2. Loading US merchant data...")
    us_train = load_jsonl("data/us_merchants_train.jsonl")
    us_test = load_jsonl("data/us_merchants_test.jsonl")
    print(f"   Loaded {len(us_train)} US train samples")
    print(f"   Loaded {len(us_test)} US test samples")

    # Merge datasets
    print("\n3. Merging datasets...")
    all_train = indian_train + us_train
    all_test = indian_test + us_test
    print(f"   Total train samples: {len(all_train)}")
    print(f"   Total test samples: {len(all_test)}")

    # Count categories
    print("\n4. Category distribution before balancing:")
    train_categories = Counter(s.get('category') or s.get('label') for s in all_train)
    for category, count in sorted(train_categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {category}: {count}")

    # Balance training data
    print("\n5. Balancing training data (target: 800 per category)...")
    balanced_train = balance_categories(all_train, target_per_category=800)

    # Balance test data
    print("\n6. Balancing test data (target: 200 per category)...")
    balanced_test = balance_categories(all_test, target_per_category=200)

    # Shuffle
    random.shuffle(balanced_train)
    random.shuffle(balanced_test)

    # Save
    print("\n7. Saving balanced datasets...")
    save_jsonl(balanced_train, "data/balanced_train.jsonl")
    save_jsonl(balanced_test, "data/balanced_test.jsonl")

    print("\n" + "=" * 60)
    print(f"✓ Saved {len(balanced_train)} balanced train samples")
    print(f"✓ Saved {len(balanced_test)} balanced test samples")

    # Final distribution
    print("\n8. Final category distribution:")
    final_categories = Counter(s.get('category') or s.get('label') for s in balanced_train)
    for category, count in sorted(final_categories.items()):
        print(f"   {category}: {count}")

    print("\n✅ Balanced dataset created successfully!")

if __name__ == "__main__":
    main()
