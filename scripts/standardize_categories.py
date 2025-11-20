#!/usr/bin/env python3
"""
Standardize all category names to use taxonomy IDs consistently
Fixes discrepancies between name formats (e.g., "Income/Salary" vs "income_salary")
"""

import json
import yaml
from pathlib import Path
from collections import Counter

def load_taxonomy():
    """Load taxonomy and create mapping from names to IDs"""
    with open('data/taxonomy.yaml', 'r') as f:
        taxonomy = yaml.safe_load(f)

    # Create mapping: both name and ID should map to ID
    name_to_id = {}
    for cat in taxonomy['categories']:
        cat_id = cat['id']
        cat_name = cat['name']

        # Map both name and ID to the canonical ID
        name_to_id[cat_name] = cat_id
        name_to_id[cat_name.lower()] = cat_id
        name_to_id[cat_id] = cat_id

        # Handle common variations
        name_to_id[cat_name.replace(' & ', '_').replace(' ', '_').lower()] = cat_id
        name_to_id[cat_name.replace('/', '_').replace(' ', '_').lower()] = cat_id

    return name_to_id, taxonomy

def standardize_file(input_path, output_path, name_to_id):
    """Standardize categories in a JSONL file"""
    if not Path(input_path).exists():
        print(f"⚠️  Skipping {input_path} (does not exist)")
        return 0, Counter()

    data = []
    changes = Counter()

    with open(input_path, 'r') as f:
        for line in f:
            item = json.loads(line.strip())

            # Get current category (could be in 'label' or 'category')
            current = item.get('label', item.get('category', ''))

            # Map to standardized ID
            standardized = name_to_id.get(current, name_to_id.get(current.lower(), current))

            # Track changes
            if current != standardized:
                changes[f"{current} → {standardized}"] += 1

            # Update both fields to use standardized ID
            item['label'] = standardized
            item['category'] = standardized

            data.append(item)

    # Write standardized data
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

    return len(data), changes

def main():
    print("=" * 70)
    print("STANDARDIZING CATEGORY NAMES TO TAXONOMY IDs")
    print("=" * 70)
    print()

    # Load taxonomy
    name_to_id, taxonomy = load_taxonomy()

    print(f"✓ Loaded taxonomy with {len(taxonomy['categories'])} categories")
    print()

    # Files to standardize
    files_to_process = [
        ('data/balanced/train_consolidated.jsonl', 'data/balanced/train_consolidated_std.jsonl'),
        ('data/balanced/test_consolidated.jsonl', 'data/balanced/test_consolidated_std.jsonl'),
        ('data/balanced/train_merged_all.jsonl', 'data/balanced/train_merged_all_std.jsonl'),
        ('data/balanced/test_merged_all.jsonl', 'data/balanced/test_merged_all_std.jsonl'),
        ('data/balanced/train.jsonl', 'data/balanced/train_std.jsonl'),
        ('data/balanced/test.jsonl', 'data/balanced/test_std.jsonl'),
        ('data/synthetic_new_categories/train_consolidated.jsonl', 'data/synthetic_new_categories/train_consolidated_std.jsonl'),
        ('data/synthetic_new_categories/val.jsonl', 'data/synthetic_new_categories/val_std.jsonl'),
        ('data/improved_weak_categories/train_consolidated.jsonl', 'data/improved_weak_categories/train_consolidated_std.jsonl'),
        ('data/improved_weak_categories/test_consolidated.jsonl', 'data/improved_weak_categories/test_consolidated_std.jsonl'),
        ('data/kaggle_new_categories/extracted_transactions.jsonl', 'data/kaggle_new_categories/extracted_transactions_std.jsonl'),
    ]

    total_changes = Counter()

    for input_path, output_path in files_to_process:
        print(f"Processing: {input_path}")
        count, changes = standardize_file(input_path, output_path, name_to_id)

        if count > 0:
            print(f"  ✓ Standardized {count} samples")
            if changes:
                print(f"  📝 Category changes:")
                for change, cnt in changes.most_common(10):
                    print(f"     {change}: {cnt} samples")
                total_changes.update(changes)
            print()
        else:
            print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if total_changes:
        print(f"\n📊 Total category mappings applied:")
        for change, cnt in total_changes.most_common():
            print(f"  {change}: {cnt} samples")
    else:
        print("\n✓ All categories were already standardized")

    print("\n" + "=" * 70)
    print("✅ STANDARDIZATION COMPLETE")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("  1. Update train.py to use *_std.jsonl files")
    print("  2. Retrain model with standardized data")
    print("  3. All category names will now use taxonomy IDs consistently")
    print()

if __name__ == "__main__":
    main()
