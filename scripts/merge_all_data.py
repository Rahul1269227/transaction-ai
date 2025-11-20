#!/usr/bin/env python3
"""
Merge ALL data sources and create one balanced dataset
"""

import json
import random
from collections import Counter
from pathlib import Path
import glob

def load_jsonl(file_path):
    """Load JSONL file"""
    samples = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line.strip()))
    except Exception as e:
        print(f"Warning: Could not load {file_path}: {e}")
    return samples

def save_jsonl(samples, file_path):
    """Save JSONL file"""
    with open(file_path, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')

def balance_categories(samples, target_per_category=600):
    """Balance categories"""
    category_samples = {}

    # Group by category
    for sample in samples:
        category = sample.get('category') or sample.get('label')
        if not category:
            continue
        if category not in category_samples:
            category_samples[category] = []
        category_samples[category].append(sample)

    balanced = []

    for category, cat_samples in sorted(category_samples.items()):
        count = len(cat_samples)

        if count >= target_per_category:
            selected = random.sample(cat_samples, target_per_category)
        else:
            selected = cat_samples.copy()
            while len(selected) < target_per_category:
                selected.append(random.choice(cat_samples))

        balanced.extend(selected)
        print(f"  {category:30s}: {count:5d} → {len(selected):5d}")

    return balanced

def main():
    print("=" * 70)
    print("MERGING ALL DATA SOURCES")
    print("=" * 70)

    all_samples = []

    # Find all JSONL files in data/
    jsonl_files = [
        "data/train_original.jsonl",
        "data/test_original.jsonl",
        "data/us_merchants_train.jsonl",
        "data/us_merchants_test.jsonl",
        "data/phonepe_labeled.jsonl",
        "data/icici_labeled.jsonl",
    ]

    print("\n1. Loading all data files...")
    for file_path in jsonl_files:
        if Path(file_path).exists():
            samples = load_jsonl(file_path)
            all_samples.extend(samples)
            print(f"   ✓ {file_path}: {len(samples)} samples")

    print(f"\n   Total samples loaded: {len(all_samples)}")

    # Show distribution
    print("\n2. Category distribution BEFORE balancing:")
    categories = Counter(s.get('category') or s.get('label') for s in all_samples if s.get('category') or s.get('label'))
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {cat:30s}: {count}")

    # Balance
    print(f"\n3. Balancing to 600 samples per category...")
    balanced = balance_categories(all_samples, target_per_category=600)

    # Shuffle
    random.shuffle(balanced)

    # Split 80/20
    split = int(len(balanced) * 0.8)
    train = balanced[:split]
    test = balanced[split:]

    # Save
    print(f"\n4. Saving balanced dataset...")
    save_jsonl(train, "data/train.jsonl")
    save_jsonl(test, "data/test.jsonl")

    print("\n" + "=" * 70)
    print(f"✅ DONE!")
    print(f"   Train: {len(train)} samples → data/train.jsonl")
    print(f"   Test:  {len(test)} samples → data/test.jsonl")
    print("=" * 70)

    # Show final distribution
    print("\n5. Final category distribution (train):")
    final = Counter(s.get('category') or s.get('label') for s in train)
    for cat, count in sorted(final.items()):
        print(f"   {cat:30s}: {count}")

if __name__ == "__main__":
    main()
