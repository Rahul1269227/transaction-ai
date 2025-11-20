#!/usr/bin/env python3
"""
Generate synthetic training data for weak categories
to achieve >90% macro F1 score
"""

import json
import random
import yaml
from pathlib import Path
from datetime import datetime, timedelta

# Weak categories that need more data (from F1 evaluation)
WEAK_CATEGORIES = [
    'personal_care',
    'subscriptions_memberships',
    'charity_donations',
    'home_improvement',
    'gifts_occasions',
    'electronics_technology',
    'taxes_government',
    'automotive',
    'insurance',
    'kids_family',
    'pets'
]

TARGET_SAMPLES_PER_CATEGORY = 500

def load_taxonomy():
    """Load taxonomy to get category details"""
    with open('data/taxonomy.yaml', 'r') as f:
        return yaml.safe_load(f)

def generate_random_date():
    """Generate random date in last 2 years"""
    start = datetime.now() - timedelta(days=730)
    random_days = random.randint(0, 730)
    return (start + timedelta(days=random_days)).strftime('%Y-%m-%d')

def generate_amount(category_id):
    """Generate realistic amount for category"""
    amount_ranges = {
        'personal_care': (200, 5000),
        'subscriptions_memberships': (99, 999),
        'charity_donations': (100, 10000),
        'home_improvement': (1000, 100000),
        'gifts_occasions': (500, 5000),
        'electronics_technology': (5000, 150000),
        'taxes_government': (1000, 100000),
        'automotive': (500, 25000),
        'insurance': (2000, 25000),
        'kids_family': (500, 15000),
        'pets': (300, 5000)
    }

    min_amt, max_amt = amount_ranges.get(category_id, (100, 10000))
    return round(random.uniform(min_amt, max_amt), 2)

def generate_samples_for_category(category_id, category_info, num_samples):
    """Generate synthetic samples for a category"""
    samples = []
    keywords = category_info.get('keywords', [])

    if not keywords:
        return samples

    templates = {
        'personal_care': [
            "{merchant} salon",
            "{merchant} spa",
            "{merchant} gym membership",
            "Haircut at {merchant}",
            "{merchant} beauty salon",
            "Spa treatment {merchant}",
            "Gym membership {merchant}",
            "{merchant} fitness center",
            "Yoga class {merchant}",
            "{merchant} wellness center"
        ],
        'subscriptions_memberships': [
            "{merchant} subscription",
            "{merchant} monthly plan",
            "{merchant} premium",
            "{merchant} membership renewal",
            "Monthly {merchant} subscription",
            "{merchant} annual membership",
            "{merchant} plan renewal",
            "Recurring {merchant} payment",
            "{merchant} pro subscription",
            "{merchant} premium plan"
        ],
        'charity_donations': [
            "Donation to {merchant}",
            "{merchant} contribution",
            "Charity payment {merchant}",
            "{merchant} donation",
            "Contribution to {merchant}",
            "{merchant} relief fund",
            "Donation {merchant}",
            "{merchant} charity",
            "Supporting {merchant}",
            "{merchant} NGO donation"
        ],
        'home_improvement': [
            "{merchant} furniture",
            "Purchased {merchant}",
            "{merchant} home repair",
            "Plumber service {merchant}",
            "{merchant} electrician",
            "Furniture from {merchant}",
            "{merchant} appliance",
            "Home renovation {merchant}",
            "{merchant} interior work",
            "Repair service {merchant}"
        ],
        'gifts_occasions': [
            "Gift from {merchant}",
            "{merchant} flowers",
            "Birthday gift {merchant}",
            "{merchant} gift delivery",
            "Anniversary gift {merchant}",
            "{merchant} bouquet",
            "Gift purchase {merchant}",
            "{merchant} celebration",
            "Party supplies {merchant}",
            "{merchant} gift card"
        ],
        'electronics_technology': [
            "{merchant} mobile",
            "Purchased {merchant} laptop",
            "{merchant} electronics",
            "Smartphone from {merchant}",
            "{merchant} gadget",
            "Laptop purchase {merchant}",
            "{merchant} computer",
            "Electronics {merchant}",
            "{merchant} tech purchase",
            "Gadget from {merchant}"
        ],
        'taxes_government': [
            "Income tax payment",
            "Property tax {merchant}",
            "Tax payment {merchant}",
            "GST payment",
            "{merchant} government fee",
            "License fee {merchant}",
            "Tax challan payment",
            "{merchant} fine",
            "Government fee {merchant}",
            "{merchant} tax payment"
        ],
        'automotive': [
            "{merchant} car service",
            "Vehicle maintenance {merchant}",
            "{merchant} car wash",
            "Auto repair {merchant}",
            "{merchant} bike service",
            "Car service {merchant}",
            "{merchant} tire change",
            "Vehicle service {merchant}",
            "{merchant} oil change",
            "Car wash {merchant}"
        ],
        'insurance': [
            "{merchant} insurance premium",
            "Policy payment {merchant}",
            "{merchant} life insurance",
            "Health insurance {merchant}",
            "{merchant} premium",
            "Insurance renewal {merchant}",
            "{merchant} policy",
            "Premium payment {merchant}",
            "{merchant} insurance",
            "Policy premium {merchant}"
        ],
        'kids_family': [
            "{merchant} kids",
            "Daycare {merchant}",
            "{merchant} toys",
            "Kids products {merchant}",
            "{merchant} baby products",
            "Childcare {merchant}",
            "{merchant} kids education",
            "Toys from {merchant}",
            "{merchant} baby care",
            "Kids activity {merchant}"
        ],
        'pets': [
            "{merchant} pet food",
            "Veterinary {merchant}",
            "{merchant} pet supplies",
            "Pet food from {merchant}",
            "{merchant} vet visit",
            "Pet supplies {merchant}",
            "{merchant} pet care",
            "Vet appointment {merchant}",
            "{merchant} dog food",
            "Pet grooming {merchant}"
        ]
    }

    category_templates = templates.get(category_id, ["{merchant}"])

    for _ in range(num_samples):
        # Pick random keyword as merchant
        merchant = random.choice(keywords).title()

        # Pick random template
        template = random.choice(category_templates)

        # Generate transaction
        text = template.format(merchant=merchant)

        # Add variation
        if random.random() < 0.3:
            text = text.upper()
        elif random.random() < 0.3:
            text = text.lower()

        sample = {
            'text': text,
            'label': category_id,
            'category': category_id,
            'amount': generate_amount(category_id),
            'currency': 'INR',
            'date': generate_random_date()
        }

        samples.append(sample)

    return samples

def main():
    print("=" * 70)
    print("GENERATING SYNTHETIC DATA FOR WEAK CATEGORIES")
    print("=" * 70)
    print()

    # Load taxonomy
    taxonomy = load_taxonomy()
    categories_by_id = {cat['id']: cat for cat in taxonomy['categories']}

    all_samples = []

    for category_id in WEAK_CATEGORIES:
        if category_id not in categories_by_id:
            print(f"⚠️  Category '{category_id}' not found in taxonomy, skipping")
            continue

        category_info = categories_by_id[category_id]
        print(f"Generating {TARGET_SAMPLES_PER_CATEGORY} samples for: {category_info['name']}")

        samples = generate_samples_for_category(
            category_id,
            category_info,
            TARGET_SAMPLES_PER_CATEGORY
        )

        all_samples.extend(samples)
        print(f"  ✓ Generated {len(samples)} samples")

    # Shuffle
    random.shuffle(all_samples)

    # Split 80/20
    split_idx = int(len(all_samples) * 0.8)
    train_samples = all_samples[:split_idx]
    test_samples = all_samples[split_idx:]

    # Save
    output_dir = Path("data/synthetic_weak_categories")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.jsonl"
    test_path = output_dir / "test.jsonl"

    with open(train_path, 'w') as f:
        for sample in train_samples:
            f.write(json.dumps(sample) + '\n')

    with open(test_path, 'w') as f:
        for sample in test_samples:
            f.write(json.dumps(sample) + '\n')

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total samples generated: {len(all_samples)}")
    print(f"  Training: {len(train_samples)}")
    print(f"  Test: {len(test_samples)}")
    print()
    print(f"✓ Saved to: {output_dir}")
    print(f"  - {train_path}")
    print(f"  - {test_path}")
    print()
    print("=" * 70)
    print("✅ SYNTHETIC DATA GENERATION COMPLETE")
    print("=" * 70)
    print("\n📝 Next: Update train.py to include these new synthetic samples")

if __name__ == "__main__":
    main()
