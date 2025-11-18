#!/usr/bin/env python3
"""
Process Balanced Kaggle Dataset
Maps well-balanced Kaggle transaction data to our category taxonomy
"""

import pandas as pd
import json
import random
from pathlib import Path
from collections import Counter

# Mapping from Kaggle categories to our taxonomy
CATEGORY_MAPPING = {
    'Restaurant': 'food_dining',
    'Market': 'groceries',
    'Travel': 'travel',
    'Electronics': 'electronics_technology',
    'Clothing': 'shopping',
    'Cosmetic': 'personal_care',
}

def process_credit_card_dataset():
    """Process the comprehensive credit card dataset"""
    print("=" * 70)
    print("📊 Processing Balanced Kaggle Credit Card Dataset")
    print("=" * 70)
    print()

    # Load dataset
    csv_file = "data/raw/credit_card_transaction_flow.csv"
    print(f"Loading: {csv_file}")

    df = pd.read_csv(csv_file)
    print(f"✓ Loaded {len(df):,} transactions")
    print()

    # Show original distribution
    print("Original category distribution:")
    orig_dist = df['Category'].value_counts()
    for cat, count in orig_dist.items():
        print(f"  {cat:20s}: {count:,}")
    print()

    # Map to our taxonomy
    mapped_data = []

    for _, row in df.iterrows():
        kaggle_cat = row['Category']
        our_cat = CATEGORY_MAPPING.get(kaggle_cat)

        if our_cat:
            sample = {
                'text': row['Merchant Name'],
                'label': our_cat,
                'amount': float(row['Transaction Amount']),
                'currency': 'USD'  # Credit card dataset
            }
            mapped_data.append(sample)

    print(f"Mapped {len(mapped_data):,} transactions to our taxonomy")
    print()

    # Show mapped distribution
    mapped_labels = [s['label'] for s in mapped_data]
    mapped_dist = Counter(mapped_labels)

    print("Mapped category distribution:")
    for cat, count in mapped_dist.items():
        print(f"  {cat:30s}: {count:,}")
    print()

    return mapped_data

def main():
    """Process balanced Kaggle data"""

    # Process credit card dataset
    kaggle_data = process_credit_card_dataset()

    # Shuffle
    random.seed(42)
    random.shuffle(kaggle_data)

    # Split 80/20
    split_idx = int(len(kaggle_data) * 0.8)
    train_data = kaggle_data[:split_idx]
    test_data = kaggle_data[split_idx:]

    # Save
    output_dir = Path("data/balanced_kaggle")
    output_dir.mkdir(exist_ok=True)

    train_file = output_dir / "train.jsonl"
    test_file = output_dir / "test.jsonl"

    with open(train_file, 'w') as f:
        for sample in train_data:
            f.write(json.dumps(sample) + '\n')

    with open(test_file, 'w') as f:
        for sample in test_data:
            f.write(json.dumps(sample) + '\n')

    print("=" * 70)
    print("📈 Summary")
    print("=" * 70)
    print(f"Total transactions:  {len(kaggle_data):,}")
    print(f"Training samples:    {len(train_data):,}")
    print(f"Test samples:        {len(test_data):,}")
    print()
    print(f"Saved to: {output_dir}")
    print("=" * 70)
    print()
    print("✅ Balanced Kaggle data processing complete!")
    print()
    print("🎯 Next Step:")
    print("   Run: python3 scripts/train.py")
    print("   (Automatically includes this balanced data!)")
    print()

if __name__ == '__main__':
    main()
