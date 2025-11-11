"""
Hybrid Router
Combines rule-based, ML-based, and merchant-based categorization
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from ..normalize import TransactionNormalizer, FeatureExtractor
from ..resolve import MerchantResolver
from ..rules import RuleCategorizer
from .classifier import EmbeddingClassifier


@dataclass
class CategorizationResult:
    """Result of transaction categorization"""
    category: str
    subcategory: Optional[str]
    confidence: float
    method: str
    explanations: List[str]
    alternatives: Optional[List[Tuple[str, float]]] = None
    requires_review: bool = False
    merchant_resolved: Optional[str] = None


class HybridRouter:
    """
    Hybrid categorization router

    Routing logic:
    1. Normalize transaction
    2. Resolve merchant (if possible)
    3. Try rule-based categorization
    4. If confidence < threshold, try ML classifier
    5. If still low confidence, mark for review

    Confidence thresholds:
    - >= 0.85: Auto-accept
    - 0.60-0.85: Use ML for re-ranking
    - < 0.60: Human review
    """

    def __init__(
        self,
        taxonomy_path: Optional[str] = None,
        gazetteer_path: Optional[str] = None,
        model_path: Optional[str] = None,
        auto_accept_threshold: float = 0.85,
        review_threshold: float = 0.60
    ):
        """
        Initialize hybrid router

        Args:
            taxonomy_path: Path to taxonomy YAML
            gazetteer_path: Path to merchant gazetteer CSV
            model_path: Path to trained ML model
            auto_accept_threshold: Confidence threshold for auto-accept
            review_threshold: Confidence threshold below which human review needed
        """
        self.auto_accept_threshold = auto_accept_threshold
        self.review_threshold = review_threshold

        # Initialize components
        self.normalizer = TransactionNormalizer()
        self.feature_extractor = FeatureExtractor()

        # Initialize merchant resolver
        self.merchant_resolver = None
        if gazetteer_path:
            try:
                self.merchant_resolver = MerchantResolver(gazetteer_path)
                logging.info("Merchant resolver initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize merchant resolver: {e}")

        # Initialize rule categorizer
        self.rule_categorizer = None
        if taxonomy_path:
            try:
                self.rule_categorizer = RuleCategorizer(taxonomy_path)
                logging.info("Rule categorizer initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize rule categorizer: {e}")

        # Initialize ML classifier
        self.ml_classifier = None
        if model_path:
            try:
                self.ml_classifier = EmbeddingClassifier()
                self.ml_classifier.load(model_path)
                logging.info("ML classifier loaded")
            except Exception as e:
                logging.warning(f"Failed to load ML classifier: {e}")

    def categorize(
        self,
        text: str,
        amount: Optional[float] = None,
        date: Optional[str] = None,
        currency: str = "INR"
    ) -> CategorizationResult:
        """
        Categorize a transaction

        Args:
            text: Transaction description
            amount: Transaction amount
            date: Transaction date
            currency: Currency code

        Returns:
            CategorizationResult with category and metadata
        """
        # Step 1: Normalize transaction
        normalized = self.normalizer.normalize(text, amount, date, currency)

        search_text = normalized['search_text']
        merchant = normalized['normalized']['merchant']
        channel = normalized['normalized']['channel']

        # Step 2: Resolve merchant
        resolved_merchant = None
        merchant_category = None

        if merchant and self.merchant_resolver:
            matches = self.merchant_resolver.resolve(merchant, threshold=0.8, top_k=1)
            if matches:
                resolved_merchant = matches[0].canonical_name
                merchant_category = matches[0].category

        # Step 3: Try rule-based categorization
        rule_result = None
        if self.rule_categorizer:
            rule_result = self.rule_categorizer.categorize(
                text=search_text,
                merchant=resolved_merchant or merchant,
                channel=channel,
                amount=amount
            )

        # Check if rule-based result is confident enough
        if rule_result and rule_result.confidence >= self.auto_accept_threshold:
            return CategorizationResult(
                category=rule_result.category,
                subcategory=rule_result.subcategory,
                confidence=rule_result.confidence,
                method="rule",
                explanations=rule_result.explanations,
                merchant_resolved=resolved_merchant,
                requires_review=False
            )

        # Step 4: Try ML classifier
        ml_result = None
        if self.ml_classifier:
            # Extract handcrafted features
            features = self.feature_extractor.extract_features(normalized)

            # Predict
            predictions = self.ml_classifier.predict_single(
                text=search_text,
                handcrafted_features=features,
                top_k=3
            )

            ml_result = predictions[0]  # (category, confidence)
            alternatives = predictions[1:] if len(predictions) > 1 else None

        # Step 5: Combine results
        if ml_result:
            ml_category, ml_confidence = ml_result

            # If ML is confident, use it
            if ml_confidence >= self.auto_accept_threshold:
                return CategorizationResult(
                    category=ml_category,
                    subcategory=None,  # TODO: Predict subcategory
                    confidence=ml_confidence,
                    method="ml",
                    explanations=["ml_classifier"],
                    alternatives=alternatives,
                    merchant_resolved=resolved_merchant,
                    requires_review=False
                )

            # Hybrid: Average rule and ML if both available
            if rule_result:
                # If both agree, boost confidence
                if rule_result.category == ml_category:
                    combined_confidence = min(1.0, (rule_result.confidence + ml_confidence) / 2 * 1.2)
                    method = "hybrid"
                else:
                    # Take higher confidence
                    if ml_confidence > rule_result.confidence:
                        combined_confidence = ml_confidence
                        final_category = ml_category
                        method = "ml"
                    else:
                        combined_confidence = rule_result.confidence
                        final_category = rule_result.category
                        method = "rule"

                    if rule_result.category == ml_category:
                        final_category = ml_category

                return CategorizationResult(
                    category=rule_result.category if rule_result.category == ml_category else (
                        ml_category if ml_confidence > rule_result.confidence else rule_result.category
                    ),
                    subcategory=rule_result.subcategory if rule_result.category == ml_category else None,
                    confidence=combined_confidence if rule_result.category == ml_category else max(
                        ml_confidence, rule_result.confidence
                    ),
                    method=method if rule_result.category == ml_category else (
                        "ml" if ml_confidence > rule_result.confidence else "rule"
                    ),
                    explanations=(rule_result.explanations if rule_result.category == ml_category else []) + [
                        "ml_classifier"],
                    alternatives=alternatives,
                    merchant_resolved=resolved_merchant,
                    requires_review=combined_confidence < self.review_threshold if rule_result.category == ml_category else max(
                        ml_confidence, rule_result.confidence) < self.review_threshold
                )

            # Only ML available
            requires_review = ml_confidence < self.review_threshold

            return CategorizationResult(
                category=ml_category,
                subcategory=None,
                confidence=ml_confidence,
                method="ml",
                explanations=["ml_classifier"],
                alternatives=alternatives,
                merchant_resolved=resolved_merchant,
                requires_review=requires_review
            )

        # Step 6: Only rule result available (or nothing)
        if rule_result:
            requires_review = rule_result.confidence < self.review_threshold

            return CategorizationResult(
                category=rule_result.category,
                subcategory=rule_result.subcategory,
                confidence=rule_result.confidence,
                method="rule",
                explanations=rule_result.explanations,
                merchant_resolved=resolved_merchant,
                requires_review=requires_review
            )

        # Fallback: No categorization possible
        return CategorizationResult(
            category="Other",
            subcategory="Uncategorized",
            confidence=0.0,
            method="fallback",
            explanations=["no_match"],
            merchant_resolved=resolved_merchant,
            requires_review=True
        )

    def categorize_batch(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[CategorizationResult]:
        """
        Categorize a batch of transactions

        Args:
            transactions: List of transaction dicts with 'text', 'amount', 'date'

        Returns:
            List of CategorizationResult
        """
        results = []

        for txn in transactions:
            result = self.categorize(
                text=txn.get('text', txn.get('description', '')),
                amount=txn.get('amount'),
                date=txn.get('date', txn.get('timestamp')),
                currency=txn.get('currency', 'INR')
            )
            results.append(result)

        return results

    def get_stats(self, results: List[CategorizationResult]) -> Dict[str, Any]:
        """Calculate batch statistics"""
        if not results:
            return {}

        total = len(results)
        avg_confidence = sum(r.confidence for r in results) / total
        review_count = sum(1 for r in results if r.requires_review)

        # Count by category
        by_category = {}
        for r in results:
            by_category[r.category] = by_category.get(r.category, 0) + 1

        # Count by method
        by_method = {}
        for r in results:
            by_method[r.method] = by_method.get(r.method, 0) + 1

        return {
            'total': total,
            'avg_confidence': round(avg_confidence, 3),
            'requires_review': review_count,
            'review_percentage': round(review_count / total * 100, 1),
            'by_category': by_category,
            'by_method': by_method
        }
