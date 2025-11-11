"""
Evaluation Runner
Comprehensive evaluation of transaction categorization system
"""

import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.model import HybridRouter
from core.normalize import TransactionNormalizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvaluationRunner:
    """Evaluate categorization system"""

    def __init__(self, router: HybridRouter):
        """
        Initialize evaluator

        Args:
            router: Hybrid router instance
        """
        self.router = router

    def load_dataset(self, file_path: str) -> List[Dict]:
        """Load JSONL dataset"""
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                data.append(json.loads(line.strip()))
        return data

    def evaluate(self, test_data: List[Dict]) -> Dict:
        """
        Evaluate system on test data

        Args:
            test_data: List of test transactions

        Returns:
            Dict with evaluation metrics
        """
        logger.info(f"Evaluating on {len(test_data)} samples...")

        # Track predictions and ground truth
        predictions = []
        ground_truth = []
        confidences = []
        requires_review = []

        # Per-category metrics
        category_correct = defaultdict(int)
        category_total = defaultdict(int)

        # Per-method metrics
        method_correct = defaultdict(int)
        method_total = defaultdict(int)

        # Confusion matrix
        confusion = defaultdict(lambda: defaultdict(int))

        for item in test_data:
            # Get ground truth
            true_category = item['label']
            ground_truth.append(true_category)
            category_total[true_category] += 1

            # Predict
            result = self.router.categorize(
                text=item['text'],
                amount=item.get('amount'),
                date=item.get('date'),
                currency=item.get('currency', 'INR')
            )

            pred_category = result.category
            predictions.append(pred_category)
            confidences.append(result.confidence)
            requires_review.append(result.requires_review)

            # Update metrics
            if pred_category == true_category:
                category_correct[true_category] += 1
                method_correct[result.method] += 1

            method_total[result.method] += 1

            # Update confusion matrix
            confusion[true_category][pred_category] += 1

        # Calculate overall metrics
        accuracy = sum(1 for p, g in zip(predictions, ground_truth) if p == g) / len(predictions)
        avg_confidence = sum(confidences) / len(confidences)
        review_rate = sum(requires_review) / len(requires_review)

        # Calculate per-category metrics
        category_metrics = {}
        for cat in category_total:
            cat_accuracy = category_correct[cat] / category_total[cat]
            category_metrics[cat] = {
                'accuracy': cat_accuracy,
                'correct': category_correct[cat],
                'total': category_total[cat]
            }

        # Calculate per-method metrics
        method_metrics = {}
        for method in method_total:
            method_accuracy = method_correct[method] / method_total[method]
            method_metrics[method] = {
                'accuracy': method_accuracy,
                'correct': method_correct[method],
                'total': method_total[method]
            }

        # Find top confusions
        top_confusions = []
        for true_cat in confusion:
            for pred_cat in confusion[true_cat]:
                if true_cat != pred_cat:
                    count = confusion[true_cat][pred_cat]
                    top_confusions.append((true_cat, pred_cat, count))

        top_confusions = sorted(top_confusions, key=lambda x: -x[2])[:10]

        return {
            'overall': {
                'accuracy': accuracy,
                'avg_confidence': avg_confidence,
                'review_rate': review_rate,
                'total_samples': len(test_data)
            },
            'by_category': category_metrics,
            'by_method': method_metrics,
            'confusion_matrix': dict(confusion),
            'top_confusions': [
                {'true': t, 'pred': p, 'count': c}
                for t, p, c in top_confusions
            ]
        }

    def print_report(self, metrics: Dict):
        """Print evaluation report"""
        print("\n" + "=" * 60)
        print("EVALUATION REPORT")
        print("=" * 60)

        # Overall metrics
        overall = metrics['overall']
        print(f"\nOverall Metrics:")
        print(f"  Accuracy: {overall['accuracy']:.4f}")
        print(f"  Avg Confidence: {overall['avg_confidence']:.4f}")
        print(f"  Review Rate: {overall['review_rate']:.2%}")
        print(f"  Total Samples: {overall['total_samples']}")

        # Per-category metrics
        print(f"\nPer-Category Accuracy:")
        by_cat = metrics['by_category']
        for cat in sorted(by_cat.keys(), key=lambda k: by_cat[k]['accuracy'], reverse=True):
            cat_metrics = by_cat[cat]
            print(f"  {cat:30s}: {cat_metrics['accuracy']:.4f} ({cat_metrics['correct']}/{cat_metrics['total']})")

        # Per-method metrics
        print(f"\nPer-Method Accuracy:")
        by_method = metrics['by_method']
        for method in sorted(by_method.keys()):
            method_metrics = by_method[method]
            print(f"  {method:20s}: {method_metrics['accuracy']:.4f} ({method_metrics['correct']}/{method_metrics['total']})")

        # Top confusions
        print(f"\nTop 10 Confusions:")
        for conf in metrics['top_confusions']:
            print(f"  {conf['true']:30s} -> {conf['pred']:30s}: {conf['count']}")

        print("\n" + "=" * 60)

    def save_report(self, metrics: Dict, output_path: str):
        """Save evaluation report to file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Report saved to {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Evaluate transaction categorization system')
    parser.add_argument('--test', type=str, required=True, help='Path to test JSONL')
    parser.add_argument('--taxonomy', type=str, default='data/taxonomy.yaml', help='Taxonomy file')
    parser.add_argument('--gazetteer', type=str, default='data/gazetteer/merchant_aliases.csv', help='Gazetteer file')
    parser.add_argument('--model', type=str, default=None, help='Path to trained model (optional)')
    parser.add_argument('--output', type=str, default='evals/reports/evaluation_report.json', help='Output report path')

    args = parser.parse_args()

    # Initialize router
    logger.info("Initializing router...")
    router = HybridRouter(
        taxonomy_path=args.taxonomy,
        gazetteer_path=args.gazetteer,
        model_path=args.model,
        auto_accept_threshold=0.85,
        review_threshold=0.60
    )

    # Initialize evaluator
    evaluator = EvaluationRunner(router)

    # Load test data
    logger.info(f"Loading test data from {args.test}")
    test_data = evaluator.load_dataset(args.test)

    # Run evaluation
    metrics = evaluator.evaluate(test_data)

    # Print report
    evaluator.print_report(metrics)

    # Save report
    evaluator.save_report(metrics, args.output)

    logger.info("Evaluation complete!")


if __name__ == '__main__':
    main()
