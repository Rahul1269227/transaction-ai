"""
Comprehensive tests for TransactionNormalizer
"""
import pytest
from core.normalize import TransactionNormalizer, FeatureExtractor


class TestTransactionNormalizer:
    """Test suite for TransactionNormalizer"""

    @pytest.fixture
    def normalizer(self):
        return TransactionNormalizer()

    def test_normalize_upi_transaction(self, normalizer):
        """Test UPI transaction normalization"""
        result = normalizer.normalize(
            text="UPI-123456-ZOMATO PAY*ABCD",
            amount=249.0,
            date="2025-11-10",
            currency="INR"
        )

        assert result["pattern_match"]["channel"] == "UPI"
        assert "ZOMATO" in result["normalized"]["merchant"].upper()
        assert result["normalized"]["amount"] == 249.0

    def test_normalize_atm_transaction(self, normalizer):
        """Test ATM transaction normalization"""
        result = normalizer.normalize(
            text="ATM WDL 123456 AXIS BANK",
            amount=5000.0,
            date="2025-11-10"
        )

        assert result["pattern_match"]["channel"] == "ATM"
        assert result["normalized"]["amount"] == 5000.0

    def test_normalize_pos_transaction(self, normalizer):
        """Test POS transaction normalization"""
        result = normalizer.normalize(
            text="POS 4532 INDIAN OIL KANPUR",
            amount=1200.0,
            date="2025-11-10"
        )

        assert result["pattern_match"]["channel"] == "POS"
        assert "INDIAN OIL" in result["normalized"]["text"]

    def test_normalize_neft_transaction(self, normalizer):
        """Test NEFT transaction normalization"""
        result = normalizer.normalize(
            text="NEFT-INTERNAL FUND TRANSFER",
            amount=25000.0,
            date="2025-11-01"
        )

        assert result["pattern_match"]["channel"] in ["NEFT", "INTERNAL"]

    def test_normalize_imps_transaction(self, normalizer):
        """Test IMPS transaction normalization"""
        result = normalizer.normalize(
            text="IMPS-P2P/123456789/JOHN DOE",
            amount=1000.0,
            date="2025-11-10"
        )

        assert result["pattern_match"]["channel"] == "IMPS"

    def test_normalize_with_special_characters(self, normalizer):
        """Test normalization with special characters"""
        result = normalizer.normalize(
            text="UPI-ZOMATO@PAYTM-₹249.00",
            amount=249.0,
            date="2025-11-10"
        )

        assert "ZOMATO" in result["normalized"]["text"]
        # Should clean special characters
        assert "₹" not in result["normalized"]["text"]

    def test_normalize_lowercase_text(self, normalizer):
        """Test normalization converts to uppercase"""
        result = normalizer.normalize(
            text="upi-zomato pay",
            amount=100.0,
            date="2025-11-10"
        )

        # Normalized text should be uppercase
        assert result["normalized"]["text"].isupper()

    def test_normalize_extracts_merchant_from_complex_text(self, normalizer):
        """Test merchant extraction from complex transaction text"""
        result = normalizer.normalize(
            text="UPI-P2M-123456789-ZOMATO PAY*RESTAURANT@PAYTM",
            amount=500.0,
            date="2025-11-10"
        )

        assert result["normalized"]["merchant"] is not None
        assert "ZOMATO" in result["normalized"]["merchant"].upper()

    def test_normalize_handles_missing_amount(self, normalizer):
        """Test normalization with missing amount"""
        result = normalizer.normalize(
            text="UPI-ZOMATO PAY",
            amount=None,
            date="2025-11-10"
        )

        assert result["normalized"]["amount"] is None

    def test_normalize_handles_invalid_date(self, normalizer):
        """Test normalization with invalid date"""
        result = normalizer.normalize(
            text="UPI-ZOMATO PAY",
            amount=249.0,
            date="invalid-date"
        )

        # Should still process successfully
        assert result is not None


class TestFeatureExtractor:
    """Test suite for FeatureExtractor"""

    @pytest.fixture
    def extractor(self):
        return FeatureExtractor()

    def test_extract_amount_features(self, extractor):
        """Test amount-based feature extraction"""
        normalized = {
            "text": "UPI ZOMATO",
            "amount": 1000.0,
            "date": "2025-11-10",
            "merchant": "ZOMATO",
            "channel": "UPI"
        }

        features = extractor.extract_features(normalized)

        assert "amount" in features
        assert "amount_log" in features
        assert "amount_bucket" in features
        assert features["amount"] == 1000.0
        assert features["amount_log"] > 0

    def test_extract_temporal_features(self, extractor):
        """Test temporal feature extraction"""
        normalized = {
            "text": "UPI ZOMATO",
            "amount": 100.0,
            "date": "2025-11-10",  # November 10
            "merchant": "ZOMATO",
            "channel": "UPI"
        }

        features = extractor.extract_features(normalized)

        assert "day_of_month" in features
        assert "month" in features
        assert "is_weekend" in features
        assert features["day_of_month"] == 10
        assert features["month"] == 11

    def test_extract_text_features(self, extractor):
        """Test text-based feature extraction"""
        normalized = {
            "text": "UPI-123456 ZOMATO PAY",
            "amount": 100.0,
            "date": "2025-11-10",
            "merchant": "ZOMATO",
            "channel": "UPI"
        }

        features = extractor.extract_features(normalized)

        assert "text_length" in features
        assert "digit_ratio" in features
        assert "special_char_ratio" in features
        assert features["text_length"] > 0
        assert 0 <= features["digit_ratio"] <= 1

    def test_extract_channel_features(self, extractor):
        """Test channel-based feature extraction"""
        normalized = {
            "text": "UPI ZOMATO",
            "amount": 100.0,
            "date": "2025-11-10",
            "merchant": "ZOMATO",
            "channel": "UPI"
        }

        features = extractor.extract_features(normalized)

        # Should have one-hot encoded channel features
        assert any(key.startswith("channel_") for key in features.keys())

    def test_extract_features_handles_missing_values(self, extractor):
        """Test feature extraction with missing values"""
        normalized = {
            "text": "UNKNOWN TRANSACTION",
            "amount": None,
            "date": None,
            "merchant": None,
            "channel": None
        }

        features = extractor.extract_features(normalized)

        # Should still return features with defaults
        assert features is not None
        assert isinstance(features, dict)

    def test_amount_bucket_categorization(self, extractor):
        """Test amount bucketing"""
        test_cases = [
            (50, "small"),
            (500, "medium"),
            (5000, "large"),
            (50000, "very_large")
        ]

        for amount, expected_bucket in test_cases:
            normalized = {
                "text": "TEST",
                "amount": amount,
                "date": "2025-11-10",
                "merchant": "TEST",
                "channel": "UPI"
            }
            features = extractor.extract_features(normalized)
            assert features["amount_bucket"] in ["small", "medium", "large", "very_large"]

    def test_amount_rounded_detection(self, extractor):
        """Test detection of rounded amounts"""
        # Rounded amounts
        for amount in [100, 500, 1000, 5000]:
            normalized = {
                "text": "TEST",
                "amount": float(amount),
                "date": "2025-11-10",
                "merchant": "TEST",
                "channel": "UPI"
            }
            features = extractor.extract_features(normalized)
            assert features.get("amount_rounded_to_100", 0) == 1 or features.get("amount_rounded_to_500", 0) == 1

    def test_weekend_detection(self, extractor):
        """Test weekend detection"""
        # 2025-11-08 is a Saturday
        normalized = {
            "text": "TEST",
            "amount": 100.0,
            "date": "2025-11-08",
            "merchant": "TEST",
            "channel": "UPI"
        }
        features = extractor.extract_features(normalized)
        assert features.get("is_weekend", 0) == 1
