#!/usr/bin/env python3
"""
Natural Language Augmentation Script
Adds lowercase, mixed-case, and natural language variations to training data
to fix the ML model's inability to handle real-world plain text inputs
"""

import json
import random
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

# Patterns to extract merchant names and strip metadata
MERCHANT_PATTERNS = [
    r'(?:UPI-|IMPS-|NEFT-)?([A-Z][A-Za-z]+)(?:-[A-Z]+)?',  # UPI-MERCHANT-XXX
    r'(?:POS PURCHASE |ONLINE ORDER |FOOD DELIVERY )?([A-Z][A-Za-z\s]+)',  # POS PURCHASE MERCHANT
    r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',  # Multi-word merchants
]

# Natural language templates for different categories
NATURAL_TEMPLATES = {
    'Food & Dining': [
        '{merchant}',
        '{merchant} coffee',
        '{merchant} food',
        '{merchant} lunch',
        '{merchant} dinner',
        '{merchant} breakfast',
        'coffee at {merchant}',
        'lunch at {merchant}',
        'dinner at {merchant}',
    ],
    'Shopping': [
        '{merchant}',
        '{merchant} shopping',
        '{merchant} order',
        'shopping at {merchant}',
        'order from {merchant}',
    ],
    'Entertainment': [
        '{merchant}',
        '{merchant} subscription',
        '{merchant} monthly',
        '{merchant} premium',
        'subscription to {merchant}',
    ],
    'Transport': [
        '{merchant}',
        '{merchant} ride',
        '{merchant} trip',
        'ride with {merchant}',
        'trip via {merchant}',
    ],
    'Travel': [
        '{merchant}',
        '{merchant} booking',
        '{merchant} hotel',
        '{merchant} flight',
    ],
    'Groceries': [
        '{merchant}',
        '{merchant} groceries',
        '{merchant} order',
        'groceries from {merchant}',
    ],
    'Health': [
        '{merchant}',
        '{merchant} medicines',
        '{merchant} checkup',
        'medicine from {merchant}',
    ],
}

def extract_merchant(text: str) -> str:
    """Extract merchant name from transaction text"""
    # Remove common prefixes
    text = re.sub(r'^(UPI-|IMPS-|NEFT-|RTGS-|POS PURCHASE |ONLINE ORDER |FOOD DELIVERY |DEBIT CARD )', '', text)

    # Extract first meaningful word(s)
    words = text.split()
    if not words:
        return text

    # Take first 1-2 words as merchant name
    merchant = ' '.join(words[:2]) if len(words) > 1 else words[0]

    # Clean up
    merchant = re.sub(r'[^A-Za-z\s]', '', merchant).strip()

    return merchant if merchant else text


def generate_natural_variations(text: str, category: str) -> List[str]:
    """Generate natural language variations of a transaction"""
    variations = []

    # Extract merchant name
    merchant = extract_merchant(text)
    if not merchant or len(merchant) < 3:
        return []

    # Get templates for this category
    templates = NATURAL_TEMPLATES.get(category, ['{merchant}'])

    # Generate variations
    for template in templates:
        variation = template.format(merchant=merchant)

        # Add different case variations
        variations.append(variation)  # Original case
        variations.append(variation.lower())  # lowercase
        variations.append(variation.title())  # Title Case

    return variations


def augment_dataset(input_path: str, output_path: str, augmentation_rate: float = 0.3):
    """
    Augment dataset with natural language variations

    Args:
        input_path: Path to original JSONL dataset
        output_path: Path to save augmented dataset
        augmentation_rate: Probability of adding natural variations for each transaction
    """
    print(f"Loading dataset from {input_path}...")

    original_data = []
    with open(input_path, 'r') as f:
        for line in f:
            original_data.append(json.loads(line.strip()))

    print(f"Loaded {len(original_data)} original samples")

    # Track statistics
    augmented_count = 0
    category_augmentations = defaultdict(int)

    # Create augmented dataset
    augmented_data = []

    for item in original_data:
        # Always include original
        augmented_data.append(item)

        text = item['text']
        category = item['label']

        # Skip if not a merchant transaction
        if category in ['Transfers/UPI', 'ATM/Cash', 'Fees & Charges', 'Income/Salary', 'Bills', 'Rent']:
            continue

        # Generate natural variations
        if random.random() < augmentation_rate:
            variations = generate_natural_variations(text, category)

            for variation in variations[:5]:  # Limit to 5 variations per transaction
                if variation.lower() != text.lower():  # Don't duplicate
                    augmented_item = {
                        'text': variation,
                        'label': category,
                        'amount': item.get('amount', 500.0),
                        'currency': item.get('currency', 'INR'),
                        'date': item.get('date', '2025-01-01')
                    }
                    augmented_data.append(augmented_item)
                    augmented_count += 1
                    category_augmentations[category] += 1

    print(f"\nAugmentation Statistics:")
    print(f"  Original samples: {len(original_data)}")
    print(f"  Augmented samples: {augmented_count}")
    print(f"  Total samples: {len(augmented_data)}")
    print(f"  Augmentation rate: {augmented_count / len(original_data):.2%}")

    print(f"\nAugmentations by category:")
    for category, count in sorted(category_augmentations.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count}")

    # Shuffle the data
    random.shuffle(augmented_data)

    # Save augmented dataset
    print(f"\nSaving augmented dataset to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        for item in augmented_data:
            f.write(json.dumps(item) + '\n')

    print(f"✓ Saved {len(augmented_data)} samples")

    # Show some examples
    print(f"\nExample augmentations:")
    for category in ['Food & Dining', 'Shopping', 'Entertainment']:
        print(f"\n{category}:")
        examples = [item for item in augmented_data if item['label'] == category]
        for item in random.sample(examples, min(3, len(examples))):
            print(f"  - {item['text']}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Augment dataset with natural language variations')
    parser.add_argument('--input', required=True, help='Input JSONL file')
    parser.add_argument('--output', required=True, help='Output JSONL file')
    parser.add_argument('--rate', type=float, default=0.5, help='Augmentation rate (0.0-1.0)')

    args = parser.parse_args()

    augment_dataset(args.input, args.output, args.rate)


if __name__ == '__main__':
    main()
