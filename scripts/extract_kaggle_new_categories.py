"""
Extract Real Transactions from Kaggle Data for New Categories
Maps Kaggle transactions to our new 12 categories
"""

import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mapping keywords for each new category
CATEGORY_MAPPINGS = {
    'insurance': {
        'keywords': ['insurance', 'lic', 'hdfc life', 'icici prudential', 'star health',
                    'max life', 'sbi life', 'bajaj allianz', 'policy', 'premium'],
        'patterns': [r'\binsurance\b', r'\bpremium\b', r'\bpolicy\b', r'\blic\b']
    },
    'charity_donations': {
        'keywords': ['donation', 'charity', 'ngo', 'temple', 'church', 'mosque',
                    'red cross', 'unicef', 'oxfam', 'donate', 'milaap', 'ketto'],
        'patterns': [r'\bdonation\b', r'\bcharity\b', r'\bngo\b', r'\btemple\b', r'\bchurch\b']
    },
    'personal_care': {
        'keywords': ['salon', 'spa', 'gym', 'fitness', 'cult.fit', 'urban company',
                    'vlcc', 'naturals', 'lakme', 'massage', 'facial', 'haircut'],
        'patterns': [r'\bsalon\b', r'\bspa\b', r'\bgym\b', r'\bfitness\b', r'\bmassage\b']
    },
    'pets': {
        'keywords': ['pedigree', 'whiskas', 'drools', 'royal canin', 'pet', 'dog food',
                    'cat food', 'veterinary', 'vet', 'pet shop', 'pet store'],
        'patterns': [r'\bpet\b', r'\bdog\b', r'\bcat\b', r'\bvet\b', r'\bpedigree\b']
    },
    'home_improvement': {
        'keywords': ['furniture', 'ikea', 'pepperfry', 'urban ladder', 'livspace',
                    'carpenter', 'plumber', 'electrician', 'home repair', 'renovation'],
        'patterns': [r'\bfurniture\b', r'\bikea\b', r'\bcarpenter\b', r'\bplumber\b']
    },
    'automotive': {
        'keywords': ['car service', 'bike service', 'vehicle', 'auto', 'tyre', 'tire',
                    'maruti', 'honda', 'hyundai', 'mechanic', 'spare parts', 'oil change'],
        'patterns': [r'\bcar\b', r'\bvehicle\b', r'\bauto\b', r'\bmechanic\b', r'\btyre\b']
    },
    'taxes_government': {
        'keywords': ['income tax', 'gst', 'property tax', 'tax payment', 'tds',
                    'challan', 'municipal', 'government fee', 'license fee', 'passport'],
        'patterns': [r'\btax\b', r'\bgst\b', r'\btds\b', r'\bchallan\b', r'\bgovernment\b']
    },
    'electronics_technology': {
        'keywords': ['iphone', 'samsung', 'laptop', 'macbook', 'ipad', 'dell', 'hp',
                    'lenovo', 'croma', 'reliance digital', 'vijay sales', 'electronics'],
        'patterns': [r'\biphone\b', r'\blaptop\b', r'\bmacbook\b', r'\belectronics\b']
    },
    'professional_services': {
        'keywords': ['lawyer', 'attorney', 'legal', 'consultant', 'consulting',
                    'accountant', 'ca', 'advocate', 'professional fee'],
        'patterns': [r'\blawyer\b', r'\blegal\b', r'\bconsultant\b', r'\battorney\b']
    },
    'kids_family': {
        'keywords': ['firstcry', 'kids', 'children', 'baby', 'toy', 'hamleys',
                    'daycare', 'diaper', 'infant', 'school supplies'],
        'patterns': [r'\bkids\b', r'\bbaby\b', r'\btoy\b', r'\bchildren\b', r'\bdiaper\b']
    },
    'subscriptions_memberships': {
        'keywords': ['netflix', 'spotify', 'amazon prime', 'hotstar', 'youtube premium',
                    'icloud', 'office 365', 'subscription', 'membership', 'monthly'],
        'patterns': [r'\bnetflix\b', r'\bspotify\b', r'\bprime\b', r'\bsubscription\b']
    },
    'gifts_occasions': {
        'keywords': ['gift', 'flower', 'bouquet', 'ferns n petals', 'archies',
                    'gift card', 'present', 'birthday', 'anniversary'],
        'patterns': [r'\bgift\b', r'\bflower\b', r'\bbouquet\b', r'\bbirthday\b']
    }
}

def match_category(text: str) -> str:
    """
    Match transaction text to new categories

    Args:
        text: Transaction description

    Returns:
        Category ID or None
    """
    text_lower = text.lower()

    # Check each category
    for category, config in CATEGORY_MAPPINGS.items():
        # Check keywords
        for keyword in config['keywords']:
            if keyword.lower() in text_lower:
                return category

        # Check patterns
        for pattern in config['patterns']:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return category

    return None

def extract_new_category_transactions():
    """Extract transactions matching new categories from Kaggle data"""

    print("Loading Kaggle data...")
    kaggle_file = Path(__file__).parent.parent / "data" / "raw" / "bank_transactions.csv"

    try:
        df = pd.read_csv(kaggle_file)
        print(f"Loaded {len(df)} transactions from Kaggle data")
    except Exception as e:
        print(f"Error loading Kaggle data: {e}")
        return

    # Find transaction description column
    desc_columns = ['TRANSACTION DETAILS', 'description', 'Description', 'transaction', 'Transaction',
                    'narration', 'Narration', 'text', 'Text']

    desc_col = None
    for col in desc_columns:
        if col in df.columns:
            desc_col = col
            break

    if not desc_col:
        print(f"Available columns: {df.columns.tolist()}")
        print("Could not find transaction description column!")
        return

    print(f"Using column: {desc_col}")

    # Extract matching transactions
    category_samples = {cat: [] for cat in CATEGORY_MAPPINGS.keys()}

    for idx, row in df.iterrows():
        text = str(row[desc_col])
        category = match_category(text)

        if category:
            # Create sample
            sample = {
                'text': text,
                'label': category
            }

            # Add amount if available
            amount_cols = ['WITHDRAWAL AMT', 'DEPOSIT AMT', 'amount', 'Amount', 'debit', 'Debit', 'credit', 'Credit']
            for amt_col in amount_cols:
                if amt_col in df.columns and pd.notna(row[amt_col]):
                    try:
                        sample['amount'] = float(row[amt_col])
                        sample['currency'] = 'INR'
                        break
                    except:
                        pass

            category_samples[category].append(sample)

    # Print summary
    print("\n=== Extracted Transactions Summary ===")
    total = 0
    for cat, samples in category_samples.items():
        count = len(samples)
        total += count
        print(f"  {cat}: {count} transactions")

    print(f"\nTotal extracted: {total} transactions")

    if total == 0:
        print("\n⚠️  No matching transactions found!")
        print("The Kaggle dataset may not contain transactions for new categories.")
        return

    # Save to file
    output_dir = Path(__file__).parent.parent / "data" / "kaggle_new_categories"
    output_dir.mkdir(exist_ok=True)

    all_samples = []
    for samples in category_samples.values():
        all_samples.extend(samples)

    output_file = output_dir / "extracted_transactions.jsonl"

    print(f"\nSaving to: {output_file}")
    with open(output_file, 'w') as f:
        for sample in all_samples:
            f.write(json.dumps(sample) + '\n')

    print("\n✅ Extraction complete!")

    # Show some examples
    print("\n=== Sample Transactions ===")
    for cat, samples in category_samples.items():
        if samples:
            print(f"\n{cat.upper()}:")
            for i, sample in enumerate(samples[:3], 1):
                print(f"  {i}. {sample['text']}")
                if i >= 3:
                    break

if __name__ == '__main__':
    extract_new_category_transactions()
