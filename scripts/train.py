#!/usr/bin/env python3
"""
Simple Training Script - Uses Final Balanced Dataset
Train LightGBM model on clean, balanced data (data/train.jsonl & data/test.jsonl)
"""

import os
import warnings
import subprocess
import sys

# Suppress warnings
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
warnings.filterwarnings('ignore')

# Optimal hyperparameters
OPTIMAL_PARAMS = {
    "train": "data/train.jsonl",
    "val": "data/test.jsonl",
    "output": "models/transaction_classifier",
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
    """Train model on balanced dataset"""
    print("\n")
    print("🚀" * 35)
    print("🚀  TRANSACTION CLASSIFIER - TRAINING ON BALANCED DATA  🚀")
    print("🚀" * 35)
    print()

    print("=" * 70)
    print("📊 Dataset:")
    print("=" * 70)
    print(f"  Training:   {OPTIMAL_PARAMS['train']}")
    print(f"  Validation: {OPTIMAL_PARAMS['val']}")
    print(f"  Output:     {OPTIMAL_PARAMS['output']}")
    print()

    print("=" * 70)
    print("🧠 Model Hyperparameters:")
    print("=" * 70)
    for key, value in OPTIMAL_PARAMS.items():
        if key not in ['train', 'val', 'output']:
            print(f"  {key:20s}: {value}")
    print()
    print("=" * 70)
    print()

    # Build command
    cmd = ["python3", "scripts/train_model.py"]

    for key, value in OPTIMAL_PARAMS.items():
        cmd.append(f"--{key.replace('_', '-')}")
        cmd.append(str(value))

    # No balancing or augmentation (data already balanced)
    cmd.append("--no-balance")
    cmd.append("--no-augment")

    # Run training
    try:
        print("🎯 Starting training...\n")
        subprocess.run(cmd, check=True)

        print()
        print("=" * 70)
        print("✅ TRAINING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"📁 Model saved to: {OPTIMAL_PARAMS['output']}")
        print()
        print("🎯 Next Steps:")
        print("   1. Evaluate F1 score:")
        print("      python3 scripts/evaluate_f1.py \\")
        print(f"        --model {OPTIMAL_PARAMS['output']} \\")
        print(f"        --test {OPTIMAL_PARAMS['val']}")
        print()
        print("   2. Start API server:")
        print(f"      MODEL_PATH={OPTIMAL_PARAMS['output']} python3 -m uvicorn apps.api.main:app --reload")
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
