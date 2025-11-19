#!/usr/bin/env python3
"""
Comprehensive Training Script
Automatically merges all data sources (synthetic, Kaggle, balanced) and trains the model
Just run: python3 scripts/train.py
"""

import os
import warnings

# Suppress warnings
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*OpenSSL.*')

import subprocess
import sys
import json
import random
import yaml
import csv
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# Optimal hyperparameters (pre-configured for best performance)
# NOTE: Always using 'transaction_classifier_balanced_final' as model name
# This ensures .env and docker-compose don't need to be updated
OPTIMAL_PARAMS = {
    "output": "models/transaction_classifier_balanced_final",  # Always use this name
    "n_estimators": 200,
    "learning_rate": 0.05,
    "max_depth": 10,
    "num_leaves": 50,
    "min_child_samples": 20,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 0.1,
}

def load_jsonl(file_path):
    """Load JSONL file"""
    if not Path(file_path).exists():
        return []

    data = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except:
                pass
    return data

def save_jsonl(data, file_path):
    """Save to JSONL file"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def load_config():
    """Load training configuration"""
    config_path = Path("config/training_config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}

def load_and_apply_corrections(train_data, test_data):
    """
    Load corrections and apply them to training data.

    Strategy:
    1. Load all corrections from corrections.jsonl
    2. Update existing samples if text matches (relabel)
    3. Add new samples for unique corrections
    4. Return enhanced training data
    """
    config = load_config()
    corrections_file = config.get('data', {}).get('corrections_file', 'data/corrections/corrections.jsonl')

    if not Path(corrections_file).exists():
        print("ℹ️  No corrections file found, skipping correction integration")
        return train_data, test_data, 0

    corrections = load_jsonl(corrections_file)
    if not corrections:
        print("ℹ️  No corrections found, skipping correction integration")
        return train_data, test_data, 0

    print(f"\n📝 Applying {len(corrections)} user corrections...")

    # Build correction map: text -> correct category
    correction_map = {}
    unique_corrections = []

    for corr in corrections:
        text = corr.get('transaction_text', '').strip().lower()
        correct_cat = corr.get('correct_category')

        if text and correct_cat:
            correction_map[text] = correct_cat
            unique_corrections.append({
                'text': corr.get('transaction_text', ''),
                'label': correct_cat,
                'amount': corr.get('amount'),
                'date': corr.get('date'),
            })

    # Apply corrections to existing training data
    relabeled_count = 0
    for item in train_data:
        item_text = item.get('text', '').strip().lower()
        if item_text in correction_map:
            old_label = item.get('label', item.get('category'))
            new_label = correction_map[item_text]
            if old_label != new_label:
                item['label'] = new_label
                if 'category' in item:
                    item['category'] = new_label
                relabeled_count += 1

    # Add unique corrections as new samples (if not already in training data)
    existing_texts = {item.get('text', '').strip().lower() for item in train_data}
    new_samples = [corr for corr in unique_corrections
                   if corr['text'].strip().lower() not in existing_texts]

    if new_samples:
        train_data.extend(new_samples)

    print(f"   ✓ Relabeled {relabeled_count} existing samples")
    print(f"   ✓ Added {len(new_samples)} new samples from corrections")
    print(f"   ✓ Total corrections applied: {relabeled_count + len(new_samples)}")

    return train_data, test_data, len(corrections)

def extract_merchant_from_text(text):
    """Extract potential merchant name from transaction text"""
    # Remove common transaction keywords
    clean = re.sub(r'\b(purchase|payment|transaction|from|to|at|via|ref|refund|return)\b', '', text, flags=re.IGNORECASE)
    # Remove numbers, special chars
    clean = re.sub(r'[0-9#\-/\\*]+', '', clean)
    clean = clean.strip()
    # Return first meaningful token (usually merchant name)
    tokens = [t.strip() for t in clean.split() if len(t.strip()) > 2]
    return tokens[0] if tokens else None

def learn_merchants_from_corrections():
    """Learn merchant patterns from corrections and update gazetteer"""
    config = load_config()
    corrections_file = config.get('data', {}).get('corrections_file', 'data/corrections/corrections.jsonl')
    gazetteer_file = config.get('data', {}).get('gazetteer_file', 'data/gazetteer/merchant_aliases.csv')
    min_occurrences = config.get('corrections', {}).get('min_merchant_occurrences', 2)

    if not Path(corrections_file).exists():
        print("ℹ️  No corrections file found, skipping merchant learning")
        return 0

    corrections = load_jsonl(corrections_file)
    if not corrections:
        print("ℹ️  No corrections found, skipping merchant learning")
        return 0

    print(f"\n🏪 Learning merchants from {len(corrections)} corrections...")

    # Count merchant -> category mappings
    merchant_categories = defaultdict(Counter)

    for corr in corrections:
        text = corr.get('transaction_text', '')
        category = corr.get('correct_category')

        if text and category:
            merchant = extract_merchant_from_text(text)
            if merchant and len(merchant) >= 3:
                merchant_categories[merchant.lower()][category] += 1

    # Load existing gazetteer
    existing_merchants = set()
    if Path(gazetteer_file).exists():
        try:
            with open(gazetteer_file, 'r') as f:
                reader = csv.DictReader(f)
                existing_merchants = {row['merchant'].lower() for row in reader if 'merchant' in row}
        except:
            pass

    # Find merchants with enough occurrences
    new_merchants = []
    for merchant, cat_counts in merchant_categories.items():
        total_count = sum(cat_counts.values())
        if total_count >= min_occurrences and merchant not in existing_merchants:
            # Use most common category for this merchant
            most_common_cat = cat_counts.most_common(1)[0][0]
            new_merchants.append({
                'merchant': merchant.title(),
                'category': most_common_cat,
                'count': total_count
            })

    if new_merchants:
        # Append to gazetteer
        Path(gazetteer_file).parent.mkdir(parents=True, exist_ok=True)
        file_exists = Path(gazetteer_file).exists()

        with open(gazetteer_file, 'a', newline='') as f:
            fieldnames = ['merchant', 'category', 'aliases']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            for merch in new_merchants:
                writer.writerow({
                    'merchant': merch['merchant'],
                    'category': merch['category'],
                    'aliases': ''
                })

        print(f"   ✓ Added {len(new_merchants)} new merchants to gazetteer")
        return len(new_merchants)
    else:
        print(f"   ℹ️  No new merchants to add (min occurrences: {min_occurrences})")
        return 0

def generate_few_shot_examples_from_corrections():
    """Generate few-shot examples for LLM from high-quality corrections"""
    config = load_config()
    corrections_file = config.get('data', {}).get('corrections_file', 'data/corrections/corrections.jsonl')
    few_shot_file = config.get('data', {}).get('few_shot_file', 'data/few_shot_examples.jsonl')
    max_per_category = config.get('few_shot', {}).get('max_examples_per_category', 5)
    min_for_few_shot = config.get('few_shot', {}).get('min_corrections_for_few_shot', 3)

    if not Path(corrections_file).exists():
        print("ℹ️  No corrections file found, skipping few-shot generation")
        return 0

    corrections = load_jsonl(corrections_file)
    if not corrections:
        print("ℹ️  No corrections found, skipping few-shot generation")
        return 0

    print(f"\n🎯 Generating few-shot examples from corrections...")

    # Group corrections by category
    by_category = defaultdict(list)

    for corr in corrections:
        text = corr.get('transaction_text', '')
        category = corr.get('correct_category')
        predicted = corr.get('predicted_category')

        if text and category:
            # Prefer corrections with high confidence delta (model was wrong)
            confidence_delta = 1.0 if predicted != category else 0.5
            by_category[category].append({
                'text': text,
                'category': category,
                'priority': confidence_delta
            })

    # Load existing few-shot examples
    existing_examples = []
    if Path(few_shot_file).exists():
        existing_examples = load_jsonl(few_shot_file)

    existing_texts = {ex.get('text', '').strip().lower() for ex in existing_examples}

    # Select best examples per category
    new_examples = []
    for category, examples in by_category.items():
        if len(examples) >= min_for_few_shot:
            # Sort by priority (wrong predictions first)
            examples.sort(key=lambda x: x['priority'], reverse=True)

            # Take top N unique examples
            added = 0
            for ex in examples:
                if ex['text'].strip().lower() not in existing_texts and added < max_per_category:
                    new_examples.append({
                        'text': ex['text'],
                        'category': ex['category']
                    })
                    existing_texts.add(ex['text'].strip().lower())
                    added += 1

    if new_examples:
        # Append to few-shot file
        all_examples = existing_examples + new_examples
        save_jsonl(all_examples, few_shot_file)
        print(f"   ✓ Added {len(new_examples)} new few-shot examples")
        print(f"   ✓ Total few-shot examples: {len(all_examples)}")
        return len(new_examples)
    else:
        print(f"   ℹ️  No new few-shot examples to add (min per category: {min_for_few_shot})")
        return 0

def merge_all_data_sources():
    """
    Merge all available data sources:
    1. Original balanced data
    2. Synthetic new categories data
    3. Real Kaggle extracted data
    """
    print("=" * 70)
    print("📊 Merging All Data Sources")
    print("=" * 70)
    print()

    all_train = []
    all_test = []

    # 1. Load original balanced data (CONSOLIDATED)
    print("1. Loading original balanced data (consolidated)...")
    balanced_train = load_jsonl("data/balanced/train_consolidated.jsonl")
    balanced_test = load_jsonl("data/balanced/test_consolidated.jsonl")

    if balanced_train:
        all_train.extend(balanced_train)
        print(f"   ✓ Loaded {len(balanced_train)} training samples")
    if balanced_test:
        all_test.extend(balanced_test)
        print(f"   ✓ Loaded {len(balanced_test)} test samples")

    # 2. Load synthetic new categories data (CONSOLIDATED)
    print("\n2. Loading synthetic new categories data (consolidated)...")
    synth_train = load_jsonl("data/synthetic_new_categories/train_consolidated.jsonl")
    synth_val = load_jsonl("data/synthetic_new_categories/val.jsonl")

    if synth_train:
        all_train.extend(synth_train)
        print(f"   ✓ Loaded {len(synth_train)} synthetic training samples")
    if synth_val:
        all_test.extend(synth_val)
        print(f"   ✓ Loaded {len(synth_val)} synthetic validation samples")

    # 3. Load and split Kaggle data
    print("\n3. Loading real Kaggle extracted data...")
    kaggle_data = load_jsonl("data/kaggle_new_categories/extracted_transactions.jsonl")

    if kaggle_data:
        # Shuffle and split 80/20
        random.seed(42)
        random.shuffle(kaggle_data)
        split_idx = int(len(kaggle_data) * 0.8)
        kaggle_train = kaggle_data[:split_idx]
        kaggle_test = kaggle_data[split_idx:]

        all_train.extend(kaggle_train)
        all_test.extend(kaggle_test)
        print(f"   ✓ Loaded {len(kaggle_train)} Kaggle training samples")
        print(f"   ✓ Loaded {len(kaggle_test)} Kaggle test samples")

    # 4. Load improved weak categories data (CONSOLIDATED)
    print("\n4. Loading improved weak categories data (consolidated)...")
    improved_train = load_jsonl("data/improved_weak_categories/train_consolidated.jsonl")
    improved_test = load_jsonl("data/improved_weak_categories/test_consolidated.jsonl")

    if improved_train:
        all_train.extend(improved_train)
        print(f"   ✓ Loaded {len(improved_train)} improved training samples")
    if improved_test:
        all_test.extend(improved_test)
        print(f"   ✓ Loaded {len(improved_test)} improved test samples")

    # 5. SKIP balanced Kaggle dataset - contains generic company names, not real transactions
    print("\n5. Skipping balanced Kaggle dataset (contains generic placeholders, not real transactions)...")
    print("   ⏭️  This dataset was causing confusion with generic company names")
    # balanced_kaggle_train = load_jsonl("data/balanced_kaggle/train_consolidated.jsonl")
    # balanced_kaggle_test = load_jsonl("data/balanced_kaggle/test_consolidated.jsonl")

    # 6. Apply user corrections
    all_train, all_test, correction_count = load_and_apply_corrections(all_train, all_test)

    # 7. Learn merchants from corrections
    merchant_count = learn_merchants_from_corrections()

    # 8. Generate few-shot examples from corrections
    few_shot_count = generate_few_shot_examples_from_corrections()

    # Summary
    print("\n" + "=" * 70)
    print(f"📈 Total Dataset Size:")
    print(f"   Training:   {len(all_train):,} samples")
    print(f"   Validation: {len(all_test):,} samples")
    print(f"   Total:      {len(all_train) + len(all_test):,} samples")
    print("=" * 70)

    # Show category distribution
    train_labels = [item.get('label', item.get('category', '')) for item in all_train]
    label_counts = Counter(train_labels)

    print(f"\n📊 Category Distribution ({len(label_counts)} categories):")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {label:30s}: {count:,}")
    if len(label_counts) > 10:
        print(f"   ... and {len(label_counts) - 10} more categories")
    print("=" * 70)
    print()

    # Save merged data
    merged_train_path = "data/balanced/train_merged_all.jsonl"
    merged_test_path = "data/balanced/test_merged_all.jsonl"

    print(f"💾 Saving merged datasets...")
    save_jsonl(all_train, merged_train_path)
    save_jsonl(all_test, merged_test_path)
    print(f"   ✓ Saved: {merged_train_path}")
    print(f"   ✓ Saved: {merged_test_path}")
    print()

    return merged_train_path, merged_test_path

def main():
    """Run complete training pipeline"""
    print("\n")
    print("🚀" * 35)
    print("🚀  TRANSACTION CATEGORIZATION MODEL - COMPLETE TRAINING  🚀")
    print("🚀" * 35)
    print()

    # Step 1: Merge all data sources
    train_path, test_path = merge_all_data_sources()

    # Step 2: Train model
    print("=" * 70)
    print("🧠 Training Model with Enhanced Dataset")
    print("=" * 70)
    print()
    print("Hyperparameters:")
    for key, value in OPTIMAL_PARAMS.items():
        if key != 'output':
            print(f"  {key:20s}: {value}")
    print()
    print("=" * 70)
    print()

    # Build command
    cmd = [
        "python3", "scripts/train_model.py",
        "--train", train_path,
        "--val", test_path,
    ]

    for key, value in OPTIMAL_PARAMS.items():
        cmd.append(f"--{key.replace('_', '-')}")
        cmd.append(str(value))

    # Add class weights if available
    class_weights_path = "data/balanced/class_weights.json"
    if Path(class_weights_path).exists():
        cmd.extend(["--class-weights", class_weights_path])
        print("ℹ️  Using custom class weights")
        print()

    # ENABLE balancing to handle class imbalance
    # Note: Augmentation is disabled to avoid overfitting, but balancing is enabled
    # to ensure minority categories (like Bills, subscriptions_memberships) are learned properly
    cmd.append("--no-augment")
    # Removed: cmd.append("--no-balance")  # Let the model balance the dataset

    # Run training
    try:
        subprocess.run(cmd, check=True)
        print()
        print("=" * 70)
        print("✅ TRAINING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"📁 Model saved to: {OPTIMAL_PARAMS['output']}")
        print()
        print("🎯 Next Steps:")
        print("   1. Test the model: python3 scripts/evaluate_model.py")
        print("   2. Start API server: MODEL_PATH=models/transaction_classifier_balanced_final \\")
        print("                        python3 -m uvicorn apps.api.main:app --reload")
        print("   3. Test new categories: ./test_new_categories.sh")
        print()
        print("=" * 70)
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 70)
        print(f"❌ TRAINING FAILED!")
        print(f"Error: {e}")
        print("=" * 70)
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("⚠️  Training interrupted by user")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
