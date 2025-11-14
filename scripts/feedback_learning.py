"""
Automatic Feedback Learning System
Continuously learns from user feedback to improve ML and LLM models
"""

import json
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from apps.api.main import FeedbackRecordORM, TransactionRecordORM, Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def export_feedback_to_training_data(
    database_url: str,
    output_path: str,
    min_feedback_count: int = 10
) -> int:
    """
    Export feedback from database to training data format

    Args:
        database_url: Database connection string
        output_path: Path to save training data
        min_feedback_count: Minimum feedback entries to trigger export

    Returns:
        Number of feedback entries exported
    """
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Get all feedback records
        feedback_records = session.query(FeedbackRecordORM).all()

        if len(feedback_records) < min_feedback_count:
            logger.info(f"Only {len(feedback_records)} feedback entries found. Need at least {min_feedback_count} to retrain.")
            return 0

        # Convert to training format
        training_data = []
        for record in feedback_records:
            training_data.append({
                "text": record.transaction_text,
                "category": record.correct_category,
                "subcategory": record.correct_subcategory,
                "amount": float(record.amount) if record.amount else None,
                "date": record.date.isoformat() if record.date else None,
                "source": "feedback"
            })

        # Save to JSONL
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            for item in training_data:
                f.write(json.dumps(item) + '\n')

        logger.info(f"Exported {len(training_data)} feedback entries to {output_path}")
        return len(training_data)

    finally:
        session.close()


def merge_feedback_with_training_data(
    original_data_path: str,
    feedback_data_path: str,
    output_path: str
) -> int:
    """
    Merge feedback data with original training data

    Returns:
        Total number of training samples
    """
    merged_data = []

    # Load original training data
    if Path(original_data_path).exists():
        with open(original_data_path, 'r') as f:
            for line in f:
                merged_data.append(json.loads(line.strip()))
        logger.info(f"Loaded {len(merged_data)} original training samples")

    # Load feedback data
    if Path(feedback_data_path).exists():
        feedback_count = 0
        with open(feedback_data_path, 'r') as f:
            for line in f:
                merged_data.append(json.loads(line.strip()))
                feedback_count += 1
        logger.info(f"Added {feedback_count} feedback samples")

    # Save merged data
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for item in merged_data:
            f.write(json.dumps(item) + '\n')

    logger.info(f"Saved {len(merged_data)} merged training samples to {output_path}")
    return len(merged_data)


def create_few_shot_examples(
    database_url: str,
    output_path: str,
    max_examples: int = 50
) -> int:
    """
    Create few-shot examples for LLM from high-confidence feedback

    Args:
        database_url: Database connection string
        output_path: Path to save few-shot examples
        max_examples: Maximum number of examples to include

    Returns:
        Number of examples created
    """
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Get high-confidence accepted transactions
        from sqlalchemy import and_, desc

        transactions = session.query(TransactionRecordORM).filter(
            and_(
                TransactionRecordORM.confidence >= 0.9,
                TransactionRecordORM.requires_review == False
            )
        ).order_by(desc(TransactionRecordORM.confidence)).limit(max_examples // 2).all()

        # Get corrected feedback
        feedback = session.query(FeedbackRecordORM).filter(
            FeedbackRecordORM.correct_category != FeedbackRecordORM.predicted_category
        ).limit(max_examples // 2).all()

        examples = []

        # Add high-confidence transactions
        for txn in transactions:
            examples.append({
                "text": txn.original_text,
                "category": txn.category,
                "subcategory": txn.subcategory,
                "confidence": float(txn.confidence) if txn.confidence else 0.0
            })

        # Add corrected feedback
        for fb in feedback:
            examples.append({
                "text": fb.transaction_text,
                "category": fb.correct_category,
                "subcategory": fb.correct_subcategory,
                "confidence": 1.0  # Human-verified
            })

        # Save examples
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')

        logger.info(f"Created {len(examples)} few-shot examples at {output_path}")
        return len(examples)

    finally:
        session.close()


def trigger_model_retraining(
    merged_data_path: str,
    model_output_path: str
) -> bool:
    """
    Trigger ML model retraining with merged data

    Returns:
        True if retraining succeeded
    """
    import subprocess

    try:
        logger.info("Starting model retraining...")

        cmd = [
            "python3",
            "scripts/train_model.py",
            "--data", merged_data_path,
            "--output", model_output_path,
            "--taxonomy", "data/taxonomy.yaml"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        if result.returncode == 0:
            logger.info("Model retraining completed successfully")
            return True
        else:
            logger.error(f"Model retraining failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error during retraining: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Automatic Feedback Learning')
    parser.add_argument('--database-url', required=True, help='Database connection URL')
    parser.add_argument('--original-data', default='data/datasets/synthetic_train.jsonl',
                       help='Original training data path')
    parser.add_argument('--min-feedback', type=int, default=10,
                       help='Minimum feedback count to trigger retraining')
    parser.add_argument('--output-dir', default='data/learning',
                       help='Output directory for learning data')
    parser.add_argument('--model-output', default='models/classifier',
                       help='Output path for retrained model')
    parser.add_argument('--few-shot-output', default='data/few_shot_examples.jsonl',
                       help='Output path for few-shot examples')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Export feedback
    feedback_path = output_dir / f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    feedback_count = export_feedback_to_training_data(
        args.database_url,
        str(feedback_path),
        args.min_feedback
    )

    if feedback_count == 0:
        logger.info("Not enough feedback to trigger learning. Exiting.")
        return

    # Step 2: Merge with original data
    merged_path = output_dir / f"merged_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    total_samples = merge_feedback_with_training_data(
        args.original_data,
        str(feedback_path),
        str(merged_path)
    )

    logger.info(f"Total training samples: {total_samples}")

    # Step 3: Create few-shot examples for LLM
    few_shot_count = create_few_shot_examples(
        args.database_url,
        args.few_shot_output,
        max_examples=50
    )

    logger.info(f"Created {few_shot_count} few-shot examples")

    # Step 4: Trigger model retraining
    success = trigger_model_retraining(
        str(merged_path),
        args.model_output
    )

    if success:
        logger.info("✅ Automatic learning completed successfully!")
        logger.info(f"   - {feedback_count} new feedback samples")
        logger.info(f"   - {total_samples} total training samples")
        logger.info(f"   - {few_shot_count} few-shot examples updated")
        logger.info(f"   - Model retrained at {args.model_output}")
    else:
        logger.error("❌ Automatic learning failed during model retraining")


if __name__ == "__main__":
    main()
