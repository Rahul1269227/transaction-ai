"""
Model Training Script
Train ML classifier on transaction data
"""

import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict
import sys

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


def prepare_training_data(dataset: List[Dict]):
    """
    Prepare training data

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

    return texts, labels, handcrafted_features


def train_classifier(
    train_path: str,
    val_path: str,
    output_path: str,
    encoder_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    n_estimators: int = 100,
    learning_rate: float = 0.1,
    max_depth: int = 7
):
    """
    Train classifier

    Args:
        train_path: Path to training JSONL
        val_path: Path to validation JSONL
        output_path: Path to save trained model
        encoder_model: Sentence transformer model name
        n_estimators: Number of boosting rounds
        learning_rate: Learning rate
        max_depth: Max tree depth
    """
    logger.info("Loading datasets...")

    # Load datasets
    train_data = load_jsonl(train_path)
    val_data = load_jsonl(val_path)

    logger.info(f"Training samples: {len(train_data)}")
    logger.info(f"Validation samples: {len(val_data)}")

    # Prepare training data
    logger.info("Preparing training data...")
    train_texts, train_labels, train_features = prepare_training_data(train_data)

    logger.info("Preparing validation data...")
    val_texts, val_labels, val_features = prepare_training_data(val_data)

    # Initialize classifier
    logger.info(f"Initializing classifier with encoder: {encoder_model}")
    classifier = EmbeddingClassifier(
        encoder_model=encoder_model,
        classifier_type='lightgbm'
    )

    # Train
    logger.info("Training classifier...")
    classifier.train(
        texts=train_texts,
        labels=train_labels,
        handcrafted_features=train_features,
        calibrate=True,
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth
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
    parser.add_argument('--n-estimators', type=int, default=100, help='Number of estimators')
    parser.add_argument('--learning-rate', type=float, default=0.1, help='Learning rate')
    parser.add_argument('--max-depth', type=int, default=7, help='Max tree depth')

    args = parser.parse_args()

    # Train model
    metrics = train_classifier(
        train_path=args.train,
        val_path=args.val,
        output_path=args.output,
        encoder_model=args.encoder,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth
    )

    # Save metrics
    metrics_file = Path(args.output) / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {metrics_file}")


if __name__ == '__main__':
    main()
