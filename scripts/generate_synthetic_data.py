"""
Generate Synthetic Training Data for New Categories
Creates synthetic transaction data based on taxonomy keywords
"""

import json
import random
import yaml
from pathlib import Path
from typing import List, Dict
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# New categories we added
NEW_CATEGORIES = [
    "insurance",
    "charity_donations",
    "personal_care",
    "pets",
    "home_improvement",
    "automotive",
    "taxes_government",
    "electronics_technology",
    "professional_services",
    "kids_family",
    "subscriptions_memberships",
    "gifts_occasions"
]

def load_taxonomy():
    """Load taxonomy from YAML"""
    taxonomy_path = Path(__file__).parent.parent / "data" / "taxonomy.yaml"
    with open(taxonomy_path, 'r') as f:
        return yaml.safe_load(f)

def generate_synthetic_transactions(category_info: Dict, num_samples: int = 150) -> List[Dict]:
    """
    Generate synthetic transactions for a category

    Args:
        category_info: Category information from taxonomy
        num_samples: Number of samples to generate

    Returns:
        List of synthetic transaction samples
    """
    samples = []
    keywords = category_info.get('keywords', [])
    subcategories = category_info.get('subcategories', [])
    mcc_codes = category_info.get('mcc_codes', [])

    # Amount ranges based on category
    amount_ranges = {
        'insurance': (5000, 50000),
        'charity_donations': (100, 10000),
        'personal_care': (500, 5000),
        'pets': (200, 5000),
        'home_improvement': (2000, 100000),
        'automotive': (1000, 20000),
        'taxes_government': (1000, 50000),
        'electronics_technology': (5000, 100000),
        'professional_services': (5000, 50000),
        'kids_family': (500, 10000),
        'subscriptions_memberships': (99, 2000),
        'gifts_occasions': (500, 10000)
    }

    category_id = category_info['id']
    min_amt, max_amt = amount_ranges.get(category_id, (100, 10000))

    # Generate variations
    for i in range(num_samples):
        keyword = random.choice(keywords) if keywords else category_info['name']

        # Create realistic transaction text patterns
        patterns = [
            f"{keyword}",
            f"Payment to {keyword}",
            f"{keyword.upper()}",
            f"{keyword} - Payment",
            f"NEFT - {keyword}",
            f"UPI - {keyword}",
            f"{keyword} India",
            f"{keyword} Services",
            f"Online {keyword}",
            f"{keyword} Purchase",
        ]

        # Add subcategory variations
        if subcategories:
            subcat = random.choice(subcategories)
            patterns.extend([
                f"{subcat}",
                f"{keyword} {subcat}",
                f"{subcat} - {keyword}",
            ])

        text = random.choice(patterns)
        amount = round(random.uniform(min_amt, max_amt), 2)

        # Add some noise/variations
        if random.random() < 0.2:
            text = text.upper()
        elif random.random() < 0.2:
            text = text.lower()

        if random.random() < 0.3:
            # Add transaction ID
            text += f" TXN{random.randint(100000, 999999)}"

        if random.random() < 0.2:
            # Add date-like suffix
            text += f" {random.randint(1, 28)}/{random.randint(1, 12)}"

        sample = {
            'text': text,
            'label': category_id,
            'amount': amount,
            'currency': 'INR'
        }

        samples.append(sample)

    return samples

def main():
    """Generate synthetic data for new categories"""
    print("Loading taxonomy...")
    taxonomy = load_taxonomy()

    # Find new categories
    all_samples = []

    for category in taxonomy['categories']:
        category_id = category['id']

        if category_id in NEW_CATEGORIES:
            print(f"\nGenerating data for: {category['name']} ({category_id})")
            samples = generate_synthetic_transactions(category, num_samples=150)
            all_samples.extend(samples)
            print(f"  Generated {len(samples)} samples")

    # Split into train (80%) and validation (20%)
    random.shuffle(all_samples)
    split_idx = int(len(all_samples) * 0.8)
    train_samples = all_samples[:split_idx]
    val_samples = all_samples[split_idx:]

    print(f"\n=== Summary ===")
    print(f"Total samples: {len(all_samples)}")
    print(f"Training samples: {len(train_samples)}")
    print(f"Validation samples: {len(val_samples)}")

    # Save to files
    output_dir = Path(__file__).parent.parent / "data" / "synthetic_new_categories"
    output_dir.mkdir(exist_ok=True)

    train_file = output_dir / "train.jsonl"
    val_file = output_dir / "val.jsonl"

    print(f"\nSaving to:")
    print(f"  Train: {train_file}")
    print(f"  Val: {val_file}")

    with open(train_file, 'w') as f:
        for sample in train_samples:
            f.write(json.dumps(sample) + '\n')

    with open(val_file, 'w') as f:
        for sample in val_samples:
            f.write(json.dumps(sample) + '\n')

    print("\n✅ Synthetic data generation complete!")

    # Show distribution
    from collections import Counter
    train_dist = Counter([s['label'] for s in train_samples])
    print("\n=== Training Distribution ===")
    for cat, count in sorted(train_dist.items()):
        print(f"  {cat}: {count}")

if __name__ == '__main__':
    main()
