#!/usr/bin/env python3
"""Merge improved weak category data with existing consolidated training data."""

import json
from collections import Counter

# Load existing consolidated data
print("Loading existing consolidated data...")
existing_train = []
existing_test = []

with open('data/balanced/train_consolidated.jsonl', 'r') as f:
    for line in f:
        existing_train.append(json.loads(line))

with open('data/balanced/test_consolidated.jsonl', 'r') as f:
    for line in f:
        existing_test.append(json.loads(line))

print(f"Existing training samples: {len(existing_train)}")
print(f"Existing test samples: {len(existing_test)}")

# Categories to replace
weak_categories = [
    'home_improvement',
    'pets',
    'kids_family',
    'electronics_technology',
    'subscriptions_memberships'
]

# Remove old weak category data from existing datasets
print("\nRemoving old weak category data...")
filtered_train = [d for d in existing_train if d['category'] not in weak_categories]
filtered_test = [d for d in existing_test if d['category'] not in weak_categories]

print(f"Filtered training samples: {len(filtered_train)}")
print(f"Filtered test samples: {len(filtered_test)}")

# Load new improved data for weak categories
print("\nLoading improved weak category data...")
new_train = []
new_test = []

for category in weak_categories:
    train_file = f'data/improved_weak_categories/{category}_train.jsonl'
    test_file = f'data/improved_weak_categories/{category}_test.jsonl'

    with open(train_file, 'r') as f:
        category_train = [json.loads(line) for line in f]
        new_train.extend(category_train)
        print(f"  {category}: {len(category_train)} train samples")

    with open(test_file, 'r') as f:
        category_test = [json.loads(line) for line in f]
        new_test.extend(category_test)
        print(f"  {category}: {len(category_test)} test samples")

# Merge data
merged_train = filtered_train + new_train
merged_test = filtered_test + new_test

print(f"\nMerged training samples: {len(merged_train)}")
print(f"Merged test samples: {len(merged_test)}")

# Show category distribution
print("\nCategory distribution (training):")
train_counts = Counter(d['category'] for d in merged_train)
for category, count in sorted(train_counts.items()):
    print(f"  {category}: {count}")

# Save merged data
print("\nSaving merged data...")
with open('data/balanced/train_consolidated_improved.jsonl', 'w') as f:
    for item in merged_train:
        f.write(json.dumps(item) + '\n')

with open('data/balanced/test_consolidated_improved.jsonl', 'w') as f:
    for item in merged_test:
        f.write(json.dumps(item) + '\n')

print("\n" + "="*80)
print("DATA MERGE COMPLETE!")
print("="*80)
print(f"New training file: data/balanced/train_consolidated_improved.jsonl ({len(merged_train)} samples)")
print(f"New test file: data/balanced/test_consolidated_improved.jsonl ({len(merged_test)} samples)")
