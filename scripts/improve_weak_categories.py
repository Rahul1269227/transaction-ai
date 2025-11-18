#!/usr/bin/env python3
"""
Improve Weak Categories
Generates more diverse, realistic training data for underperforming categories
"""

import json
import random
from pathlib import Path
import yaml

# Categories that need improvement
WEAK_CATEGORIES = {
    'personal_care': {
        'target_samples': 500,
        'merchants': [
            'Urban Company', 'Lakme Salon', 'VLCC', 'Naturals Salon', 'Jawed Habib',
            'Cult.fit', 'Gold\'s Gym', 'Anytime Fitness', 'Talwalkars', 'Snap Fitness',
            'O2 Spa', 'Tattva Spa', 'Four Fountains', 'Enrich Salon', 'Green Trends',
            'YLG Salon', 'Looks Salon', 'Bodycraft Spa', 'Kaya Clinic', 'Shahnaz Husain',
            'Geetanjali Salon', 'Tony & Guy', 'Toni&Guy', 'Affinity Salon', 'Jean Claude'
        ],
        'services': [
            'Haircut', 'Hair Color', 'Facial', 'Massage', 'Spa', 'Manicure', 'Pedicure',
            'Hair Spa', 'Waxing', 'Threading', 'Gym Membership', 'Personal Training',
            'Yoga Class', 'Zumba', 'Salon Service', 'Beauty Treatment', 'Hair Treatment',
            'Skin Treatment', 'Fitness', 'Wellness'
        ],
        'amount_range': (300, 5000)
    },
    'insurance': {
        'target_samples': 500,
        'merchants': [
            'LIC', 'HDFC Life', 'ICICI Prudential', 'SBI Life', 'Max Life', 'Bajaj Allianz',
            'Star Health', 'TATA AIG', 'Reliance Life', 'Kotak Life', 'Aditya Birla',
            'Future Generali', 'Aegon Life', 'PNB MetLife', 'Canara HSBC', 'IndiaFirst Life',
            'Edelweiss Tokio', 'DHFL Pramerica', 'Exide Life', 'Aviva Life', 'Shriram Life',
            'National Insurance', 'New India Assurance', 'Oriental Insurance', 'United India'
        ],
        'policies': [
            'Premium', 'Policy Payment', 'Insurance Premium', 'Life Insurance', 'Health Insurance',
            'Term Insurance', 'Vehicle Insurance', 'Car Insurance', 'Bike Insurance',
            'Home Insurance', 'Travel Insurance', 'Policy Renewal', 'Annual Premium',
            'Monthly Premium', 'Quarterly Premium'
        ],
        'amount_range': (2000, 50000)
    },
    'gifts_occasions': {
        'target_samples': 500,
        'merchants': [
            'Ferns N Petals', 'FNP', 'Archies', 'IGP', 'FlowerAura', 'MyFlowerTree',
            'Interflora', 'GiftstoIndia24x7', 'Amazon Gift', 'Flipkart Gift', 'BookMyFlowers',
            'Phoolwala', 'Flowerz.in', 'A1 Flowers', 'Gift Shop', 'Hallmark',
            'Carlton Cards', 'Spencer\'s Gifts', 'Shoppers Stop Gift', 'Lifestyle Gift'
        ],
        'items': [
            'Flowers', 'Bouquet', 'Cake', 'Gift', 'Birthday Gift', 'Anniversary Gift',
            'Chocolate Box', 'Gift Hamper', 'Personalized Gift', 'Gift Card',
            'Greeting Card', 'Teddy Bear', 'Photo Frame', 'Gift Voucher', 'Roses',
            'Mixed Flowers', 'Gift Basket', 'Special Occasion', 'Celebration', 'Present'
        ],
        'amount_range': (500, 10000)
    },
    'charity_donations': {
        'target_samples': 500,
        'organizations': [
            'Red Cross', 'UNICEF', 'Oxfam', 'CRY', 'Akshaya Patra', 'Goonj', 'Helpage India',
            'Smile Foundation', 'Give India', 'Ketto', 'Milaap', 'Teach For India',
            'Magic Bus', 'Pratham', 'Asha', 'Nanhi Kali', 'Save the Children',
            'HelpAge', 'Being Human', 'Temple', 'Church', 'Mosque', 'Gurudwara',
            'PM Cares', 'CM Relief Fund', 'Charity', 'NGO', 'Foundation'
        ],
        'purposes': [
            'Donation', 'Charity', 'Relief Fund', 'Crowdfunding', 'Support',
            'Contribution', 'Aid', 'Help', 'Zakat', 'Sadaqah', 'Daan',
            'Temple Donation', 'Church Offering', 'Religious Donation',
            'COVID Relief', 'Flood Relief', 'Education Support', 'Medical Aid'
        ],
        'amount_range': (100, 10000)
    }
}

def generate_realistic_transaction(category, config):
    """Generate a realistic transaction for a category"""

    if category == 'personal_care':
        merchant = random.choice(config['merchants'])
        service = random.choice(config['services'])

        patterns = [
            f"{merchant} {service}",
            f"{service} - {merchant}",
            f"{merchant}",
            f"Payment to {merchant}",
            f"{merchant} - {service} Service",
            f"UPI - {merchant}",
            f"NEFT {merchant}",
            f"{service} at {merchant}",
            f"{merchant.upper()} {service.upper()}",
        ]

    elif category == 'insurance':
        merchant = random.choice(config['merchants'])
        policy = random.choice(config['policies'])

        patterns = [
            f"{merchant} Insurance {policy}",
            f"{merchant} {policy}",
            f"{policy} - {merchant}",
            f"{merchant} Premium Payment",
            f"Payment to {merchant}",
            f"{merchant.upper()} INSURANCE",
            f"{policy} {merchant}",
            f"NEFT - {merchant} Insurance",
            f"{merchant} Policy Premium",
        ]

    elif category == 'gifts_occasions':
        merchant = random.choice(config['merchants'])
        item = random.choice(config['items'])

        patterns = [
            f"{merchant} {item}",
            f"{item} from {merchant}",
            f"{merchant}",
            f"Order - {merchant}",
            f"{item} - {merchant}",
            f"{merchant.upper()} {item.upper()}",
            f"Payment to {merchant}",
            f"{item} Purchase",
            f"{merchant} - {item} Order",
        ]

    elif category == 'charity_donations':
        org = random.choice(config['organizations'])
        purpose = random.choice(config['purposes'])

        patterns = [
            f"{purpose} to {org}",
            f"{org} {purpose}",
            f"{purpose} - {org}",
            f"Payment to {org}",
            f"{org.upper()} DONATION",
            f"{purpose}",
            f"{org}",
            f"NEFT - {org}",
            f"UPI {org} {purpose}",
        ]

    text = random.choice(patterns)
    min_amt, max_amt = config['amount_range']
    amount = round(random.uniform(min_amt, max_amt), 2)

    return {
        'text': text,
        'label': category,
        'amount': amount,
        'currency': 'INR'
    }

def main():
    """Generate improved training data for weak categories"""
    print("=" * 70)
    print("📈 Generating Enhanced Data for Weak Categories")
    print("=" * 70)
    print()

    all_samples = []

    for category, config in WEAK_CATEGORIES.items():
        print(f"Generating {config['target_samples']} samples for: {category}")

        samples = []
        for _ in range(config['target_samples']):
            sample = generate_realistic_transaction(category, config)
            samples.append(sample)

        all_samples.extend(samples)
        print(f"  ✓ Generated {len(samples)} samples")

    # Shuffle
    random.seed(42)
    random.shuffle(all_samples)

    # Split 80/20
    split_idx = int(len(all_samples) * 0.8)
    train_samples = all_samples[:split_idx]
    test_samples = all_samples[split_idx:]

    # Save
    output_dir = Path("data/improved_weak_categories")
    output_dir.mkdir(exist_ok=True)

    train_file = output_dir / "train.jsonl"
    test_file = output_dir / "test.jsonl"

    with open(train_file, 'w') as f:
        for sample in train_samples:
            f.write(json.dumps(sample) + '\n')

    with open(test_file, 'w') as f:
        for sample in test_samples:
            f.write(json.dumps(sample) + '\n')

    print()
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   Total samples:      {len(all_samples):,}")
    print(f"   Training samples:   {len(train_samples):,}")
    print(f"   Test samples:       {len(test_samples):,}")
    print()
    print(f"   Saved to: {output_dir}")
    print("=" * 70)
    print()
    print("✅ Enhanced data generation complete!")
    print()
    print("🎯 Next Steps:")
    print("   Run: python3 scripts/train.py")
    print("   This will automatically include the new improved data!")
    print()

if __name__ == '__main__':
    main()
