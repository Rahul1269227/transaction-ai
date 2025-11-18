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
        enable_parallel: bool = True,
        llm_timeout: float = 120.0,  # 120-second timeout for LLM (allows time for inference + parallelization)
        fast_mode: bool = False,  # Skip LLM when rule+ML agree with high confidence
        fast_mode_threshold: float = 0.90  # Confidence threshold for fast mode (rule+ML agreement)
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
            llm_timeout: Timeout for LLM requests in seconds (default: 120.0)
            fast_mode: Skip LLM when rule+ML agree with high confidence (default: False)
            fast_mode_threshold: Confidence threshold for fast mode (default: 0.90)
        """
        self.rule_weight = rule_weight
        self.ml_weight = ml_weight
        self.llm_weight = llm_weight
        self.auto_accept_threshold = auto_accept_threshold
        self.review_threshold = review_threshold
        self.enable_parallel = enable_parallel
        self.llm_timeout = llm_timeout
        self.fast_mode = fast_mode
        self.fast_mode_threshold = fast_mode_threshold

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
        total_active_weight = 0.0  # Track total weight of active methods

        if rule_result:
            category, conf, expl, subcat = rule_result
            weighted_vote = conf * self.rule_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            total_active_weight += self.rule_weight
            logger.info(f"  → Rule votes for '{category}': {weighted_vote:.4f}")

        if ml_result:
            category, conf, alts = ml_result
            weighted_vote = conf * self.ml_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            total_active_weight += self.ml_weight
            logger.info(f"  → ML votes for '{category}': {weighted_vote:.4f}")

        if llm_result:
            category, conf, reasoning = llm_result
            weighted_vote = conf * self.llm_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            total_active_weight += self.llm_weight
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

        # Normalize winner score by total active weight
        # This ensures confidence reflects actual method performance, not just configured weights
        if total_active_weight > 0:
            normalized_score = winner_score / total_active_weight
        else:
            normalized_score = winner_score

        logger.info(f"Winner score: {winner_score:.4f} (normalized: {normalized_score:.4f}, active_weight: {total_active_weight:.4f})")

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

        # FIX #3: BETTER CONFIDENCE CALIBRATION
        # Calculate agreement metrics
        num_methods = sum([rule_result is not None, ml_result is not None, llm_result is not None])
        agreement_count = len(methods_voted)

        # Stronger rewards/penalties based on agreement
        if num_methods >= 2:
            if agreement_count == num_methods:
                # Full agreement: +20% boost (was +10%)
                agreement_adjustment = 0.20
                logger.info(f"Full agreement ({agreement_count}/{num_methods}): +20% confidence boost")
            elif agreement_count >= 2:
                # Partial agreement (2+ methods): +10% boost
                agreement_adjustment = 0.10
                logger.info(f"Partial agreement ({agreement_count}/{num_methods}): +10% confidence boost")
            elif agreement_count == 1:
                # No agreement: -15% penalty (winner is alone)
                agreement_adjustment = -0.15
                logger.info(f"No agreement ({agreement_count}/{num_methods}): -15% confidence penalty")
            else:
                agreement_adjustment = 0.0
        else:
            # Only one method available
            agreement_adjustment = 0.0

        # Final confidence with calibration (capped at 0.05-1.0)
        # Use normalized_score instead of winner_score to account for active methods only
        final_confidence = max(0.05, min(1.0, normalized_score + agreement_adjustment))

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
        currency: str = "INR",
        merchant: Optional[str] = None
    ) -> CategorizationResult:
        """
        Categorize a transaction using ensemble of all methods

        Args:
            text: Transaction description
            amount: Transaction amount
            date: Transaction date
            currency: Currency code
            merchant: Merchant name (optional, extracted from JSON)

        Returns:
            CategorizationResult with category and metadata
        """
        # Step 1: Normalize transaction
        normalized = self.normalizer.normalize(text, amount, date, currency, merchant)
        search_text = normalized['search_text']
        # Only use normalized merchant if one wasn't explicitly provided
        if merchant is None:
            merchant = normalized['normalized']['merchant']
        channel = normalized['normalized']['channel']

        # Step 2: Resolve merchant (with fuzzy matching on full text)
        resolved_merchant = None
        merchant_category = None
        merchant_subcategory = None
        merchant_confidence = 0.0

        # Try fuzzy matching on the full transaction text first
        if self.merchant_resolver:
            # Search the entire transaction text against gazetteer
            fuzzy_matches = self.merchant_resolver.search(text, limit=1)
            if fuzzy_matches and fuzzy_matches[0].similarity_score >= 0.70:
                match = fuzzy_matches[0]
                resolved_merchant = match.canonical_name
                merchant_category = match.category
                merchant_subcategory = match.subcategory
                merchant_confidence = match.similarity_score
                logger.info(f"Fuzzy merchant match in text: '{text}' -> {resolved_merchant} ({merchant_confidence:.2%})")

        # Fallback to normalized merchant extraction if fuzzy didn't find anything
        if not resolved_merchant and merchant and self.merchant_resolver:
            matches = self.merchant_resolver.resolve(merchant, threshold=0.8, top_k=1)
            if matches:
                match = matches[0]
                resolved_merchant = match.canonical_name
                merchant_category = match.category
                merchant_subcategory = match.subcategory
                merchant_confidence = match.similarity_score

        # FIX #1: MERCHANT-FIRST STRATEGY - Merchant matches should dominate
        # Lower threshold to 0.70 for fuzzy matches (already high-quality from gazetteer)
        # Boost confidence to 95% when merchant is clearly identified
        if merchant_confidence >= 0.70:
            # Boost confidence for merchant matches (they're highly reliable)
            boosted_confidence = min(0.95, merchant_confidence + 0.10)
            logger.info(f"High-confidence merchant match: {resolved_merchant} -> {merchant_category} ({merchant_confidence:.2%} -> {boosted_confidence:.2%})")
            return CategorizationResult(
                category=merchant_category,
                subcategory=merchant_subcategory,
                confidence=boosted_confidence,
                method="merchant_gazetteer",
                explanations=[f"merchant_match={resolved_merchant}"],
                requires_review=False,
                merchant_resolved=resolved_merchant,
                ensemble_votes={
                    "merchant": {"category": merchant_category, "confidence": boosted_confidence},
                    "rule": None,
                    "ml": None,
                    "llm": None,
                    "weighted_votes": {merchant_category: boosted_confidence},
                    "agreement_count": 1,
                    "total_methods": 1
                }
            )

        # Step 3: Run categorizers (with fast mode optimization)
        rule_result = None
        ml_result = None
        llm_result = None

        # Try rule-based first for potential early exit
        if self.rule_categorizer:
            rule_result = self._run_rule_categorizer(
                search_text, resolved_merchant or merchant, channel, amount
            )

            # HIGH-CONFIDENCE RULE EARLY EXIT (deterministic rules like ATM, EMI, Salary, Fuel)
            if rule_result and rule_result[1] >= 0.95:
                logger.info(f"High-confidence deterministic rule: {rule_result[0]} ({rule_result[1]:.2%}) - skipping ML/LLM")
                return CategorizationResult(
                    category=rule_result[0],
                    subcategory=rule_result[3],
                    confidence=rule_result[1],
                    method="rule_deterministic",
                    explanations=rule_result[2],
                    requires_review=False,
                    merchant_resolved=resolved_merchant,
                    ensemble_votes={
                        "rule": {"category": rule_result[0], "confidence": rule_result[1]},
                        "ml": None,
                        "llm": None,
                        "weighted_votes": {rule_result[0]: rule_result[1]},
                        "agreement_count": 1,
                        "total_methods": 1
                    }
                )

        if self.enable_parallel and self.executor:
            # Parallel execution with per-method timeouts
            futures = {}
            timeouts = {}

            # Don't re-run rule if we already ran it for early exit check
            # (rule_result will be None if not run, or < 0.95 if run but didn't exit)
            if self.rule_categorizer and rule_result is None:
                futures['rule'] = self.executor.submit(
                    self._run_rule_categorizer,
                    search_text, resolved_merchant or merchant, channel, amount
                )
                timeouts['rule'] = 2.0  # Rules are fast

            if self.ml_classifier:
                futures['ml'] = self.executor.submit(
                    self._run_ml_classifier,
                    search_text, normalized
                )
                timeouts['ml'] = 5.0  # ML is moderately fast

            # FIX #2: LLM AS FALLBACK - Only run LLM when ML confidence is low
            # Wait for rule and ML first, then decide if LLM is needed
            should_skip_llm = False
            if self.llm_classifier:
                # Wait for rule and ML first
                rule_result = None
                ml_result = None
                for method in ['rule', 'ml']:
                    if method in futures:
                        try:
                            timeout = timeouts.get(method, 10.0)
                            result = futures[method].result(timeout=timeout)
                            if method == 'rule':
                                rule_result = result
                            elif method == 'ml':
                                ml_result = result
                        except (TimeoutError, Exception) as e:
                            logger.warning(f"{method} method failed: {e}")

                # Skip LLM if:
                # 1. Fast mode + Rule+ML agree with high confidence (>= 90%)
                # 2. ML confidence alone is >= 60% (LLM fallback threshold)
                if self.fast_mode and rule_result and ml_result:
                    # Extract from tuple results
                    rule_cat = rule_result[0]
                    rule_conf = rule_result[1]
                    ml_cat = ml_result[0]
                    ml_conf = ml_result[1]

                    # Check agreement and confidence
                    if rule_cat == ml_cat and rule_conf >= self.fast_mode_threshold and ml_conf >= self.fast_mode_threshold:
                        should_skip_llm = True
                        min_conf = min(rule_conf, ml_conf)
                        logger.info(f"Fast mode: Rule+ML agree on '{rule_cat}' with confidence {min_conf:.2f} - skipping LLM")

                # Also skip if ML confidence is high enough (LLM fallback logic)
                if not should_skip_llm and ml_result:
                    ml_conf = ml_result[1]
                    if ml_conf >= 0.60:  # 60% threshold for ML confidence
                        should_skip_llm = True
                        logger.info(f"LLM fallback: ML confidence {ml_conf:.2f} >= 0.60 - skipping LLM")

            if self.llm_classifier and not should_skip_llm:
                futures['llm'] = self.executor.submit(
                    self._run_llm_classifier,
                    text, amount
                )
                timeouts['llm'] = self.llm_timeout  # LLM gets aggressive timeout

            # Collect results with individual timeouts
            for method, future in futures.items():
                try:
                    timeout = timeouts.get(method, 10.0)
                    result = future.result(timeout=timeout)
                    if method == 'rule':
                        rule_result = result
                    elif method == 'ml':
                        ml_result = result
                    elif method == 'llm':
                        llm_result = result
                except TimeoutError:
                    logger.warning(f"{method} method timed out after {timeouts.get(method)}s - continuing without it")
                except Exception as e:
                    logger.error(f"{method} method failed: {e}")

        else:
            # Sequential execution
            rule_result = self._run_rule_categorizer(
                search_text, resolved_merchant or merchant, channel, amount
            )
            ml_result = self._run_ml_classifier(search_text, normalized)

            # FIX #2: LLM AS FALLBACK - Only run when needed
            should_skip_llm = False

            # Check fast mode first (Rule+ML agreement)
            if self.fast_mode and rule_result and ml_result:
                # Extract from tuple results
                rule_cat = rule_result[0]
                rule_conf = rule_result[1]
                ml_cat = ml_result[0]
                ml_conf = ml_result[1]

                if rule_cat == ml_cat and rule_conf >= self.fast_mode_threshold and ml_conf >= self.fast_mode_threshold:
                    should_skip_llm = True
                    logger.info(f"Fast mode: Rule+ML agree on '{rule_cat}' - skipping LLM")

            # Also check ML confidence threshold (LLM fallback logic)
            if not should_skip_llm and ml_result:
                ml_conf = ml_result[1]
                if ml_conf >= 0.60:  # 60% threshold
                    should_skip_llm = True
                    logger.info(f"LLM fallback: ML confidence {ml_conf:.2f} >= 0.60 - skipping LLM")

            # Run LLM only if needed
            if should_skip_llm:
                llm_result = None
            else:
                logger.info("Running LLM as fallback for low-confidence prediction")
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
