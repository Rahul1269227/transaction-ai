"""
Evaluate F1 Score for Trained Model
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.model.classifier import EmbeddingClassifier
from core.normalize import TransactionNormalizer, FeatureExtractor
import json
from sklearn.metrics import classification_report, f1_score, accuracy_score
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, help='Path to trained model')
    parser.add_argument('--test', required=True, help='Path to test data (JSONL)')
    args = parser.parse_args()

    # Load model
    print(f'Loading model from {args.model}...')
    model = EmbeddingClassifier()
    model.load(args.model)

    # Load test data
    print(f'Loading test data from {args.test}...')
    test_data = []
    with open(args.test, 'r') as f:
        for line in f:
            test_data.append(json.loads(line))

    print(f'Loaded {len(test_data)} test samples\n')

    # Initialize normalizer and feature extractor
    normalizer = TransactionNormalizer()

    # Prepare data
    texts = []
    handcrafted_features = []
    true_labels = []

    for item in test_data:
        # Normalize transaction
        normalized = normalizer.normalize(
            text=item['text'],
            amount=item.get('amount', 0.0),
            date=item.get('date', '2025-01-01')
        )

        # Extract features
        features = FeatureExtractor.extract_features(normalized)

        texts.append(item['text'])
        handcrafted_features.append(features)
        true_labels.append(item['label'])

    print('Predicting on test set...')
    predictions_with_conf = model.predict(texts, handcrafted_features=handcrafted_features, top_k=1)
    predictions = [pred[0][0] for pred in predictions_with_conf]

    # Generate detailed report
    print('\n' + '='*70)
    print('CLASSIFICATION REPORT - LightGBM Model')
    print('='*70)
    report = classification_report(true_labels, predictions, digits=4, zero_division=0)
    print(report)

    # Calculate F1 scores
    macro_f1 = f1_score(true_labels, predictions, average='macro', zero_division=0)
    weighted_f1 = f1_score(true_labels, predictions, average='weighted', zero_division=0)
    accuracy = accuracy_score(true_labels, predictions)

    print('\n' + '='*70)
    print('SUMMARY METRICS')
    print('='*70)
    status_macro = "✓ PASS" if macro_f1 >= 0.90 else "✗ BELOW 90% TARGET"
    status_weighted = "✓ PASS" if weighted_f1 >= 0.90 else "✗ BELOW 90% TARGET"
    print(f'Macro F1 Score:    {macro_f1:.4f} ({status_macro})')
    print(f'Weighted F1 Score: {weighted_f1:.4f} ({status_weighted})')
    print(f'Accuracy:          {accuracy:.4f}')
    print('='*70)

    # Return exit code based on F1 score
    if macro_f1 >= 0.90 and weighted_f1 >= 0.90:
        print('\n✓ Model meets F1 score requirement (>= 0.90)')
        return 0
    else:
        print('\n✗ Model does NOT meet F1 score requirement (>= 0.90)')
        return 1

if __name__ == '__main__':
    sys.exit(main())
