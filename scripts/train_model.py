"""
Model Training Script
Train ML classifier on transaction data with enhanced features and data augmentation
"""

import json
import argparse
import logging
import random
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
import sys
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.normalize import TransactionNormalizer, FeatureExtractor
from core.model import EmbeddingClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_jsonl(file_path: str) -> List[Dict]:
    """Load JSONL dataset"""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def augment_text(text: str) -> List[str]:
    """
    Data augmentation: Generate variations of transaction text
    
    Returns:
        List of augmented text variations
    """
    variations = [text]  # Original
    
    # Case variations
    variations.append(text.upper())
    variations.append(text.lower())
    
    # Delimiter variations
    variations.append(text.replace('-', ' '))
    variations.append(text.replace(' ', '-'))
    variations.append(text.replace('/', ' '))
    variations.append(text.replace(' ', '/'))
    
    # Remove/add spaces
    variations.append(text.replace(' ', ''))
    variations.append(text.replace('-', ' '))
    
    # Remove duplicates and return
    return list(set(variations))[:5]  # Limit to 5 variations


def balance_dataset(dataset: List[Dict], min_samples_per_category: int = 100) -> List[Dict]:
    """
    Balance dataset by oversampling minority categories
    
    Args:
        dataset: Original dataset
        min_samples_per_category: Minimum samples per category
        
    Returns:
        Balanced dataset
    """
    # Count samples per category
    category_counts = Counter([item['label'] for item in dataset])
    max_count = max(category_counts.values())
    target_count = max(min_samples_per_category, int(max_count * 0.8))
    
    balanced = []
    
    for category, count in category_counts.items():
        category_samples = [item for item in dataset if item['label'] == category]
        balanced.extend(category_samples)
        
        # Oversample if needed
        if count < target_count:
            needed = target_count - count
            # Use augmentation for oversampling
            augmented = []
            for _ in range(needed):
                sample = random.choice(category_samples)
                # Create variation
                variation = sample.copy()
                variation['text'] = random.choice(augment_text(sample['text']))
                augmented.append(variation)
            balanced.extend(augmented)
    
    # Shuffle
    random.shuffle(balanced)
    
    logger.info(f"Balanced dataset: {len(dataset)} -> {len(balanced)} samples")
    logger.info(f"Category distribution after balancing:")
    balanced_counts = Counter([item['label'] for item in balanced])
    for cat, count in sorted(balanced_counts.items()):
        logger.info(f"  {cat}: {count}")
    
    return balanced


def prepare_training_data(dataset: List[Dict], augment: bool = False):
    """
    Prepare training data with optional augmentation

    Returns:
        texts, labels, handcrafted_features
    """
    normalizer = TransactionNormalizer()
    feature_extractor = FeatureExtractor()

    texts = []
    labels = []
    handcrafted_features = []

    for item in dataset:
        # Normalize
        normalized = normalizer.normalize(
            text=item['text'],
            amount=item.get('amount'),
            date=item.get('date'),
            currency=item.get('currency', 'INR')
        )

        # Extract features
        features = feature_extractor.extract_features(normalized)

        # Use search text for embedding
        texts.append(normalized['search_text'])
        labels.append(item['label'])
        handcrafted_features.append(features)
        
        # Augment if requested
        if augment and random.random() < 0.3:  # 30% augmentation rate
            variations = augment_text(item['text'])
            for var_text in variations[1:]:  # Skip original
                var_normalized = normalizer.normalize(
                    text=var_text,
                    amount=item.get('amount'),
                    date=item.get('date'),
                    currency=item.get('currency', 'INR')
                )
                var_features = feature_extractor.extract_features(var_normalized)
                texts.append(var_normalized['search_text'])
                labels.append(item['label'])
                handcrafted_features.append(var_features)

    return texts, labels, handcrafted_features


def train_classifier(
    train_path: str,
    val_path: str,
    output_path: str,
    encoder_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    n_estimators: int = 200,
    learning_rate: float = 0.05,
    max_depth: int = 10,
    balance: bool = True,
    augment: bool = True,
    num_leaves: int = 50,
    min_child_samples: int = 20,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    reg_alpha: float = 0.1,
    reg_lambda: float = 0.1,
    class_weights_path: str = None
):
    """
    Train classifier with enhanced hyperparameters

    Args:
        train_path: Path to training JSONL
        val_path: Path to validation JSONL
        output_path: Path to save trained model
        encoder_model: Sentence transformer model name
        n_estimators: Number of boosting rounds (increased from 100)
        learning_rate: Learning rate (decreased from 0.1 for better convergence)
        max_depth: Max tree depth (increased from 7)
        balance: Whether to balance dataset
        augment: Whether to augment training data
        num_leaves: Number of leaves (increased from 31)
        min_child_samples: Minimum samples per leaf
        subsample: Row subsampling ratio
        colsample_bytree: Column subsampling ratio
        reg_alpha: L1 regularization
        reg_lambda: L2 regularization
    """
    logger.info("Loading datasets...")

    # Load datasets
    train_data = load_jsonl(train_path)
    val_data = load_jsonl(val_path)

    # Load class weights if provided
    class_weights = None
    if class_weights_path:
        logger.info(f"Loading class weights from {class_weights_path}")
        with open(class_weights_path, 'r') as f:
            class_weights = json.load(f)
        logger.info("Class weights loaded successfully")

    logger.info(f"Training samples: {len(train_data)}")
    logger.info(f"Validation samples: {len(val_data)}")

    # Balance dataset if requested
    if balance:
        logger.info("Balancing dataset...")
        train_data = balance_dataset(train_data, min_samples_per_category=100)

    # Prepare training data
    logger.info("Preparing training data...")
    train_texts, train_labels, train_features = prepare_training_data(
        train_data, 
        augment=augment
    )
    
    logger.info(f"Training samples after augmentation: {len(train_texts)}")

    logger.info("Preparing validation data...")
    val_texts, val_labels, val_features = prepare_training_data(val_data, augment=False)

    # Initialize classifier
    logger.info(f"Initializing classifier with encoder: {encoder_model}")
    classifier = EmbeddingClassifier(
        encoder_model=encoder_model,
        classifier_type='lightgbm'
    )

    # Train with enhanced hyperparameters
    logger.info("Training classifier with enhanced hyperparameters...")
    logger.info(f"  n_estimators: {n_estimators}")
    logger.info(f"  learning_rate: {learning_rate}")
    logger.info(f"  max_depth: {max_depth}")
    logger.info(f"  num_leaves: {num_leaves}")
    logger.info(f"  regularization: L1={reg_alpha}, L2={reg_lambda}")
    if class_weights:
        logger.info(f"  Using custom class weights")

    classifier.train(
        texts=train_texts,
        labels=train_labels,
        handcrafted_features=train_features,
        calibrate=True,
        class_weights=class_weights,
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        num_leaves=num_leaves,
        min_child_samples=min_child_samples,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        reg_alpha=reg_alpha,
        reg_lambda=reg_lambda
    )

    # Evaluate on validation set
    logger.info("Evaluating on validation set...")
    predictions = classifier.predict(val_texts, val_features, top_k=1)

    # Calculate accuracy
    correct = 0
    for i, pred_list in enumerate(predictions):
        pred_cat, _ = pred_list[0]  # Get first prediction (top-1)
        if pred_cat == val_labels[i]:
            correct += 1

    accuracy = correct / len(val_labels)
    logger.info(f"Validation Accuracy: {accuracy:.4f}")

    # Calculate per-category accuracy
    category_correct = {}
    category_total = {}

    for i, pred_list in enumerate(predictions):
        pred_cat, _ = pred_list[0]  # Get first prediction (top-1)
        true_cat = val_labels[i]

        if true_cat not in category_total:
            category_total[true_cat] = 0
            category_correct[true_cat] = 0

        category_total[true_cat] += 1
        if pred_cat == true_cat:
            category_correct[true_cat] += 1

    logger.info("\nPer-category accuracy:")
    for cat in sorted(category_total.keys()):
        cat_acc = category_correct[cat] / category_total[cat]
        logger.info(f"  {cat}: {cat_acc:.4f} ({category_correct[cat]}/{category_total[cat]})")

    # Get feature importance
    logger.info("\nTop 20 most important features:")
    importance = classifier.get_feature_importance(top_n=20)
    for feat, imp in importance:
        logger.info(f"  {feat}: {imp:.6f}")

    # Save model
    logger.info(f"\nSaving model to {output_path}")
    classifier.save(output_path)

    logger.info("Training complete!")

    return {
        'accuracy': accuracy,
        'train_samples': len(train_data),
        'val_samples': len(val_data),
        'num_categories': len(set(train_labels))
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Train transaction categorization model')
    parser.add_argument('--train', type=str, required=True, help='Path to training JSONL')
    parser.add_argument('--val', type=str, required=True, help='Path to validation JSONL')
    parser.add_argument('--output', type=str, required=True, help='Path to save model')
    parser.add_argument('--encoder', type=str, default='sentence-transformers/all-MiniLM-L6-v2',
                       help='Encoder model name')
    parser.add_argument('--n-estimators', type=int, default=200, help='Number of estimators')
    parser.add_argument('--learning-rate', type=float, default=0.05, help='Learning rate')
    parser.add_argument('--max-depth', type=int, default=10, help='Max tree depth')
    parser.add_argument('--num-leaves', type=int, default=50, help='Number of leaves')
    parser.add_argument('--min-child-samples', type=int, default=20, help='Min child samples')
    parser.add_argument('--subsample', type=float, default=0.8, help='Row subsampling ratio')
    parser.add_argument('--colsample-bytree', type=float, default=0.8, help='Column subsampling ratio')
    parser.add_argument('--reg-alpha', type=float, default=0.1, help='L1 regularization')
    parser.add_argument('--reg-lambda', type=float, default=0.1, help='L2 regularization')
    parser.add_argument('--no-balance', action='store_true', help='Disable dataset balancing')
    parser.add_argument('--no-augment', action='store_true', help='Disable data augmentation')
    parser.add_argument('--class-weights', type=str, default=None, help='Path to class weights JSON file')

    args = parser.parse_args()

    # Train model
    metrics = train_classifier(
        train_path=args.train,
        val_path=args.val,
        output_path=args.output,
        encoder_model=args.encoder,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth,
        balance=not args.no_balance,
        augment=not args.no_augment,
        num_leaves=args.num_leaves,
        min_child_samples=args.min_child_samples,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        reg_alpha=args.reg_alpha,
        reg_lambda=args.reg_lambda,
        class_weights_path=args.class_weights
    )

    # Save metrics
    metrics_file = Path(args.output) / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {metrics_file}")


if __name__ == '__main__':
    main()
