"""
Synthetic Dataset Generator
Generates realistic transaction data for training
"""

import json
import random
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import argparse


class SyntheticDataGenerator:
    """Generate synthetic transaction data"""

    def __init__(self, taxonomy_path: str, gazetteer_path: str):
        """
        Initialize generator

        Args:
            taxonomy_path: Path to taxonomy YAML
            gazetteer_path: Path to merchant gazetteer CSV
        """
        # Load taxonomy
        with open(taxonomy_path, 'r') as f:
            self.taxonomy = yaml.safe_load(f)

        # Load merchants
        self.merchants = {}
        with open(gazetteer_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                cat = row['category']
                if cat not in self.merchants:
                    self.merchants[cat] = []
                self.merchants[cat].append({
                    'canonical': row['canonical_name'],
                    'aliases': row['aliases'].split(','),
                    'subcategory': row.get('subcategory', '')
                })

        # Transaction templates by channel
        self.templates = {
            'UPI': [
                'UPI-{ref}-{merchant}',
                'UPI/{ref}/{merchant}',
                '{merchant}*UPI',
                '{merchant}-UPI',
                'UPI TO {merchant} REF {ref}',
                'UPI {merchant} {ref}',
            ],
            'IMPS': [
                'IMPS-{ref}-TO {merchant}',
                'IMPS/{merchant}/{ref}',
                'IMPS TO {merchant}',
                'IMPS {ref} {merchant}',
            ],
            'NEFT': [
                'NEFT-{ref}-TO {merchant}',
                'NEFT/{merchant}/{ref}',
                'NEFT TO {merchant}',
            ],
            'POS': [
                'POS {ref} {merchant} {city}',
                'POS/{merchant}/{city}',
                'POS {merchant} AT {city}',
            ],
            'ATM': [
                'ATM WDL {ref} {location}',
                'ATM WITHDRAWAL {ref}',
                'ATM/{ref}/{location}',
            ],
            'CARD': [
                'CARD {last4} AT {merchant}',
                'DEBIT CARD {merchant}',
                'CARD PURCHASE {merchant}',
            ],
        }

        # Amount ranges by category
        self.amount_ranges = {
            'food_dining': (50, 2000),
            'groceries': (200, 5000),
            'transport': (20, 500),
            'travel': (500, 50000),
            'fuel': (500, 3000),
            'utilities': (100, 5000),
            'rent': (5000, 50000),
            'shopping': (100, 10000),
            'entertainment': (50, 2000),
            'health': (100, 10000),
            'education': (1000, 100000),
            'fees_charges': (10, 500),
            'income_salary': (20000, 200000),
            'transfers_upi': (100, 50000),
            'atm_cash': (500, 20000),
            'investments': (1000, 100000),
            'bills': (500, 10000),
            'other': (10, 10000),
        }

        # Indian cities for location
        self.cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai',
            'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow',
            'Kanpur', 'Nagpur', 'Indore', 'Surat', 'Kochi'
        ]

    def generate_reference(self) -> str:
        """Generate random reference number"""
        return ''.join([str(random.randint(0, 9)) for _ in range(12)])

    def generate_last4(self) -> str:
        """Generate last 4 digits of card"""
        return ''.join([str(random.randint(0, 9)) for _ in range(4)])

    def add_noise(self, text: str) -> str:
        """Add realistic noise to transaction text"""
        # Randomly apply noise
        if random.random() < 0.3:  # 30% chance of noise

            choices = [
                lambda t: t.replace(' ', ''),  # Remove spaces
                lambda t: t.replace('-', '/'),  # Change delimiters
                lambda t: t.replace('/', '-'),
                lambda t: t.upper(),  # Uppercase
                lambda t: t.lower(),  # Lowercase
                lambda t: t.replace('  ', ' '),  # Extra spaces
                lambda t: f"{t}  ",  # Trailing spaces
            ]

            noise_fn = random.choice(choices)
            return noise_fn(text)

        return text

    def generate_transaction(self, category: Dict) -> Dict:
        """Generate a single synthetic transaction"""
        cat_id = category['id']
        cat_name = category['name']

        # Select merchant (if available for this category)
        merchant = None
        subcategory = None

        if cat_id in self.merchants and self.merchants[cat_id]:
            merchant_info = random.choice(self.merchants[cat_id])
            # Use alias with some randomness
            alias = random.choice(merchant_info['aliases']).strip()
            merchant = alias
            subcategory = merchant_info['subcategory']
        else:
            # Use keywords for categories without merchants
            if category.get('keywords'):
                merchant = random.choice(category['keywords'])

        # Select channel
        if cat_id == 'atm_cash':
            channel = 'ATM'
        elif cat_id == 'transfers_upi':
            channel = random.choice(['UPI', 'IMPS', 'NEFT'])
        elif cat_id == 'fuel':
            channel = random.choice(['POS', 'CARD'])
        else:
            channel = random.choice(['UPI', 'IMPS', 'POS', 'CARD'])

        # Generate amount
        amount_range = self.amount_ranges.get(cat_id, (100, 5000))
        amount = round(random.uniform(*amount_range), 2)

        # Generate date (last 6 months)
        days_ago = random.randint(0, 180)
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        # Generate transaction text
        template = random.choice(self.templates.get(channel, ['TRANSACTION {merchant}']))

        text = template.format(
            merchant=merchant or 'MERCHANT',
            ref=self.generate_reference(),
            last4=self.generate_last4(),
            city=random.choice(self.cities),
            location=random.choice(self.cities)
        )

        # Add noise
        text = self.add_noise(text)

        return {
            'text': text,
            'amount': amount,
            'date': date,
            'currency': 'INR',
            'label': cat_name,
            'category': cat_id,
            'subcategory': subcategory,
            'channel': channel
        }

    def generate_dataset(
        self,
        num_samples: int = 10000,
        output_path: str = 'data/datasets/synthetic_train.jsonl'
    ):
        """
        Generate synthetic dataset

        Args:
            num_samples: Number of samples to generate
            output_path: Output file path
        """
        categories = self.taxonomy['categories']

        # Calculate samples per category (roughly balanced)
        samples_per_category = num_samples // len(categories)

        transactions = []

        for category in categories:
            # Generate samples for this category
            for _ in range(samples_per_category):
                txn = self.generate_transaction(category)
                transactions.append(txn)

        # Generate a few more for popular categories
        popular_categories = ['food_dining', 'groceries', 'transport', 'shopping']
        for cat_id in popular_categories:
            cat = next(c for c in categories if c['id'] == cat_id)
            for _ in range(samples_per_category // 2):
                txn = self.generate_transaction(cat)
                transactions.append(txn)

        # Shuffle
        random.shuffle(transactions)

        # Save to JSONL
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            for txn in transactions:
                f.write(json.dumps(txn) + '\n')

        print(f"Generated {len(transactions)} transactions")
        print(f"Saved to: {output_path}")

        # Print statistics
        category_counts = {}
        for txn in transactions:
            cat = txn['label']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print("\nCategory distribution:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

        return transactions


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate synthetic transaction dataset')
    parser.add_argument('--num-samples', type=int, default=10000, help='Number of samples to generate')
    parser.add_argument('--output', type=str, default='data/datasets/synthetic_train.jsonl', help='Output file path')
    parser.add_argument('--taxonomy', type=str, default='data/taxonomy.yaml', help='Taxonomy file path')
    parser.add_argument('--gazetteer', type=str, default='data/gazetteer/merchant_aliases.csv', help='Gazetteer file path')

    args = parser.parse_args()

    # Initialize generator
    generator = SyntheticDataGenerator(
        taxonomy_path=args.taxonomy,
        gazetteer_path=args.gazetteer
    )

    # Generate dataset
    generator.generate_dataset(
        num_samples=args.num_samples,
        output_path=args.output
    )

    # Also generate validation and test sets
    print("\nGenerating validation set...")
    generator.generate_dataset(
        num_samples=args.num_samples // 5,  # 20% for validation
        output_path=args.output.replace('train', 'val')
    )

    print("\nGenerating test set...")
    generator.generate_dataset(
        num_samples=args.num_samples // 5,  # 20% for test
        output_path=args.output.replace('train', 'test')
    )


if __name__ == '__main__':
    main()
