#!/usr/bin/env python3
"""
Prepare combined dataset from real Kaggle data and synthetic data
"""

import pandas as pd
import json
import yaml
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

def load_taxonomy():
    """Load taxonomy"""
    with open('data/taxonomy.yaml', 'r') as f:
        return yaml.safe_load(f)

def generate_synthetic_transactions(taxonomy: Dict, n_samples: int = 5000) -> List[Dict]:
    """
    Generate synthetic transactions based on taxonomy
    """
    synthetic = []

    # Get categories (exclude 'Other')
    categories = [cat for cat in taxonomy['categories'] if cat['name'] != 'Other']

    # Templates for each category
    templates = {
        'Food & Dining': [
            'UPI-{merchant}-{amount}',
            'POS PURCHASE {merchant}',
            '{merchant} ONLINE ORDER',
            'SWIGGY {merchant}',
            'ZOMATO {merchant}',
        ],
        'Groceries': [
            'BIGBASKET PURCHASE',
            'DMART {merchant}',
            'BLINKIT ORDER',
            'ZEPTO {merchant}',
            'JIOMART PURCHASE',
        ],
        'Transport': [
            'UPI-UBER-{amount}',
            'UPI-OLA-{amount}',
            'RAPIDO RIDE',
            'METRO CARD RECHARGE',
            'FASTAG DEDUCTION',
        ],
        'Travel': [
            'IRCTC TICKET BOOKING',
            'MAKEMYTRIP FLIGHT',
            'OYO HOTELS',
            'GOIBIBO BOOKING',
            'INDIGO AIRLINES',
        ],
        'Utilities': [
            'BSES RAJDHANI POWER LIMIT',
            'AIRTEL BROADBAND',
            'JIO MOBILE RECHARGE',
            'TATA SKY DTH RECHARGE',
            'INDANE GAS CYLINDER',
        ],
        'Shopping': [
            'AMAZON PAY',
            'FLIPKART ORDER',
            'MYNTRA FASHION',
            'NYKAA PURCHASE',
            'AJIO SHOPPING',
        ],
        'Entertainment': [
            'NETFLIX SUBSCRIPTION',
            'PRIME VIDEO SUBSCRIPTION',
            'PVR CINEMA',
            'BOOKMYSHOW TICKET',
            'SPOTIFY PREMIUM',
        ],
        'Health': [
            'APOLLO PHARMACY',
            '1MG MEDICINE ORDER',
            'PHARMEASY PURCHASE',
            'MAX HOSPITAL',
            'FORTIS HEALTHCARE',
        ],
        'ATM/Cash': [
            'CASHDEP/{city}/',
            'ATM WDL {bank}',
            'CASH WITHDRAWAL',
            'POS CASH BACK',
        ],
        'Transfers/UPI': [
            'FDRL/INTERNAL FUND TRANSFE',
            'FDRL/NATIONAL ELECTRONIC F',
            'UPI-P2P-{name}',
            'IMPS TRANSFER',
            'NEFT TO {name}',
        ],
        'Investments': [
            'ZERODHA KITE',
            'GROWW MUTUAL FUND',
            'UPSTOX TRADING',
            'SIP INVESTMENT',
            'HDFC LIFE INSURANCE',
        ],
        'Bills': [
            'BILL PAYMENT ELECTRICITY',
            'WATER BILL PAYMENT',
            'CREDIT CARD BILL',
            'LOAN EMI DEDUCTION',
            'MAINTENANCE CHARGES',
        ],
        'Fees & Charges': [
            'BANK SERVICE CHARGE',
            'TRANSACTION FEE',
            'ANNUAL FEE DEBIT',
            'GST CHARGES',
            'PROCESSING FEE',
        ],
        'Income/Salary': [
            'SALARY CREDIT',
            'BONUS CREDIT',
            'REFUND FROM {merchant}',
            'CASHBACK CREDIT',
            'INTEREST CREDIT',
        ],
    }

    # Merchants
    merchants = {
        'Food & Dining': ['DOMINOS', 'KFC', 'MCDONALDS', 'STARBUCKS', 'HALDIRAMS', 'CAFE COFFEE DAY'],
        'Groceries': ['MORE', 'RELIANCE FRESH', 'SPENCERS', 'NATURE BASKET'],
        'default': ['PAYTM', 'PHONEPE', 'GOOGLEPAY']
    }

    # Generate samples
    for _ in range(n_samples):
        # Pick random category
        category = random.choice(categories)
        cat_name = category['name']

        # Get template for category
        if cat_name in templates:
            template = random.choice(templates[cat_name])
            merchant_list = merchants.get(cat_name, merchants['default'])
            merchant = random.choice(merchant_list)

            # Replace placeholders
            text = template.replace('{merchant}', merchant)
            text = text.replace('{amount}', f"{random.randint(100, 5000)}")
            text = text.replace('{city}', random.choice(['DELHI', 'MUMBAI', 'BANGALORE', 'CHENNAI']))
            text = text.replace('{bank}', random.choice(['HDFC', 'ICICI', 'SBI', 'AXIS']))
            text = text.replace('{name}', random.choice(['RAHUL', 'AMIT', 'PRIYA', 'NEHA']))

            # Generate transaction
            synthetic.append({
                'text': text,
                'label': cat_name,
                'amount': random.randint(50, 10000),
                'currency': 'INR',
                'date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
            })

    return synthetic

def convert_real_to_jsonl(df: pd.DataFrame, output_path: str):
    """
    Convert real transaction data from CSV to JSONL format
    """
    with open(output_path, 'w') as f:
        for _, row in df.iterrows():
            # Skip if no transaction details
            if pd.isna(row['TRANSACTION DETAILS']):
                continue

            # Determine amount (withdrawal or deposit)
            amount = None
            if pd.notna(row['WITHDRAWAL AMT']):
                amount = -float(row['WITHDRAWAL AMT'])
            elif pd.notna(row['DEPOSIT AMT']):
                amount = float(row['DEPOSIT AMT'])

            record = {
                'text': str(row['TRANSACTION DETAILS']),
                'label': str(row['category']),
                'amount': amount,
                'currency': 'INR',
                'date': str(row['DATE'])[:10] if pd.notna(row['DATE']) else None
            }

            f.write(json.dumps(record) + '\n')

def main():
    print("Preparing combined dataset...")

    # Load taxonomy
    taxonomy = load_taxonomy()

    # 1. Load real data
    print("\n1. Loading real transaction data...")
    real_df = pd.read_csv('data/labeled/real_transactions_labeled.csv')
    print(f"   Loaded {len(real_df)} real transactions")

    # Filter out "Other" category for better quality
    real_df_filtered = real_df[real_df['category'] != 'Other'].copy()
    print(f"   After filtering 'Other': {len(real_df_filtered)} transactions")

    print("\n   Category distribution in real data:")
    print(real_df_filtered['category'].value_counts())

    # 2. Generate synthetic data
    print("\n2. Generating synthetic transactions...")
    synthetic_transactions = generate_synthetic_transactions(taxonomy, n_samples=8000)
    synthetic_df = pd.DataFrame(synthetic_transactions)
    print(f"   Generated {len(synthetic_df)} synthetic transactions")

    print("\n   Category distribution in synthetic data:")
    synthetic_category_dist = pd.Series([t['label'] for t in synthetic_transactions])
    print(synthetic_category_dist.value_counts())

    # 3. Create train/val/test splits
    print("\n3. Creating train/val/test splits...")

    # Create output directory
    output_dir = Path('data/processed')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Split real data (60% train, 20% val, 20% test)
    real_shuffled = real_df_filtered.sample(frac=1, random_state=42).reset_index(drop=True)
    n_real = len(real_shuffled)

    real_train = real_shuffled[:int(n_real * 0.6)]
    real_val = real_shuffled[int(n_real * 0.6):int(n_real * 0.8)]
    real_test = real_shuffled[int(n_real * 0.8):]

    # Split synthetic data (70% train, 15% val, 15% test)
    synthetic_shuffled = synthetic_df.sample(frac=1, random_state=42).reset_index(drop=True)
    n_synth = len(synthetic_shuffled)

    synth_train = synthetic_shuffled[:int(n_synth * 0.7)]
    synth_val = synthetic_shuffled[int(n_synth * 0.7):int(n_synth * 0.85)]
    synth_test = synthetic_shuffled[int(n_synth * 0.85):]

    # Combine real and synthetic for each split
    train_combined = pd.concat([real_train, synth_train], ignore_index=True).sample(frac=1, random_state=42)
    val_combined = pd.concat([real_val, synth_val], ignore_index=True).sample(frac=1, random_state=42)
    test_combined = pd.concat([real_test, synth_test], ignore_index=True).sample(frac=1, random_state=42)

    print(f"\n   Train: {len(train_combined)} ({len(real_train)} real + {len(synth_train)} synthetic)")
    print(f"   Val:   {len(val_combined)} ({len(real_val)} real + {len(synth_val)} synthetic)")
    print(f"   Test:  {len(test_combined)} ({len(real_test)} real + {len(synth_test)} synthetic)")

    # 4. Convert to JSONL
    print("\n4. Converting to JSONL format...")
    convert_real_to_jsonl(train_combined, output_dir / 'train.jsonl')
    convert_real_to_jsonl(val_combined, output_dir / 'val.jsonl')
    convert_real_to_jsonl(test_combined, output_dir / 'test.jsonl')

    print("\n✓ Dataset preparation complete!")
    print(f"\n   Output files:")
    print(f"   - {output_dir / 'train.jsonl'}")
    print(f"   - {output_dir / 'val.jsonl'}")
    print(f"   - {output_dir / 'test.jsonl'}")

    # Print final statistics
    print(f"\n   Final statistics:")
    print(f"   Train category distribution:")
    print(train_combined['category'].value_counts())

if __name__ == '__main__':
    main()
