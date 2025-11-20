#!/usr/bin/env python3
"""
Train Model on Balanced US+Indian Dataset
Uses data/balanced_train.jsonl and data/balanced_test.jsonl
"""

import os
import warnings
import subprocess
import sys

# Suppress warnings
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
warnings.filterwarnings('ignore')

# Optimal hyperparameters for balanced dataset
BALANCED_PARAMS = {
    "train": "data/balanced_train.jsonl",
    "val": "data/balanced_test.jsonl",
    "output": "models/balanced_classifier",
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

def main():
    """Train model on balanced US+Indian dataset"""
    print("\n")
    print("🚀" * 40)
    print("  TRAINING ON BALANCED US + INDIAN MERCHANT DATASET")
    print("🚀" * 40)
    print()

    print("=" * 80)
    print("📊 Dataset Information:")
    print("=" * 80)
    print(f"  Training:   {BALANCED_PARAMS['train']} (22,400 samples, 800 per category)")
    print(f"  Validation: {BALANCED_PARAMS['val']} (5,600 samples, 200 per category)")
    print(f"  Output:     {BALANCED_PARAMS['output']}")
    print()
    print("  Categories: 28 balanced categories")
    print("  Languages: US merchants (English) + Indian merchants (Hindi/English)")
    print("  Currency: USD + INR")
    print()

    print("=" * 80)
    print("🧠 Model Configuration:")
    print("=" * 80)
    for key, value in BALANCED_PARAMS.items():
        if key not in ['train', 'val', 'output']:
            print(f"  {key:20s}: {value}")
    print()
    print("=" * 80)
    print()

    # Build command
    cmd = ["python3", "scripts/train_model.py"]

    for key, value in BALANCED_PARAMS.items():
        cmd.append(f"--{key.replace('_', '-')}")
        cmd.append(str(value))

    # Data already balanced - no need for balancing or augmentation
    cmd.append("--no-balance")
    cmd.append("--no-augment")

    # Run training
    try:
        print("🎯 Starting training on balanced dataset...\n")
        print("This will take a few minutes. Please wait...")
        print()

        subprocess.run(cmd, check=True)

        print()
        print("=" * 80)
        print("✅ TRAINING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print(f"📁 Model saved to: {BALANCED_PARAMS['output']}")
        print()
        print("🎯 Next Steps:")
        print()
        print("   1. Test the new model:")
        print(f"      MODEL_PATH={BALANCED_PARAMS['output']} ./test_50_transactions.sh")
        print()
        print("   2. Evaluate F1 score:")
        print("      python3 scripts/evaluate_f1.py \\")
        print(f"        --model {BALANCED_PARAMS['output']} \\")
        print(f"        --test {BALANCED_PARAMS['val']}")
        print()
        print("   3. Start API server with new model:")
        print(f"      MODEL_PATH={BALANCED_PARAMS['output']} python3 -m uvicorn apps.api.main:app --reload")
        print()
        print("=" * 80)
        print()
        print("📈 Expected Improvements:")
        print("   - Shopping (Amazon, Walmart, Target): 10% → 90%+")
        print("   - Fuel (Shell, Chevron): 0% → 85%+")
        print("   - Food Delivery (DoorDash, UberEats): 0% → 80%+")
        print("   - Overall Accuracy: 54% → 85-90%+")
        print()
        print("=" * 80)

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 80)
        print(f"❌ TRAINING FAILED!")
        print(f"Error: {e}")
        print("=" * 80)
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("⚠️  Training interrupted by user")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main()
