"""
Ensemble Router
Combines rule-based, ML embedding-based, and LLM-based categorization in parallel
Uses weighted voting for final decision
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

from ..normalize import TransactionNormalizer, FeatureExtractor
from ..resolve import MerchantResolver
from ..rules import RuleCategorizer
from .classifier import EmbeddingClassifier
from .llm_classifier import LLMClassifier

logger = logging.getLogger(__name__)


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
    ensemble_votes: Optional[Dict[str, Any]] = None  # Individual method results


class EnsembleRouter:
    """
    Ensemble categorization router - TRUE HYBRID APPROACH

    Strategy:
    1. Run ALL three methods in PARALLEL:
       - Rule-based categorization
       - ML embedding classifier
       - LLM-based classifier
    2. Combine results using weighted ensemble voting
    3. Final decision based on:
       - Agreement between methods (higher confidence)
       - Individual method confidences
       - Weighted voting based on method reliability

    Weights (configurable):
    - Rules: 0.3 (fast, deterministic, good for known patterns)
    - ML Embeddings: 0.4 (balanced, trained on data)
    - LLM: 0.3 (reasoning, handles edge cases)
    """

    def __init__(
        self,
        taxonomy_path: Optional[str] = None,
        gazetteer_path: Optional[str] = None,
        ml_model_path: Optional[str] = None,
        llm_url: str = "http://llm-service:11434",
        llm_model: str = "llama3.1:8b",
        few_shot_examples_path: Optional[str] = None,
        rule_weight: float = 0.3,
        ml_weight: float = 0.4,
        llm_weight: float = 0.3,
        auto_accept_threshold: float = 0.85,
        review_threshold: float = 0.60,
        enable_parallel: bool = True
    ):
        """
        Initialize ensemble router

        Args:
            taxonomy_path: Path to taxonomy YAML
            gazetteer_path: Path to merchant gazetteer CSV
            ml_model_path: Path to trained ML model
            llm_url: Ollama LLM service URL
            llm_model: LLM model name
            few_shot_examples_path: Path to few-shot examples for LLM
            rule_weight: Weight for rule-based method (0-1)
            ml_weight: Weight for ML method (0-1)
            llm_weight: Weight for LLM method (0-1)
            auto_accept_threshold: Confidence threshold for auto-accept
            review_threshold: Confidence threshold for human review
            enable_parallel: Run methods in parallel (faster)
        """
        self.rule_weight = rule_weight
        self.ml_weight = ml_weight
        self.llm_weight = llm_weight
        self.auto_accept_threshold = auto_accept_threshold
        self.review_threshold = review_threshold
        self.enable_parallel = enable_parallel

        # Normalize weights
        total_weight = rule_weight + ml_weight + llm_weight
        if total_weight > 0:
            self.rule_weight /= total_weight
            self.ml_weight /= total_weight
            self.llm_weight /= total_weight

        # Initialize components
        self.normalizer = TransactionNormalizer()
        self.feature_extractor = FeatureExtractor()

        # Initialize merchant resolver
        self.merchant_resolver = None
        if gazetteer_path:
            try:
                self.merchant_resolver = MerchantResolver(gazetteer_path)
                logger.info("Merchant resolver initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize merchant resolver: {e}")

        # Initialize rule categorizer
        self.rule_categorizer = None
        if taxonomy_path:
            try:
                self.rule_categorizer = RuleCategorizer(taxonomy_path)
                logger.info("Rule categorizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize rule categorizer: {e}")

        # Initialize ML classifier
        self.ml_classifier = None
        if ml_model_path:
            try:
                self.ml_classifier = EmbeddingClassifier()
                self.ml_classifier.load(ml_model_path)
                logger.info("ML classifier loaded")
            except Exception as e:
                logger.warning(f"Failed to load ML classifier: {e}")

        # Initialize LLM classifier
        self.llm_classifier = None
        try:
            self.llm_classifier = LLMClassifier(
                ollama_url=llm_url,
                model_name=llm_model,
                taxonomy_path=taxonomy_path
            )

            # Load few-shot examples
            if few_shot_examples_path:
                self.llm_classifier.load_few_shot_examples(few_shot_examples_path)

            # Check if LLM service is available
            if self.llm_classifier.check_health():
                logger.info("LLM classifier initialized and service is healthy")
            else:
                logger.warning("LLM classifier initialized but service not available")

        except Exception as e:
            logger.warning(f"Failed to initialize LLM classifier: {e}")

        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=3) if enable_parallel else None

    def _run_rule_categorizer(
        self,
        search_text: str,
        merchant: Optional[str],
        channel: Optional[str],
        amount: Optional[float]
    ) -> Optional[Tuple[str, float, List[str], Optional[str]]]:
        """Run rule-based categorization"""
        if not self.rule_categorizer:
            return None

        try:
            result = self.rule_categorizer.categorize(
                text=search_text,
                merchant=merchant,
                channel=channel,
                amount=amount
            )
            return (
                result.category,
                result.confidence,
                result.explanations,
                result.subcategory
            )
        except Exception as e:
            logger.error(f"Rule categorizer error: {e}")
            return None

    def _run_ml_classifier(
        self,
        search_text: str,
        normalized: Dict[str, Any]
    ) -> Optional[Tuple[str, float, List[Tuple[str, float]]]]:
        """Run ML embedding classifier"""
        if not self.ml_classifier:
            return None

        try:
            features = self.feature_extractor.extract_features(normalized)
            predictions = self.ml_classifier.predict_single(
                text=search_text,
                handcrafted_features=features,
                top_k=3
            )

            top_category, top_confidence = predictions[0]
            alternatives = predictions[1:] if len(predictions) > 1 else []

            return (top_category, top_confidence, alternatives)
        except Exception as e:
            logger.error(f"ML classifier error: {e}")
            return None

    def _run_llm_classifier(
        self,
        text: str,
        amount: Optional[float]
    ) -> Optional[Tuple[str, float, str]]:
        """Run LLM-based classifier"""
        if not self.llm_classifier:
            return None

        try:
            category, confidence, reasoning = self.llm_classifier.predict_single(
                text=text,
                amount=amount
            )
            # Handle LLM service unavailable (returns None)
            if category is None or confidence == 0.0:
                return None
            return (category, confidence, reasoning)
        except Exception as e:
            logger.warning(f"LLM classifier error: {e}")
            return None

    def _ensemble_vote(
        self,
        rule_result: Optional[Tuple],
        ml_result: Optional[Tuple],
        llm_result: Optional[Tuple]
    ) -> CategorizationResult:
        """
        Combine results from all methods using weighted voting

        Args:
            rule_result: (category, confidence, explanations, subcategory)
            ml_result: (category, confidence, alternatives)
            llm_result: (category, confidence, reasoning)

        Returns:
            Final CategorizationResult
        """
        # Log individual method results
        logger.info("=== ENSEMBLE VOTING DETAILS ===")
        logger.info(f"Rule result: {rule_result[0] if rule_result else 'None'} (conf: {rule_result[1] if rule_result else 0:.3f}, weight: {self.rule_weight})")
        logger.info(f"ML result:   {ml_result[0] if ml_result else 'None'} (conf: {ml_result[1] if ml_result else 0:.3f}, weight: {self.ml_weight})")
        logger.info(f"LLM result:  {llm_result[0] if llm_result else 'None'} (conf: {llm_result[1] if llm_result else 0:.3f}, weight: {self.llm_weight})")

        # Collect votes with weights
        votes = {}

        if rule_result:
            category, conf, expl, subcat = rule_result
            weighted_vote = conf * self.rule_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            logger.info(f"  → Rule votes for '{category}': {weighted_vote:.4f}")

        if ml_result:
            category, conf, alts = ml_result
            weighted_vote = conf * self.ml_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            logger.info(f"  → ML votes for '{category}': {weighted_vote:.4f}")

        if llm_result:
            category, conf, reasoning = llm_result
            weighted_vote = conf * self.llm_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            logger.info(f"  → LLM votes for '{category}': {weighted_vote:.4f}")

        if not votes:
            # No methods available
            return CategorizationResult(
                category="Other",
                subcategory="Uncategorized",
                confidence=0.0,
                method="none",
                explanations=["no_methods_available"],
                requires_review=True
            )

        # Get winner
        winner_category = max(votes.items(), key=lambda x: x[1])[0]
        winner_score = votes[winner_category]

        # Determine method(s) that voted for winner
        methods_voted = []
        explanations = []
        subcategory = None

        if rule_result and rule_result[0] == winner_category:
            methods_voted.append("rule")
            explanations.extend(rule_result[2])
            subcategory = rule_result[3]

        if ml_result and ml_result[0] == winner_category:
            methods_voted.append("ml")
            explanations.append("ml_embedding_classifier")

        if llm_result and llm_result[0] == winner_category:
            methods_voted.append("llm")
            explanations.append(f"llm_reasoning: {llm_result[2][:100]}")

        # Calculate agreement bonus
        num_methods = sum([rule_result is not None, ml_result is not None, llm_result is not None])
        agreement_count = len(methods_voted)
        agreement_bonus = (agreement_count - 1) * 0.1  # +10% for each additional agreeing method

        # Final confidence (capped at 1.0)
        final_confidence = min(1.0, winner_score + agreement_bonus)

        # Determine method string
        if agreement_count == num_methods and num_methods > 1:
            method = "ensemble_unanimous"
        elif agreement_count > 1:
            method = f"ensemble_{'+'.join(methods_voted)}"
        else:
            method = methods_voted[0] if methods_voted else "ensemble"

        # Get alternatives from ML if available
        alternatives = None
        if ml_result:
            alternatives = ml_result[2]

        # Store individual votes for transparency
        ensemble_votes = {
            "rule": {"category": rule_result[0], "confidence": rule_result[1]} if rule_result else None,
            "ml": {"category": ml_result[0], "confidence": ml_result[1]} if ml_result else None,
            "llm": {"category": llm_result[0], "confidence": llm_result[1]} if llm_result else None,
            "weighted_votes": votes,
            "agreement_count": agreement_count,
            "total_methods": num_methods
        }

        # Log final decision
        logger.info(f"All votes: {votes}")
        logger.info(f"Winner: '{winner_category}' with score {winner_score:.4f}")
        logger.info(f"Agreement: {agreement_count}/{num_methods} methods agreed")
        logger.info(f"Final confidence: {final_confidence:.3f} (method: {method})")
        logger.info("=" * 35)

        return CategorizationResult(
            category=winner_category,
            subcategory=subcategory,
            confidence=final_confidence,
            method=method,
            explanations=explanations,
            alternatives=alternatives,
            requires_review=final_confidence < self.review_threshold,
            ensemble_votes=ensemble_votes
        )

    def categorize(
        self,
        text: str,
        amount: Optional[float] = None,
        date: Optional[str] = None,
        currency: str = "INR"
    ) -> CategorizationResult:
        """
        Categorize a transaction using ensemble of all methods

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
        if merchant and self.merchant_resolver:
            matches = self.merchant_resolver.resolve(merchant, threshold=0.8, top_k=1)
            if matches:
                resolved_merchant = matches[0].canonical_name

        # Step 3: Run all categorizers in parallel
        rule_result = None
        ml_result = None
        llm_result = None

        if self.enable_parallel and self.executor:
            # Parallel execution
            futures = {}

            if self.rule_categorizer:
                futures['rule'] = self.executor.submit(
                    self._run_rule_categorizer,
                    search_text, resolved_merchant or merchant, channel, amount
                )

            if self.ml_classifier:
                futures['ml'] = self.executor.submit(
                    self._run_ml_classifier,
                    search_text, normalized
                )

            if self.llm_classifier:
                futures['llm'] = self.executor.submit(
                    self._run_llm_classifier,
                    text, amount
                )

            # Collect results
            for method, future in futures.items():
                try:
                    result = future.result(timeout=60)  # 60s timeout
                    if method == 'rule':
                        rule_result = result
                    elif method == 'ml':
                        ml_result = result
                    elif method == 'llm':
                        llm_result = result
                except Exception as e:
                    logger.error(f"{method} method failed: {e}")

        else:
            # Sequential execution
            rule_result = self._run_rule_categorizer(
                search_text, resolved_merchant or merchant, channel, amount
            )
            ml_result = self._run_ml_classifier(search_text, normalized)
            llm_result = self._run_llm_classifier(text, amount)

        # Step 4: Ensemble voting
        result = self._ensemble_vote(rule_result, ml_result, llm_result)
        result.merchant_resolved = resolved_merchant

        return result

    def categorize_batch(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[CategorizationResult]:
        """
        Categorize a batch of transactions

        Args:
            transactions: List of transaction dicts

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

        # Ensemble agreement stats
        unanimous_count = sum(1 for r in results if 'unanimous' in r.method)

        return {
            'total': total,
            'avg_confidence': round(avg_confidence, 3),
            'requires_review': review_count,
            'review_percentage': round(review_count / total * 100, 1),
            'by_category': by_category,
            'by_method': by_method,
            'unanimous_decisions': unanimous_count,
            'unanimous_percentage': round(unanimous_count / total * 100, 1)
        }

    def __del__(self):
        """Cleanup thread pool"""
        if self.executor:
            self.executor.shutdown(wait=False)
