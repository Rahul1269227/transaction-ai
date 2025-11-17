#!/usr/bin/env python3
"""
Simple Training Script
Trains the transaction categorization model with pre-configured optimal parameters
"""

import subprocess
import sys

# Optimal hyperparameters (pre-configured for best performance)
OPTIMAL_PARAMS = {
    "train": "data/balanced/train.jsonl",
    "val": "data/balanced/test.jsonl",
    "output": "models/transaction_classifier_balanced_final",
    "n_estimators": 500,
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
    """Run training with optimal parameters"""
    print("=" * 70)
    print("🚀 Training Transaction Categorization Model")
    print("=" * 70)
    print()
    print("Using pre-configured optimal hyperparameters:")
    for key, value in OPTIMAL_PARAMS.items():
        if not key.startswith("_"):
            print(f"  {key}: {value}")
    print()
    print("=" * 70)
    print()

    # Build command
    cmd = ["python3", "scripts/train_model.py"]

    for key, value in OPTIMAL_PARAMS.items():
        cmd.append(f"--{key.replace('_', '-')}")
        cmd.append(str(value))

    # Add flags to skip re-balancing/re-augmentation (data is pre-processed)
    cmd.append("--no-balance")
    cmd.append("--no-augment")

    # Run training
    try:
        subprocess.run(cmd, check=True)
        print()
        print("=" * 70)
        print("✅ Training completed successfully!")
        print("=" * 70)
    except subprocess.CalledProcessError as e:
        print(f"❌ Training failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
