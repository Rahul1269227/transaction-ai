#!/usr/bin/env python3
"""
Prepare a more balanced dataset using multiple strategies:
1. Generate more synthetic data for minority classes
2. Undersample majority classes (ATM/Cash, Investments)
3. Use class weights during training
"""

import pandas as pd
import json
import yaml
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

def load_taxonomy():
    """Load taxonomy"""
    with open('data/taxonomy.yaml', 'r') as f:
        return yaml.safe_load(f)

def generate_enhanced_synthetic_transactions(taxonomy: Dict, target_samples_per_category: int = 3000) -> List[Dict]:
    """
    Generate synthetic transactions with enhanced templates for better quality
    """
    synthetic = []

    # Enhanced templates with more variety
    templates = {
        'Food & Dining': [
            'UPI-{merchant}-ORDER',
            'POS PURCHASE {merchant}',
            '{merchant} ONLINE ORDER',
            'SWIGGY {merchant}',
            'ZOMATO {merchant}',
            'UPI-{merchant}-PAYMENT',
            '{merchant} FOOD DELIVERY',
            'ONLINE FOOD ORDER {merchant}',
        ],
        'Groceries': [
            'BIGBASKET PURCHASE',
            'DMART {merchant}',
            'BLINKIT ORDER {merchant}',
            'ZEPTO GROCERY',
            'JIOMART PURCHASE',
            '{merchant} GROCERY STORE',
            'ONLINE GROCERY {merchant}',
        ],
        'Transport': [
            'UPI-UBER-TRIP',
            'UPI-OLA-RIDE',
            'RAPIDO BIKE RIDE',
            'METRO CARD RECHARGE',
            'FASTAG TOLL DEDUCTION',
            'UBER TRIP PAYMENT',
            'OLA CAB PAYMENT',
            'AUTO RICKSHAW PAYMENT',
        ],
        'Travel': [
            'IRCTC TICKET BOOKING',
            'MAKEMYTRIP FLIGHT BOOKING',
            'OYO HOTELS PAYMENT',
            'GOIBIBO BOOKING',
            'INDIGO AIRLINES',
            'SPICEJET FLIGHT',
            'REDBUS TICKET',
            'CLEARTRIP BOOKING',
            'YATRA TRAVEL',
        ],
        'Utilities': [
            'BSES RAJDHANI POWER',
            'AIRTEL BROADBAND BILL',
            'JIO MOBILE RECHARGE',
            'TATA SKY DTH',
            'INDANE GAS BOOKING',
            'VODAFONE BILL PAYMENT',
            'RELIANCE JIO RECHARGE',
            'ELECTRICITY BILL PAYMENT',
        ],
        'Shopping': [
            'AMAZON ORDER',
            'FLIPKART PURCHASE',
            'MYNTRA FASHION',
            'NYKAA BEAUTY',
            'AJIO SHOPPING',
            'MEESHO ORDER',
            'SNAPDEAL PURCHASE',
            'AMAZON PAY PURCHASE',
        ],
        'Entertainment': [
            'NETFLIX SUBSCRIPTION',
            'PRIME VIDEO MONTHLY',
            'PVR CINEMA TICKET',
            'BOOKMYSHOW TICKET',
            'SPOTIFY PREMIUM',
            'HOTSTAR SUBSCRIPTION',
            'YOUTUBE PREMIUM',
            'INOX CINEMA',
        ],
        'Health': [
            'APOLLO PHARMACY',
            '1MG MEDICINE ORDER',
            'PHARMEASY PURCHASE',
            'MAX HOSPITAL',
            'FORTIS HEALTHCARE',
            'MEDLIFE MEDICINES',
            'NETMEDS ORDER',
            'HOSPITAL PAYMENT',
        ],
        'Education': [
            'SCHOOL FEE PAYMENT',
            'COLLEGE TUITION FEE',
            'UDEMY COURSE',
            'COURSERA SUBSCRIPTION',
            'BYJU APP PAYMENT',
            'UNACADEMY SUBSCRIPTION',
            'VEDANTU CLASSES',
            'EXAM FEE PAYMENT',
        ],
        'Rent': [
            'HOUSE RENT PAYMENT',
            'APARTMENT RENT',
            'MONTHLY RENT TRANSFER',
            'LEASE PAYMENT',
            'FLAT RENT',
            'PG RENT PAYMENT',
            'HOSTEL FEE',
        ],
        'ATM/Cash': [
            'CASHDEP/{city}/',
            'ATM WDL {bank}',
            'CASH WITHDRAWAL',
            'ATM CASH WITHDRAWAL',
            'POS CASH BACK',
        ],
        'Transfers/UPI': [
            'FDRL/INTERNAL FUND TRANSFE',
            'FDRL/NATIONAL ELECTRONIC F',
            'UPI-P2P-{name}@paytm',
            'IMPS TRANSFER TO {name}',
            'NEFT TO {name}',
            'UPI-{name}@phonepe',
            'FUND TRANSFER',
        ],
        'Investments': [
            'ZERODHA KITE TRADING',
            'GROWW MUTUAL FUND SIP',
            'UPSTOX TRADING',
            'SIP INVESTMENT',
            'HDFC LIFE INSURANCE PREMIUM',
            'ICICI PRUDENTIAL',
            'FIXED DEPOSIT',
        ],
        'Bills': [
            'ELECTRICITY BILL PAYMENT',
            'WATER BILL PAYMENT',
            'CREDIT CARD BILL',
            'LOAN EMI DEDUCTION',
            'SOCIETY MAINTENANCE',
            'PHONE BILL PAYMENT',
            'INTERNET BILL PAYMENT',
        ],
        'Fees & Charges': [
            'BANK SERVICE CHARGE',
            'TRANSACTION FEE DEBIT',
            'ANNUAL FEE',
            'GST CHARGES',
            'PROCESSING FEE',
            'CONVENIENCE FEE',
            'LATE PAYMENT FEE',
        ],
        'Income/Salary': [
            'SALARY CREDIT',
            'BONUS CREDIT',
            'REFUND FROM {merchant}',
            'CASHBACK CREDIT',
            'INTEREST CREDIT',
            'COMMISSION CREDIT',
            'INCENTIVE PAYMENT',
        ],
        'Fuel': [
            'HPCL PETROL PUMP',
            'IOCL FUEL STATION',
            'BPCL PETROL',
            'SHELL PETROL PUMP',
            'RELIANCE PETROL',
            'ESSAR FUEL',
            'CNG STATION',
        ],
    }

    # Merchants and other variables
    merchants = {
        'Food & Dining': ['DOMINOS', 'KFC', 'MCDONALDS', 'STARBUCKS', 'HALDIRAMS', 'CAFE COFFEE DAY', 'BURGER KING', 'SUBWAY'],
        'Groceries': ['MORE', 'RELIANCE FRESH', 'SPENCERS', 'NATURE BASKET', 'SPAR'],
        'Shopping': ['AMAZON', 'FLIPKART', 'MYNTRA', 'AJIO', 'NYKAA'],
        'default': ['PAYTM', 'PHONEPE', 'GOOGLEPAY']
    }

    cities = ['DELHI', 'MUMBAI', 'BANGALORE', 'CHENNAI', 'KOLKATA', 'PUNE', 'HYDERABAD', 'GURGAON']
    banks = ['HDFC', 'ICICI', 'SBI', 'AXIS', 'KOTAK', 'YES BANK']
    names = ['RAHUL', 'AMIT', 'PRIYA', 'NEHA', 'VIKAS', 'ANJALI', 'ROHIT', 'SNEHA']

    # Get categories (exclude 'Other')
    categories = [cat for cat in taxonomy['categories'] if cat['name'] != 'Other']

    # Generate samples per category
    for category in categories:
        cat_name = category['name']

        if cat_name not in templates:
            continue

        # Generate target number of samples for this category
        for _ in range(target_samples_per_category):
            template = random.choice(templates[cat_name])
            merchant_list = merchants.get(cat_name, merchants['default'])
            merchant = random.choice(merchant_list)

            # Replace placeholders
            text = template.replace('{merchant}', merchant)
            text = text.replace('{amount}', f"{random.randint(100, 5000)}")
            text = text.replace('{city}', random.choice(cities))
            text = text.replace('{bank}', random.choice(banks))
            text = text.replace('{name}', random.choice(names))

            # Determine amount range based on category
            amount_ranges = {
                'Food & Dining': (50, 1500),
                'Groceries': (200, 3000),
                'Transport': (30, 500),
                'Travel': (500, 15000),
                'Utilities': (200, 2000),
                'Shopping': (300, 5000),
                'Entertainment': (100, 1000),
                'Health': (100, 5000),
                'Education': (500, 50000),
                'Rent': (5000, 50000),
                'ATM/Cash': (500, 20000),
                'Transfers/UPI': (100, 50000),
                'Investments': (500, 100000),
                'Bills': (200, 5000),
                'Fees & Charges': (10, 500),
                'Income/Salary': (10000, 200000),
                'Fuel': (500, 5000),
            }

            amount_min, amount_max = amount_ranges.get(cat_name, (100, 10000))

            # Generate transaction
            synthetic.append({
                'text': text,
                'label': cat_name,
                'amount': random.randint(amount_min, amount_max),
                'currency': 'INR',
                'date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
            })

    return synthetic

def undersample_majority_classes(df: pd.DataFrame, max_samples_per_class: int = 5000) -> pd.DataFrame:
    """
    Undersample majority classes to reduce imbalance
    """
    balanced_dfs = []

    for category in df['category'].unique():
        cat_df = df[df['category'] == category]

        if len(cat_df) > max_samples_per_class:
            # Randomly sample
            cat_df = cat_df.sample(n=max_samples_per_class, random_state=42)

        balanced_dfs.append(cat_df)

    return pd.concat(balanced_dfs, ignore_index=True)

def convert_to_jsonl(df: pd.DataFrame, output_path: str):
    """Convert DataFrame to JSONL format"""
    with open(output_path, 'w') as f:
        for _, row in df.iterrows():
            if pd.isna(row.get('TRANSACTION DETAILS', row.get('text'))):
                continue

            # Handle both real and synthetic data formats
            if 'TRANSACTION DETAILS' in row:
                text = str(row['TRANSACTION DETAILS'])
                category = str(row['category'])
                amount = None
                if pd.notna(row.get('WITHDRAWAL AMT')):
                    amount = -float(row['WITHDRAWAL AMT'])
                elif pd.notna(row.get('DEPOSIT AMT')):
                    amount = float(row['DEPOSIT AMT'])
                date = str(row['DATE'])[:10] if pd.notna(row.get('DATE')) else None
            else:
                text = str(row['text'])
                category = str(row['label'])
                amount = row.get('amount')
                date = row.get('date')

            record = {
                'text': text,
                'label': category,
                'amount': amount,
                'currency': 'INR',
                'date': date
            }

            f.write(json.dumps(record) + '\n')

def main():
    print("Preparing balanced dataset with multiple strategies...\n")

    # Load taxonomy
    taxonomy = load_taxonomy()

    # 1. Load real data
    print("1. Loading real transaction data...")
    real_df = pd.read_csv('data/labeled/real_transactions_labeled.csv')
    real_df_filtered = real_df[real_df['category'] != 'Other'].copy()
    print(f"   Real data: {len(real_df_filtered)} transactions")

    # 2. Undersample majority classes
    print("\n2. Undersampling majority classes (ATM/Cash, Investments)...")
    real_balanced = undersample_majority_classes(real_df_filtered, max_samples_per_class=5000)
    print(f"   After undersampling: {len(real_balanced)} transactions")
    print("\n   Category distribution after undersampling:")
    print(real_balanced['category'].value_counts())

    # 3. Generate enhanced synthetic data
    print("\n3. Generating enhanced synthetic transactions...")
    print("   Target: 3000 samples per category")
    synthetic_transactions = generate_enhanced_synthetic_transactions(taxonomy, target_samples_per_category=3000)
    synthetic_df = pd.DataFrame(synthetic_transactions)
    print(f"   Generated {len(synthetic_df)} synthetic transactions")

    print("\n   Category distribution in synthetic data:")
    print(pd.Series([t['label'] for t in synthetic_transactions]).value_counts())

    # 4. Combine and split
    print("\n4. Combining real (undersampled) + synthetic data...")

    # Convert real data to same format as synthetic
    real_for_combine = []
    for _, row in real_balanced.iterrows():
        amount = None
        if pd.notna(row.get('WITHDRAWAL AMT')):
            amount = -float(row['WITHDRAWAL AMT'])
        elif pd.notna(row.get('DEPOSIT AMT')):
            amount = float(row['DEPOSIT AMT'])

        real_for_combine.append({
            'text': str(row['TRANSACTION DETAILS']),
            'label': str(row['category']),
            'amount': amount,
            'currency': 'INR',
            'date': str(row['DATE'])[:10] if pd.notna(row.get('DATE')) else None
        })

    real_df_unified = pd.DataFrame(real_for_combine)

    # Combine
    combined_df = pd.concat([real_df_unified, synthetic_df], ignore_index=True)
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"   Total combined: {len(combined_df)} transactions")
    print(f"   Real: {len(real_df_unified)} ({len(real_df_unified)/len(combined_df)*100:.1f}%)")
    print(f"   Synthetic: {len(synthetic_df)} ({len(synthetic_df)/len(combined_df)*100:.1f}%)")

    # 5. Split into train/val/test
    print("\n5. Creating train/val/test splits (70/15/15)...")
    n = len(combined_df)
    train_df = combined_df[:int(n * 0.7)]
    val_df = combined_df[int(n * 0.7):int(n * 0.85)]
    test_df = combined_df[int(n * 0.85):]

    print(f"   Train: {len(train_df)}")
    print(f"   Val:   {len(val_df)}")
    print(f"   Test:  {len(test_df)}")

    # 6. Save to JSONL
    print("\n6. Saving to JSONL format...")
    output_dir = Path('data/balanced')
    output_dir.mkdir(parents=True, exist_ok=True)

    convert_to_jsonl(train_df, output_dir / 'train.jsonl')
    convert_to_jsonl(val_df, output_dir / 'val.jsonl')
    convert_to_jsonl(test_df, output_dir / 'test.jsonl')

    print("\n✓ Balanced dataset preparation complete!")
    print(f"\n   Output files:")
    print(f"   - {output_dir / 'train.jsonl'}")
    print(f"   - {output_dir / 'val.jsonl'}")
    print(f"   - {output_dir / 'test.jsonl'}")

    # Print final statistics
    print(f"\n   Final train set distribution:")
    print(train_df['label'].value_counts().sort_index())

    # Calculate class weights for training
    print(f"\n7. Calculating class weights for training...")
    class_counts = train_df['label'].value_counts()
    total_samples = len(train_df)
    n_classes = len(class_counts)

    class_weights = {}
    for cls in class_counts.index:
        # weight = total_samples / (n_classes * class_count)
        weight = total_samples / (n_classes * class_counts[cls])
        class_weights[cls] = weight

    print("\n   Recommended class weights:")
    for cls, weight in sorted(class_weights.items()):
        print(f"   {cls:20s}: {weight:.4f}")

    # Save class weights
    with open(output_dir / 'class_weights.json', 'w') as f:
        json.dump(class_weights, f, indent=2)

    print(f"\n   Class weights saved to {output_dir / 'class_weights.json'}")

if __name__ == '__main__':
    main()
