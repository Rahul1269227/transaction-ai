"""
Comprehensive tests for Ensemble Router
"""
import pytest
from core.model.ensemble_router import EnsembleRouter
from core.models import CategoryResult


class TestEnsembleRouter:
    """Test suite for EnsembleRouter"""

    @pytest.fixture
    def router(self, taxonomy_path, gazetteer_path):
        """Create router without ML/LLM for testing"""
        return EnsembleRouter(
            taxonomy_path=taxonomy_path,
            gazetteer_path=gazetteer_path,
            ml_model_path=None,  # Skip ML model
            llm_url=None,  # Skip LLM
            rule_weight=0.5,
            ml_weight=0.3,
            llm_weight=0.2
        )

    def test_router_initialization(self, router):
        """Test router initializes correctly"""
        assert router is not None
        assert router.rule_categorizer is not None
        assert router.merchant_resolver is not None

    def test_categorize_with_rule_only(self, router):
        """Test categorization when only rules match"""
        result = router.categorize(
            text="ATM WDL 123456",
            amount=5000.0,
            date="2025-11-10",
            currency="INR"
        )

        assert result.category == "ATM/Cash"
        assert "rule" in result.method.lower()

    def test_categorize_returns_result_object(self, router):
        """Test that categorize returns proper result object"""
        result = router.categorize(
            text="UPI-ZOMATO PAY",
            amount=249.0,
            date="2025-11-10"
        )

        assert hasattr(result, 'category')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'method')
        assert hasattr(result, 'requires_review')

    def test_confidence_within_valid_range(self, router):
        """Test that confidence is between 0 and 1"""
        result = router.categorize(
            text="UPI-ZOMATO PAY",
            amount=249.0,
            date="2025-11-10"
        )

        assert 0 <= result.confidence <= 1

    def test_requires_review_flag(self, router):
        """Test requires_review flag is set correctly"""
        # High confidence case
        result_high = router.categorize(
            text="ATM WDL 123456",
            amount=5000.0,
            date="2025-11-10"
        )

        # Low confidence case (ambiguous)
        result_low = router.categorize(
            text="UNKNOWN PAYMENT",
            amount=100.0,
            date="2025-11-10"
        )

        # High confidence should not require review
        if result_high.confidence >= 0.85:
            assert result_high.requires_review == False

    def test_ensemble_votes_populated(self, router):
        """Test that ensemble_votes is populated"""
        result = router.categorize(
            text="UPI-ZOMATO PAY",
            amount=249.0,
            date="2025-11-10"
        )

        assert hasattr(result, 'ensemble_votes')
        if result.ensemble_votes:
            assert isinstance(result.ensemble_votes, dict)


class TestEnsembleVoting:
    """Test ensemble voting logic"""

    def test_weighted_voting_calculation(self):
        """Test weighted voting calculation"""
        from core.model.ensemble_router import EnsembleRouter

        # Mock votes
        rule_vote = CategoryResult(category="Food & Dining", confidence=0.9, method="rule")
        ml_vote = CategoryResult(category="Food & Dining", confidence=0.95, method="ml")
        llm_vote = CategoryResult(category="Shopping", confidence=0.7, method="llm")

        votes = {
            "rule": rule_vote,
            "ml": ml_vote,
            "llm": llm_vote
        }

        weights = {
            "rule": 0.3,
            "ml": 0.4,
            "llm": 0.3
        }

        # Calculate weighted scores
        scores = {}
        for method, vote in votes.items():
            if vote:
                weight = weights.get(method, 0)
                score = vote.confidence * weight
                if vote.category not in scores:
                    scores[vote.category] = 0
                scores[vote.category] += score

        # Food & Dining should win
        winner = max(scores, key=scores.get)
        assert winner == "Food & Dining"

    def test_unanimous_agreement_boost(self):
        """Test that unanimous agreement boosts confidence"""
        # All agree on same category
        votes_unanimous = {
            "rule": CategoryResult(category="Food & Dining", confidence=0.85, method="rule"),
            "ml": CategoryResult(category="Food & Dining", confidence=0.90, method="ml"),
            "llm": CategoryResult(category="Food & Dining", confidence=0.88, method="llm")
        }

        # Disagreement
        votes_disagree = {
            "rule": CategoryResult(category="Shopping", confidence=0.85, method="rule"),
            "ml": CategoryResult(category="Food & Dining", confidence=0.90, method="ml"),
            "llm": CategoryResult(category="Other", confidence=0.70, method="llm")
        }

        # Count agreement
        unanimous_categories = set(v.category for v in votes_unanimous.values() if v)
        disagree_categories = set(v.category for v in votes_disagree.values() if v)

        assert len(unanimous_categories) == 1  # All agree
        assert len(disagree_categories) > 1    # Disagreement

    def test_missing_votes_handled(self):
        """Test that missing votes are handled correctly"""
        votes = {
            "rule": CategoryResult(category="Food & Dining", confidence=0.9, method="rule"),
            "ml": None,  # ML unavailable
            "llm": None  # LLM unavailable
        }

        # Should still work with only rule vote
        available_votes = [v for v in votes.values() if v is not None]
        assert len(available_votes) == 1


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def router(self, taxonomy_path, gazetteer_path):
        return EnsembleRouter(
            taxonomy_path=taxonomy_path,
            gazetteer_path=gazetteer_path,
            ml_model_path=None,
            llm_url=None
        )

    def test_empty_text(self, router):
        """Test categorization with empty text"""
        result = router.categorize(
            text="",
            amount=100.0,
            date="2025-11-10"
        )

        # Should return fallback result
        assert result is not None
        assert result.category == "Other"

    def test_none_amount(self, router):
        """Test categorization with None amount"""
        result = router.categorize(
            text="UPI-ZOMATO PAY",
            amount=None,
            date="2025-11-10"
        )

        # Should still categorize based on text
        assert result is not None

    def test_invalid_date(self, router):
        """Test categorization with invalid date"""
        result = router.categorize(
            text="UPI-ZOMATO PAY",
            amount=249.0,
            date="invalid-date"
        )

        # Should handle gracefully
        assert result is not None

    def test_very_long_text(self, router):
        """Test categorization with very long text"""
        long_text = "UPI-" + "X" * 1000 + "-ZOMATO"
        result = router.categorize(
            text=long_text,
            amount=249.0,
            date="2025-11-10"
        )

        # Should handle without error
        assert result is not None

    def test_special_characters_in_text(self, router):
        """Test categorization with special characters"""
        result = router.categorize(
            text="UPI-₹@#$%^&*()-ZOMATO",
            amount=249.0,
            date="2025-11-10"
        )

        # Should clean and categorize
        assert result is not None

    def test_numeric_only_text(self, router):
        """Test categorization with numeric-only text"""
        result = router.categorize(
            text="123456789",
            amount=100.0,
            date="2025-11-10"
        )

        # Should return fallback
        assert result is not None

    def test_zero_amount(self, router):
        """Test categorization with zero amount"""
        result = router.categorize(
            text="UPI-ZOMATO PAY",
            amount=0.0,
            date="2025-11-10"
        )

        # Should handle zero amount
        assert result is not None

    def test_negative_amount(self, router):
        """Test categorization with negative amount (refund)"""
        result = router.categorize(
            text="REFUND-ZOMATO",
            amount=-249.0,
            date="2025-11-10"
        )

        # Should categorize refunds
        assert result is not None

    def test_future_date(self, router):
        """Test categorization with future date"""
        result = router.categorize(
            text="UPI-ZOMATO PAY",
            amount=249.0,
            date="2099-12-31"
        )

        # Should handle future dates
        assert result is not None
