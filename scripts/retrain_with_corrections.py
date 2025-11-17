#!/usr/bin/env python3
"""
Retrain model with user corrections from active learning
Run this weekly or when you have 50+ corrections

Usage:
    python3 scripts/retrain_with_corrections.py
    python3 scripts/retrain_with_corrections.py --corrections data/corrections/corrections.jsonl
    python3 scripts/retrain_with_corrections.py --min-corrections 10
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import List, Dict

# Add parent directory to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))


def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def save_jsonl(data: List[Dict], file_path: Path) -> None:
    """Save data to JSONL"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            json.dump(item, f)
            f.write('\n')


def merge_corrections(original_data: List[Dict], corrections: List[Dict]) -> tuple[List[Dict], int]:
    """
    Merge corrections into training data
    Priority: corrections > original

    Returns:
        (corrected_data, corrections_applied)
    """
    # Build correction index by text (normalize to lowercase)
    correction_map = {}
    for corr in corrections:
        text = corr['text'].lower().strip()
        correction_map[text] = {
            'category': corr['correct_category'],
            'subcategory': corr.get('correct_subcategory'),
        }

    # Apply corrections to original data
    corrected_data = []
    corrections_applied = 0
    new_examples = []

    for item in original_data:
        text = item['text'].lower().strip()

        if text in correction_map:
            # Override with corrected category
            item['category'] = correction_map[text]['category']
            if correction_map[text]['subcategory']:
                item['subcategory'] = correction_map[text]['subcategory']
            corrections_applied += 1
            # Mark as corrected (remove from map)
            del correction_map[text]

        corrected_data.append(item)

    # Add remaining corrections as new training examples
    for text, correction in correction_map.items():
        # Find original correction entry to get full details
        matching_corr = next((c for c in corrections if c['text'].lower().strip() == text), None)
        if matching_corr:
            new_example = {
                'text': matching_corr['text'],
                'category': correction['category'],
                'subcategory': correction.get('subcategory'),
                'amount': matching_corr.get('amount'),
                'date': matching_corr.get('date'),
            }
            new_examples.append(new_example)
            corrected_data.append(new_example)

    print(f"✅ Applied {corrections_applied} corrections to existing training data")
    if new_examples:
        print(f"✅ Added {len(new_examples)} new training examples from corrections")

    return corrected_data, corrections_applied + len(new_examples)


def main():
    parser = argparse.ArgumentParser(
        description="Retrain model with user corrections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (uses defaults)
  python3 scripts/retrain_with_corrections.py

  # Specify corrections file
  python3 scripts/retrain_with_corrections.py --corrections data/corrections/corrections.jsonl

  # Lower minimum corrections threshold
  python3 scripts/retrain_with_corrections.py --min-corrections 10

  # Specify output file
  python3 scripts/retrain_with_corrections.py --output data/balanced/train_with_corrections.jsonl
        """
    )
    parser.add_argument(
        '--corrections',
        default='data/corrections/corrections.jsonl',
        help='Path to corrections file (default: data/corrections/corrections.jsonl)'
    )
    parser.add_argument(
        '--train-data',
        default='data/balanced/train_natural.jsonl',
        help='Path to original training data (default: data/balanced/train_natural.jsonl)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path (default: data/balanced/train_with_corrections_TIMESTAMP.jsonl)'
    )
    parser.add_argument(
        '--min-corrections',
        type=int,
        default=5,
        help='Minimum number of corrections required to proceed (default: 5)'
    )
    parser.add_argument(
        '--auto-retrain',
        action='store_true',
        help='Automatically retrain model after merging corrections'
    )
    args = parser.parse_args()

    print("=" * 70)
    print("RETRAINING WITH USER CORRECTIONS")
    print("=" * 70)

    # Load corrections
    corrections_file = Path(args.corrections)
    if not corrections_file.exists():
        print(f"\n❌ No corrections file found at {corrections_file}")
        print("   Users need to provide feedback first via the UI")
        print(f"   Corrections will be stored at: {BASE_DIR / 'data' / 'corrections' / 'corrections.jsonl'}")
        sys.exit(1)

    corrections = load_jsonl(corrections_file)
    print(f"\n📊 Loaded {len(corrections)} feedback entries")

    if len(corrections) < args.min_corrections:
        print(f"\n⚠️  Only {len(corrections)} corrections found (minimum: {args.min_corrections})")
        print("   Retraining requires more user feedback for meaningful improvement")
        print(f"   Collect at least {args.min_corrections - len(corrections)} more corrections")
        sys.exit(1)

    # Stats
    incorrect_count = sum(1 for c in corrections if c.get('was_incorrect', False))
    print(f"   - {incorrect_count} were incorrect predictions (need correction)")
    print(f"   - {len(corrections) - incorrect_count} were correct confirmations")

    # Category distribution
    category_dist = Counter(c['correct_category'] for c in corrections)
    print(f"\n📈 Corrections by category:")
    for cat, count in category_dist.most_common(10):
        print(f"   - {cat}: {count}")

    # Load original training data
    train_data_file = BASE_DIR / args.train_data
    if not train_data_file.exists():
        print(f"\n❌ Training data not found at {train_data_file}")
        sys.exit(1)

    print(f"\n📂 Loading original training data from {train_data_file}")
    original_data = load_jsonl(train_data_file)
    print(f"   Loaded {len(original_data)} training samples")

    # Merge
    print(f"\n🔄 Merging corrections...")
    corrected_data, total_changes = merge_corrections(original_data, corrections)
    print(f"   Total dataset size after merge: {len(corrected_data)} samples")

    # Save
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = BASE_DIR / "data" / "balanced" / f"train_with_corrections_{timestamp}.jsonl"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n💾 Saving merged data to {output_file}")
    save_jsonl(corrected_data, output_file)

    # Backup corrections file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = corrections_file.parent / f"corrections_applied_{timestamp}.jsonl"
    print(f"   Creating backup of corrections: {backup_file}")
    corrections_file.rename(backup_file)

    print(f"\n✅ Done! Merged {total_changes} corrections into training data")
    print(f"   Original corrections backed up to: {backup_file}")

    # Auto-retrain if requested
    if args.auto_retrain:
        print(f"\n🚀 Auto-retrain enabled. Starting model training...")
        import subprocess

        cmd = [
            "python3",
            str(BASE_DIR / "scripts" / "train_model.py"),
            "--train", str(output_file),
            "--val", str(BASE_DIR / "data" / "balanced" / "test_natural.jsonl"),
            "--output", str(BASE_DIR / "models" / f"retrained_{datetime.now().strftime('%Y%m%d')}"),
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(result.stdout)
            print(f"\n✅ Model retrained successfully!")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Retraining failed: {e.stderr}")
            sys.exit(1)
    else:
        print(f"\n📋 Next steps:")
        print(f"   1. Review the merged dataset: {output_file}")
        print(f"   2. Retrain your model:")
        print(f"      python3 scripts/train_model.py \\")
        print(f"        --train {output_file} \\")
        print(f"        --val data/balanced/test_natural.jsonl \\")
        print(f"        --output models/retrained_{datetime.now().strftime('%Y%m%d')}")
        print(f"   3. Deploy the updated model")

    print("=" * 70)


if __name__ == "__main__":
    main()
