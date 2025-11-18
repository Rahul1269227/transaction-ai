#!/usr/bin/env python3
"""
Learn new merchants from user corrections and add to gazetteer
Automatically extracts merchant names from corrections and updates gazetteer

Usage:
    python3 scripts/learn_merchants_from_corrections.py
    python3 scripts/learn_merchants_from_corrections.py --corrections data/corrections/corrections.jsonl
    python3 scripts/learn_merchants_from_corrections.py --min-corrections 5
"""

import json
import argparse
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional

# Add parent directory to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file"""
    data = []
    if not file_path.exists():
        return data

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def load_csv_gazetteer(file_path: Path) -> tuple[List[Dict], set]:
    """Load existing merchant gazetteer"""
    merchants = []
    canonical_names = set()

    if not file_path.exists():
        return merchants, canonical_names

    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip header
        header = f.readline()

        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse CSV: merchant_id,canonical_name,aliases,category,subcategory
            parts = line.split(',', 4)
            if len(parts) >= 4:
                merchant_id, canonical_name, aliases, category = parts[:4]
                subcategory = parts[4] if len(parts) > 4 else ""

                merchants.append({
                    'merchant_id': merchant_id,
                    'canonical_name': canonical_name,
                    'aliases': aliases,
                    'category': category,
                    'subcategory': subcategory
                })
                canonical_names.add(canonical_name.upper())

    return merchants, canonical_names


def save_csv_gazetteer(merchants: List[Dict], file_path: Path) -> None:
    """Save merchant gazetteer to CSV"""
    with open(file_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("merchant_id,canonical_name,aliases,category,subcategory\n")

        # Write merchants
        for m in merchants:
            f.write(f"{m['merchant_id']},{m['canonical_name']},{m['aliases']},{m['category']},{m['subcategory']}\n")


def extract_merchant_name(text: str) -> Optional[str]:
    """
    Extract potential merchant name from transaction text

    Strategy:
    1. Look for brand names (capitalized words)
    2. Remove common transaction keywords
    3. Extract first 1-3 capitalized words
    """
    # Remove common noise
    noise_keywords = [
        'UPI', 'IMPS', 'NEFT', 'RTGS', 'POS', 'CARD', 'ATM',
        'PAYMENT', 'PURCHASE', 'BILL', 'INR', 'RS',
        'DEBIT', 'CREDIT', 'TXN', 'TRANSACTION', 'TO', 'FROM',
        'AT', 'ON', 'IN', 'VIA', 'BY'
    ]

    # Clean text
    cleaned = text.upper()
    for keyword in noise_keywords:
        cleaned = re.sub(rf'\b{keyword}\b', '', cleaned)

    # Extract capitalized word sequences
    words = cleaned.split()
    merchant_candidates = []

    current_sequence = []
    for word in words:
        # Check if word is mostly alphabetic and capitalized
        if len(word) >= 3 and word[0].isalpha():
            current_sequence.append(word)
        else:
            if current_sequence:
                merchant_candidates.append(' '.join(current_sequence))
                current_sequence = []

    if current_sequence:
        merchant_candidates.append(' '.join(current_sequence))

    # Return longest candidate (likely the merchant name)
    if merchant_candidates:
        return max(merchant_candidates, key=len)

    return None


def learn_merchants_from_corrections(
    corrections: List[Dict],
    existing_merchants: List[Dict],
    existing_names: set,
    min_occurrences: int = 2
) -> List[Dict]:
    """
    Extract new merchants from corrections

    Args:
        corrections: List of correction records
        existing_merchants: Existing merchant records
        existing_names: Set of existing canonical merchant names
        min_occurrences: Minimum number of corrections before adding merchant

    Returns:
        List of new merchant records to add
    """
    # Group corrections by extracted merchant name
    merchant_corrections = defaultdict(list)

    for corr in corrections:
        if not corr.get('was_incorrect'):
            # Only learn from actual corrections
            continue

        text = corr.get('text', '')
        correct_category = corr.get('correct_category')
        correct_subcategory = corr.get('correct_subcategory')

        # Extract potential merchant name
        merchant_name = extract_merchant_name(text)

        if merchant_name and len(merchant_name) >= 3:
            merchant_corrections[merchant_name].append({
                'category': correct_category,
                'subcategory': correct_subcategory,
                'text': text
            })

    # Build new merchant records
    new_merchants = []
    next_id = max([int(m['merchant_id']) for m in existing_merchants], default=0) + 1

    for merchant_name, corr_list in merchant_corrections.items():
        # Skip if already in gazetteer
        if merchant_name in existing_names:
            continue

        # Skip if not enough occurrences
        if len(corr_list) < min_occurrences:
            continue

        # Determine category by majority vote
        category_counts = defaultdict(int)
        subcategory_counts = defaultdict(int)

        for corr in corr_list:
            if corr['category']:
                category_counts[corr['category']] += 1
            if corr['subcategory']:
                subcategory_counts[corr['subcategory']] += 1

        category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else 'other'
        subcategory = max(subcategory_counts.items(), key=lambda x: x[1])[0] if subcategory_counts else ''

        # Convert category name to ID
        category_id = category.lower().replace(' & ', '_').replace(' ', '_').replace('/', '_')

        # Generate aliases (lowercase, variations)
        canonical_upper = merchant_name.upper()
        merchant_lower = merchant_name.lower()
        merchant_simple = re.sub(r'[^a-z0-9]', '', merchant_lower)

        aliases = f'"{merchant_lower},{canonical_upper},{merchant_simple}"'

        new_merchants.append({
            'merchant_id': str(next_id),
            'canonical_name': canonical_upper,
            'aliases': aliases,
            'category': category_id,
            'subcategory': subcategory,
            'occurrence_count': len(corr_list)
        })

        next_id += 1

    return new_merchants


def main():
    parser = argparse.ArgumentParser(description="Learn merchants from corrections")
    parser.add_argument(
        '--corrections',
        default='data/corrections/corrections.jsonl',
        help='Path to corrections JSONL file'
    )
    parser.add_argument(
        '--gazetteer',
        default='data/gazetteer/merchant_aliases.csv',
        help='Path to merchant gazetteer CSV'
    )
    parser.add_argument(
        '--min-corrections',
        type=int,
        default=2,
        help='Minimum corrections before adding merchant (default: 2)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be added without actually modifying gazetteer'
    )

    args = parser.parse_args()

    corrections_path = BASE_DIR / args.corrections
    gazetteer_path = BASE_DIR / args.gazetteer

    print("=" * 60)
    print("Merchant Learning from Corrections")
    print("=" * 60)

    # Load corrections
    print(f"\n📖 Loading corrections from: {corrections_path}")
    corrections = load_jsonl(corrections_path)

    if not corrections:
        print("❌ No corrections found")
        return

    incorrect_corrections = [c for c in corrections if c.get('was_incorrect')]
    print(f"✅ Found {len(corrections)} total corrections ({len(incorrect_corrections)} incorrect predictions)")

    # Load existing gazetteer
    print(f"\n📖 Loading existing gazetteer from: {gazetteer_path}")
    existing_merchants, existing_names = load_csv_gazetteer(gazetteer_path)
    print(f"✅ Found {len(existing_merchants)} existing merchants")

    # Learn new merchants
    print(f"\n🔍 Extracting merchants from corrections (min occurrences: {args.min_corrections})...")
    new_merchants = learn_merchants_from_corrections(
        corrections,
        existing_merchants,
        existing_names,
        min_occurrences=args.min_corrections
    )

    if not new_merchants:
        print("ℹ️  No new merchants to add")
        return

    print(f"\n✨ Found {len(new_merchants)} new merchants to add:")
    for m in new_merchants:
        print(f"  • {m['canonical_name']} → {m['category']} ({m['occurrence_count']} occurrences)")

    if args.dry_run:
        print("\n🔍 DRY RUN: No changes made to gazetteer")
        return

    # Add new merchants
    all_merchants = existing_merchants + new_merchants

    # Save updated gazetteer
    print(f"\n💾 Saving updated gazetteer to: {gazetteer_path}")
    save_csv_gazetteer(all_merchants, gazetteer_path)

    print(f"\n✅ SUCCESS!")
    print(f"   Added {len(new_merchants)} new merchants")
    print(f"   Total merchants: {len(all_merchants)}")
    print("\n📊 Next steps:")
    print("   1. Review the new merchants in the gazetteer")
    print("   2. Restart the API service to load the updated gazetteer")
    print("   3. Test categorization with transactions from these merchants")


if __name__ == '__main__':
    main()
