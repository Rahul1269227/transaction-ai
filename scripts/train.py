#!/usr/bin/env python3
"""
Comprehensive Training Script
Automatically merges all data sources (synthetic, Kaggle, balanced) and trains the model
Just run: python3 scripts/train.py
"""

import subprocess
import sys
import json
import random
from pathlib import Path
from collections import Counter

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
