"""
Ensemble Router
Combines rule-based, ML embedding-based, and LLM-based categorization in parallel
Uses weighted voting for final decision
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

from ..normalize import TransactionNormalizer, FeatureExtractor
from ..resolve import MerchantResolver
from ..rules import RuleCategorizer
from .classifier import EmbeddingClassifier
from .llm_classifier import LLMClassifier
from .mcc_classifier import MCCClassifier

logger = logging.getLogger(__name__)

# Load ensemble configuration from environment variables
MERCHANT_CONFIDENCE_THRESHOLD = float(os.getenv("MERCHANT_CONFIDENCE_THRESHOLD", "0.70"))
MERCHANT_CONFIDENCE_BOOST = float(os.getenv("MERCHANT_CONFIDENCE_BOOST", "0.10"))
RULE_EARLY_EXIT_THRESHOLD = float(os.getenv("RULE_EARLY_EXIT_THRESHOLD", "0.95"))
MCC_EARLY_EXIT_THRESHOLD = float(os.getenv("MCC_EARLY_EXIT_THRESHOLD", "0.90"))
FULL_AGREEMENT_BOOST = float(os.getenv("FULL_AGREEMENT_BOOST", "0.20"))
PARTIAL_AGREEMENT_BOOST = float(os.getenv("PARTIAL_AGREEMENT_BOOST", "0.10"))
NO_AGREEMENT_PENALTY = float(os.getenv("NO_AGREEMENT_PENALTY", "0.15"))
LLM_FALLBACK_THRESHOLD = float(os.getenv("LLM_FALLBACK_THRESHOLD", "0.60"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))


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
    normalized_data: Optional[Dict[str, Any]] = None  # Normalized transaction data (avoids duplicate work)


class EnsembleRouter:
    """
    Ensemble categorization router - TRUE HYBRID APPROACH

    Strategy:
    1. Run ALL four methods in PARALLEL:
       - MCC-based categorization (when MCC code available)
       - Rule-based categorization
       - ML embedding classifier
       - LLM-based classifier
    2. Combine results using weighted ensemble voting
    3. Final decision based on:
       - Agreement between methods (higher confidence)
       - Individual method confidences
       - Weighted voting based on method reliability

    Weights (configurable):
    - MCC: 0.25 (highly accurate when available, ISO standard)
    - Rules: 0.25 (fast, deterministic, good for known patterns)
    - ML Embeddings: 0.30 (balanced, trained on data)
    - LLM: 0.20 (reasoning, handles edge cases)
    """

    # Category-specific confidence thresholds
    # Critical categories require higher confidence for auto-accept and review
    CATEGORY_THRESHOLDS = {
        # Critical financial categories - higher thresholds
        "Investments": {"auto_accept": 0.90, "review": 0.70},
        "income_salary": {"auto_accept": 0.90, "review": 0.70},
        "Rent": {"auto_accept": 0.90, "review": 0.70},
        "Fees & Charges": {"auto_accept": 0.90, "review": 0.70},
        "Bills": {"auto_accept": 0.88, "review": 0.65},
        "transfers_upi": {"auto_accept": 0.88, "review": 0.65},
        "Fraud & Security": {"auto_accept": 0.95, "review": 0.80},  # Highest threshold

        # Medium-importance categories - standard thresholds
        "Travel": {"auto_accept": 0.85, "review": 0.60},
        "Health": {"auto_accept": 0.85, "review": 0.60},
        "Education": {"auto_accept": 0.85, "review": 0.60},
        "Fuel": {"auto_accept": 0.85, "review": 0.60},
        "Utilities": {"auto_accept": 0.85, "review": 0.60},

        # Low-risk categories - lower thresholds
        "Food & Dining": {"auto_accept": 0.80, "review": 0.50},
        "Groceries": {"auto_accept": 0.80, "review": 0.50},
        "Shopping": {"auto_accept": 0.80, "review": 0.50},
        "Entertainment": {"auto_accept": 0.80, "review": 0.50},
        "Transport": {"auto_accept": 0.80, "review": 0.50},
        "ATM/Cash": {"auto_accept": 0.85, "review": 0.60},

        # Default for uncategorized
        "Other": {"auto_accept": 0.95, "review": 0.80},
    }

    def __init__(
        self,
        taxonomy_path: Optional[str] = None,
        gazetteer_path: Optional[str] = None,
        ml_model_path: Optional[str] = None,
        llm_url: str = "http://llm-service:11434",
        llm_model: str = "llama3.1:8b",
        few_shot_examples_path: Optional[str] = None,
        mcc_weight: float = 0.25,
        rule_weight: float = 0.25,
        ml_weight: float = 0.30,
        llm_weight: float = 0.20,
        auto_accept_threshold: float = 0.85,
        review_threshold: float = 0.60,
        enable_parallel: bool = True,
        llm_timeout: float = 120.0,  # 120-second timeout for LLM (allows time for inference + parallelization)
        fast_mode: bool = False,  # Skip LLM when rule+ML agree with high confidence
        fast_mode_threshold: float = 0.90,  # Confidence threshold for fast mode (rule+ML agreement)
        use_category_thresholds: bool = True  # Use category-specific thresholds
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
            mcc_weight: Weight for MCC-based method (0-1)
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
        self.mcc_weight = mcc_weight
        self.rule_weight = rule_weight
        self.ml_weight = ml_weight
        self.llm_weight = llm_weight
        self.auto_accept_threshold = auto_accept_threshold
        self.review_threshold = review_threshold
        self.enable_parallel = enable_parallel
        self.llm_timeout = llm_timeout
        self.fast_mode = fast_mode
        self.fast_mode_threshold = fast_mode_threshold
        self.use_category_thresholds = use_category_thresholds

        # Normalize weights
        total_weight = mcc_weight + rule_weight + ml_weight + llm_weight
        if total_weight > 0:
            self.mcc_weight /= total_weight
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

        # Initialize MCC classifier
        self.mcc_classifier = None
        try:
            self.mcc_classifier = MCCClassifier()
            logger.info("MCC classifier initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize MCC classifier: {e}")

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
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS) if enable_parallel else None

    def _get_category_threshold(self, category: str, threshold_type: str) -> float:
        """
        Get category-specific threshold

        Args:
            category: Category name
            threshold_type: Either 'auto_accept' or 'review'

        Returns:
            Threshold value (float)
        """
        if not self.use_category_thresholds:
            # Use global thresholds
            if threshold_type == 'auto_accept':
                return self.auto_accept_threshold
            else:
                return self.review_threshold

        # Get category-specific threshold
        category_config = self.CATEGORY_THRESHOLDS.get(category)
        if category_config:
            return category_config.get(threshold_type,
                                      self.auto_accept_threshold if threshold_type == 'auto_accept' else self.review_threshold)

        # Fallback to global thresholds if category not found
        return self.auto_accept_threshold if threshold_type == 'auto_accept' else self.review_threshold

    def _run_mcc_classifier(
        self,
        text: str,
        mcc: Optional[str]
    ) -> Optional[Tuple[str, float, str]]:
        """Run MCC-based classifier"""
        if not self.mcc_classifier:
            return None

        try:
            result = self.mcc_classifier.categorize(text=text, mcc=mcc)
            # Only return result if MCC was actually available and matched
            if result['confidence'] > 0.0:
                return (result['category'], result['confidence'], result['mcc_code'])
            return None
        except Exception as e:
            logger.error(f"MCC classifier error: {e}")
            return None

    def _run_rule_categorizer(
        self,
        search_text: str,
        merchant: Optional[str],
        channel: Optional[str],
        amount: Optional[float],
        date: Optional[str] = None
    ) -> Optional[Tuple[str, float, List[str], Optional[str]]]:
        """Run rule-based categorization"""
        if not self.rule_categorizer:
            return None

        try:
            result = self.rule_categorizer.categorize(
                text=search_text,
                merchant=merchant,
                channel=channel,
                amount=amount,
                date=date
            )
            if result:
                return (
                    result.category,
                    result.confidence,
                    result.explanations,
                    result.subcategory
                )
            return None
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

    def _normalize_category_name(self, category: str) -> str:
        """
        Normalize category names to match taxonomy
        Maps legacy/variant category names to standard taxonomy categories
        
        Args:
            category: Category name from any method
            
        Returns:
            Normalized category name matching taxonomy
        """
        if not category:
            return category
        
        # First, try to use taxonomy from rule categorizer if available
        if self.rule_categorizer and hasattr(self.rule_categorizer, 'categories'):
            # Check if category is a category ID (like "bills")
            if category in self.rule_categorizer.categories:
                taxonomy_category = self.rule_categorizer.categories[category]
                return taxonomy_category.get('name', category)
            
            # Check if category matches any taxonomy category name
            for cat_id, cat_info in self.rule_categorizer.categories.items():
                if cat_info.get('name', '').lower() == category.lower():
                    return cat_info.get('name', category)
        
        # Fallback: Static normalization mapping for common mismatches
        # Maps variant names to standard taxonomy category names
        CATEGORY_NORMALIZATION = {
            # Utilities -> Bills (most common mismatch)
            "utilities": "Bills",
            "Utilities": "Bills",
            "utility": "Bills",
            "Utility": "Bills",
            "bills": "Bills",  # Handle lowercase ID
            "Bills": "Bills",  # Ensure proper case
            
            # Ensure consistency with taxonomy category names
            # (Add more mappings as needed)
        }
        
        normalized = CATEGORY_NORMALIZATION.get(category, category)
        if normalized != category:
            logger.debug(f"Normalized category '{category}' -> '{normalized}'")
        return normalized

    def _ensemble_vote(
        self,
        mcc_result: Optional[Tuple],
        rule_result: Optional[Tuple],
        ml_result: Optional[Tuple],
        llm_result: Optional[Tuple]
    ) -> CategorizationResult:
        """
        Combine results from all methods using weighted voting

        Args:
            mcc_result: (category, confidence, mcc_code)
            rule_result: (category, confidence, explanations, subcategory)
            ml_result: (category, confidence, alternatives)
            llm_result: (category, confidence, reasoning)

        Returns:
            Final CategorizationResult
        """
        # Normalize category names before voting to ensure consistency
        if mcc_result:
            mcc_result = (self._normalize_category_name(mcc_result[0]), mcc_result[1], mcc_result[2])
        if rule_result:
            rule_result = (self._normalize_category_name(rule_result[0]), rule_result[1], rule_result[2], rule_result[3])
        if ml_result:
            # Normalize main category and alternatives
            normalized_alts = [(self._normalize_category_name(cat), conf) for cat, conf in ml_result[2]]
            ml_result = (self._normalize_category_name(ml_result[0]), ml_result[1], normalized_alts)
        if llm_result:
            llm_result = (self._normalize_category_name(llm_result[0]), llm_result[1], llm_result[2])
        
        # Log individual method results
        logger.info("=== ENSEMBLE VOTING DETAILS ===")
        logger.info(f"MCC result:  {mcc_result[0] if mcc_result else 'None'} (conf: {mcc_result[1] if mcc_result else 0:.3f}, weight: {self.mcc_weight})")
        logger.info(f"Rule result: {rule_result[0] if rule_result else 'None'} (conf: {rule_result[1] if rule_result else 0:.3f}, weight: {self.rule_weight})")
        logger.info(f"ML result:   {ml_result[0] if ml_result else 'None'} (conf: {ml_result[1] if ml_result else 0:.3f}, weight: {self.ml_weight})")
        logger.info(f"LLM result:  {llm_result[0] if llm_result else 'None'} (conf: {llm_result[1] if llm_result else 0:.3f}, weight: {self.llm_weight})")

        # Collect votes with weights
        votes = {}
        total_active_weight = 0.0  # Track total weight of active methods

        if mcc_result:
            category, conf, mcc_code = mcc_result
            weighted_vote = conf * self.mcc_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            total_active_weight += self.mcc_weight
            logger.debug(f"  → MCC votes for '{category}' (code: {mcc_code}): {weighted_vote:.4f}")

        if rule_result:
            category, conf, expl, subcat = rule_result
            weighted_vote = conf * self.rule_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            total_active_weight += self.rule_weight
            logger.debug(f"  → Rule votes for '{category}': {weighted_vote:.4f}")

        if ml_result:
            category, conf, alts = ml_result
            weighted_vote = conf * self.ml_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            total_active_weight += self.ml_weight
            logger.debug(f"  → ML votes for '{category}': {weighted_vote:.4f}")

        if llm_result:
            category, conf, reasoning = llm_result
            weighted_vote = conf * self.llm_weight
            votes[category] = votes.get(category, 0) + weighted_vote
            total_active_weight += self.llm_weight
            logger.debug(f"  → LLM votes for '{category}': {weighted_vote:.4f}")

        if not votes:
            # No methods available
            return CategorizationResult(
                category="Other",
                subcategory="Uncategorized",
                confidence=0.0,
                method="none",
                explanations=["no_methods_available"],
                requires_review=True,
                normalized_data=None
            )

        # LLM TIEBREAKER: When rule and ML disagree, ALWAYS trust LLM if available
        llm_tiebreaker_applied = False
        if (rule_result and ml_result and llm_result and
            rule_result[0] != ml_result[0]):  # Rule and ML disagree

            # LLM ALWAYS makes final decision when there's disagreement
            llm_category = llm_result[0]
            logger.info(f"🎯 LLM TIEBREAKER: Rule={rule_result[0]}, ML={ml_result[0]}, LLM={llm_category} (conf: {llm_result[1]:.3f})")
            logger.info(f"   → LLM makes FINAL DECISION: '{llm_category}'")

            # Override winner to LLM's choice
            winner_category = llm_category
            winner_score = votes[winner_category]
            llm_tiebreaker_applied = True

        if not llm_tiebreaker_applied:
            # Standard voting: Get winner by weighted votes
            winner_category = max(votes.items(), key=lambda x: x[1])[0]
            winner_score = votes[winner_category]

        # Normalize winner score by total active weight
        # This ensures confidence reflects actual method performance, not just configured weights
        if total_active_weight > 0:
            normalized_score = winner_score / total_active_weight
        else:
            normalized_score = winner_score

        logger.info(f"Winner score: {winner_score:.4f} (normalized: {normalized_score:.4f}, active_weight: {total_active_weight:.4f}, llm_tiebreaker: {llm_tiebreaker_applied})")

        # Determine method(s) that voted for winner
        methods_voted = []
        explanations = []
        subcategory = None

        if mcc_result and mcc_result[0] == winner_category:
            methods_voted.append("mcc")
            explanations.append(f"mcc_code={mcc_result[2]}")

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
        num_methods = sum([mcc_result is not None, rule_result is not None, ml_result is not None, llm_result is not None])
        agreement_count = len(methods_voted)

        # Stronger rewards/penalties based on agreement
        if num_methods >= 2:
            if agreement_count == num_methods:
                # Full agreement: use configured boost
                agreement_adjustment = FULL_AGREEMENT_BOOST
                logger.info(f"Full agreement ({agreement_count}/{num_methods}): +{FULL_AGREEMENT_BOOST*100:.0f}% confidence boost")
            elif agreement_count >= 2:
                # Partial agreement (2+ methods): use configured boost
                agreement_adjustment = PARTIAL_AGREEMENT_BOOST
                logger.info(f"Partial agreement ({agreement_count}/{num_methods}): +{PARTIAL_AGREEMENT_BOOST*100:.0f}% confidence boost")
            elif agreement_count == 1:
                # No agreement (multiple methods disagree): use configured penalty
                agreement_adjustment = -NO_AGREEMENT_PENALTY
                logger.info(f"No agreement ({agreement_count}/{num_methods}): -{NO_AGREEMENT_PENALTY*100:.0f}% confidence penalty")
            else:
                agreement_adjustment = 0.0
        else:
            # Only one method available - no penalty, this is the best we have
            agreement_adjustment = 0.0
            logger.debug(f"Single method available ({methods_voted[0] if methods_voted else 'unknown'}): no adjustment")

        # Final confidence with calibration (capped at 0.05-1.0)
        # Use normalized_score instead of winner_score to account for active methods only
        final_confidence = max(0.05, min(1.0, normalized_score + agreement_adjustment))

        # Determine method string
        # Collect all methods that participated (not just those that voted for winner)
        all_participating_methods = []
        if mcc_result:
            all_participating_methods.append("mcc")
        if rule_result:
            all_participating_methods.append("rule")
        if ml_result:
            all_participating_methods.append("ml")
        if llm_result:
            all_participating_methods.append("llm")

        if agreement_count == num_methods and num_methods > 1:
            method = "ensemble_unanimous"
        elif num_methods > 1:
            # Show all participating methods, not just those that agreed
            method = f"ensemble_{'+'.join(all_participating_methods)}"
        else:
            method = methods_voted[0] if methods_voted else "ensemble"

        # Enhanced ambiguity scoring: Collect all alternatives and rank by voting
        alternatives = []

        # Add ML alternatives if available
        if ml_result and ml_result[2]:
            for alt_cat, alt_conf in ml_result[2]:
                if alt_cat != winner_category:
                    alternatives.append((alt_cat, alt_conf))

        # Add categories that received votes but didn't win
        for cat, vote_score in sorted(votes.items(), key=lambda x: x[1], reverse=True):
            if cat != winner_category and cat not in [a[0] for a in alternatives]:
                # Normalize vote score same way as winner
                normalized_alt_score = vote_score / total_active_weight if total_active_weight > 0 else vote_score
                alternatives.append((cat, normalized_alt_score))

        # Keep top 3 alternatives, sorted by confidence
        alternatives = sorted(alternatives, key=lambda x: x[1], reverse=True)[:3]

        # Calculate ambiguity score (0-1, higher = more ambiguous)
        if alternatives:
            # Ambiguity is high when top alternative is close to winner
            top_alternative_conf = alternatives[0][1] if alternatives else 0.0
            ambiguity_score = min(1.0, top_alternative_conf / (final_confidence + 0.001))
        else:
            ambiguity_score = 0.0

        # Store individual votes for transparency
        ensemble_votes = {
            "mcc": {"category": mcc_result[0], "confidence": mcc_result[1], "mcc_code": mcc_result[2]} if mcc_result else None,
            "rule": {"category": rule_result[0], "confidence": rule_result[1]} if rule_result else None,
            "ml": {"category": ml_result[0], "confidence": ml_result[1]} if ml_result else None,
            "llm": {"category": llm_result[0], "confidence": llm_result[1]} if llm_result else None,
            "weighted_votes": votes,
            "agreement_count": agreement_count,
            "total_methods": num_methods,
            "ambiguity_score": ambiguity_score
        }

        # Get category-specific review threshold
        category_review_threshold = self._get_category_threshold(winner_category, 'review')

        # Log final decision - moved to DEBUG to reduce log bloat at scale
        logger.debug(f"All votes: {votes}")
        logger.debug(f"Winner: '{winner_category}' with score {winner_score:.4f}")
        logger.debug(f"Agreement: {agreement_count}/{num_methods} methods agreed")
        logger.info(f"Categorized: '{winner_category}' (confidence: {final_confidence:.3f}, method: {method})")  # Concise INFO log
        logger.debug(f"Category-specific review threshold: {category_review_threshold:.3f}")
        logger.debug("=" * 35)

        return CategorizationResult(
            category=winner_category,
            subcategory=subcategory,
            confidence=final_confidence,
            method=method,
            explanations=explanations,
            alternatives=alternatives,
            requires_review=final_confidence < category_review_threshold,
            ensemble_votes=ensemble_votes,
            normalized_data=None  # Will be set by categorize() method
        )

    def categorize(
        self,
        text: str,
        amount: Optional[float] = None,
        date: Optional[str] = None,
        currency: str = "INR",
        merchant: Optional[str] = None,
        mcc: Optional[str] = None
    ) -> CategorizationResult:
        """
        Categorize a transaction using ensemble of all methods

        Args:
            text: Transaction description
            amount: Transaction amount
            date: Transaction date
            currency: Currency code
            merchant: Merchant name (optional, extracted from JSON)
            mcc: Merchant Category Code (optional, 4-digit code)

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
        # Use configured threshold for fuzzy matches (already high-quality from gazetteer)
        # Boost confidence when merchant is clearly identified
        #
        # IMPORTANT: Check for REFUND/RETURN keywords FIRST - these override merchant matches
        text_lower = text.lower()
        is_refund = any(keyword in text_lower for keyword in ['refund', 'return', 'reversal', 'chargeback'])

        if merchant_confidence >= MERCHANT_CONFIDENCE_THRESHOLD and not is_refund:
            # Boost confidence for merchant matches (they're highly reliable)
            boosted_confidence = min(0.95, merchant_confidence + MERCHANT_CONFIDENCE_BOOST)
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
                },
                normalized_data=normalized
            )
        elif is_refund:
            logger.info(f"REFUND/RETURN detected - skipping merchant early-exit, will use ensemble voting")

        # Step 3: Run categorizers (with fast mode optimization)
        mcc_result = None
        rule_result = None
        ml_result = None
        llm_result = None

        # Try rule-based FIRST for potential early exit (before MCC)
        # This ensures fraud/security and other high-priority deterministic rules take precedence
        if self.rule_categorizer:
            rule_result = self._run_rule_categorizer(
                search_text, resolved_merchant or merchant, channel, amount, date
            )

            # HIGH-CONFIDENCE RULE EARLY EXIT (deterministic rules like Fraud, ATM, EMI, Salary, Fuel)
            if rule_result and rule_result[1] >= RULE_EARLY_EXIT_THRESHOLD:
                logger.info(f"High-confidence deterministic rule: {rule_result[0]} ({rule_result[1]:.2%}) - skipping MCC/ML/LLM")
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
                        "mcc": None,
                        "ml": None,
                        "llm": None,
                        "weighted_votes": {rule_result[0]: rule_result[1]},
                        "agreement_count": 1,
                        "total_methods": 1
                    },
                    normalized_data=normalized
                )

        # Try MCC second - if high confidence MCC match, use it directly
        # (only if deterministic rules didn't match)
        if mcc and self.mcc_classifier:
            mcc_result = self._run_mcc_classifier(text, mcc)
            # HIGH-CONFIDENCE MCC EARLY EXIT (MCC codes are highly reliable)
            if mcc_result and mcc_result[1] >= MCC_EARLY_EXIT_THRESHOLD:
                logger.info(f"High-confidence MCC match: {mcc_result[0]} (code: {mcc_result[2]}, conf: {mcc_result[1]:.2%}) - skipping other methods")
                return CategorizationResult(
                    category=mcc_result[0],
                    subcategory=None,
                    confidence=mcc_result[1],
                    method="mcc_deterministic",
                    explanations=[f"mcc_code={mcc_result[2]}"],
                    requires_review=False,
                    merchant_resolved=resolved_merchant,
                    ensemble_votes={
                        "mcc": {"category": mcc_result[0], "confidence": mcc_result[1], "mcc_code": mcc_result[2]},
                        "rule": None,
                        "ml": None,
                        "llm": None,
                        "weighted_votes": {mcc_result[0]: mcc_result[1]},
                        "agreement_count": 1,
                        "total_methods": 1
                    },
                    normalized_data=normalized
                )

        if self.enable_parallel and self.executor:
            # Parallel execution with per-method timeouts
            futures = {}
            timeouts = {}

            # Don't re-run MCC if we already ran it for early exit check
            # (mcc_result will be None if not run, or < 0.90 if run but didn't exit)
            if mcc and self.mcc_classifier and mcc_result is None:
                futures['mcc'] = self.executor.submit(
                    self._run_mcc_classifier,
                    text, mcc
                )
                timeouts['mcc'] = 1.0  # MCC is instant

            # Don't re-run rule if we already ran it for early exit check
            # (rule_result will be None if not run, or < 0.95 if run but didn't exit)
            if self.rule_categorizer and rule_result is None:
                futures['rule'] = self.executor.submit(
                    self._run_rule_categorizer,
                    search_text, resolved_merchant or merchant, channel, amount, date
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
                # Wait for rule and ML first (but don't reset if already set from early-exit check)
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

                    # IMPORTANT: NEVER skip LLM if Rule and ML disagree!
                    if rule_cat != ml_cat:
                        should_skip_llm = False
                        logger.info(f"Rule+ML DISAGREE (Rule={rule_cat}, ML={ml_cat}) - LLM will make final decision")
                    # Check agreement and confidence
                    elif rule_cat == ml_cat and rule_conf >= self.fast_mode_threshold and ml_conf >= self.fast_mode_threshold:
                        should_skip_llm = True
                        min_conf = min(rule_conf, ml_conf)
                        logger.info(f"Fast mode: Rule+ML agree on '{rule_cat}' with confidence {min_conf:.2f} - skipping LLM")

                # Also skip if ML confidence is high enough (LLM fallback logic)
                # BUT NOT if Rule and ML disagreed (already handled above)
                if not should_skip_llm and ml_result and not (rule_result and rule_result[0] != ml_result[0]):
                    ml_conf = ml_result[1]
                    if ml_conf >= LLM_FALLBACK_THRESHOLD:
                        should_skip_llm = True
                        logger.info(f"LLM fallback: ML confidence {ml_conf:.2f} >= {LLM_FALLBACK_THRESHOLD} - skipping LLM")

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
                    if method == 'mcc':
                        mcc_result = result
                    elif method == 'rule':
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
            # Run MCC if not already run
            if mcc and self.mcc_classifier and mcc_result is None:
                mcc_result = self._run_mcc_classifier(text, mcc)

            # Run rules if not already run
            if self.rule_categorizer and rule_result is None:
                rule_result = self._run_rule_categorizer(
                    search_text, resolved_merchant or merchant, channel, amount, date
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

                # IMPORTANT: NEVER skip LLM if Rule and ML disagree!
                if rule_cat != ml_cat:
                    should_skip_llm = False
                    logger.info(f"Rule+ML DISAGREE (Rule={rule_cat}, ML={ml_cat}) - LLM will make final decision")
                elif rule_cat == ml_cat and rule_conf >= self.fast_mode_threshold and ml_conf >= self.fast_mode_threshold:
                    should_skip_llm = True
                    logger.info(f"Fast mode: Rule+ML agree on '{rule_cat}' - skipping LLM")

            # Also check ML confidence threshold (LLM fallback logic)
            # BUT NOT if Rule and ML disagreed (already handled above)
            if not should_skip_llm and ml_result and not (rule_result and rule_result[0] != ml_result[0]):
                ml_conf = ml_result[1]
                if ml_conf >= LLM_FALLBACK_THRESHOLD:
                    should_skip_llm = True
                    logger.info(f"LLM fallback: ML confidence {ml_conf:.2f} >= {LLM_FALLBACK_THRESHOLD} - skipping LLM")

            # Run LLM only if needed
            if should_skip_llm:
                llm_result = None
            else:
                logger.info("Running LLM as fallback for low-confidence prediction")
                llm_result = self._run_llm_classifier(text, amount)

        # Step 4: Ensemble voting
        result = self._ensemble_vote(mcc_result, rule_result, ml_result, llm_result)
        result.merchant_resolved = resolved_merchant
        result.normalized_data = normalized  # Attach normalized data to avoid duplicate work in API

        return result

    def categorize_batch(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[CategorizationResult]:
        """
        Categorize a batch of transactions

        Args:
            transactions: List of transaction dicts (can include 'mcc' field)

        Returns:
            List of CategorizationResult
        """
        results = []
        for txn in transactions:
            result = self.categorize(
                text=txn.get('text', txn.get('description', '')),
                amount=txn.get('amount'),
                date=txn.get('date', txn.get('timestamp')),
                currency=txn.get('currency', 'INR'),
                mcc=txn.get('mcc')
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
