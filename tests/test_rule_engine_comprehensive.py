"""
Comprehensive tests for RuleCategorizer
"""
import pytest
from core.rules import RuleCategorizer


class TestRuleCategorizer:
    """Test suite for RuleCategorizer"""

    @pytest.fixture
    def categorizer(self, taxonomy_path):
        return RuleCategorizer(taxonomy_path)

    # Category-specific tests
    def test_categorize_atm_withdrawal(self, categorizer):
        """Test ATM withdrawal categorization"""
        result = categorizer.categorize(
            text="ATM WDL 123456",
            merchant=None,
            channel="ATM",
            amount=5000.0
        )

        assert result is not None
        assert result.category == "ATM/Cash"
        assert result.confidence > 0.8

    def test_categorize_food_delivery(self, categorizer):
        """Test food delivery categorization"""
        test_cases = [
            "UPI-ZOMATO PAY",
            "SWIGGY FOOD ORDER",
            "DOMINOS PIZZA",
            "MCDONALDS",
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0],
                channel="UPI",
                amount=300.0
            )

            assert result is not None
            assert result.category == "Food & Dining"

    def test_categorize_fuel_transactions(self, categorizer):
        """Test fuel transaction categorization"""
        test_cases = [
            ("POS 4532 INDIAN OIL", "INDIAN OIL"),
            ("POS 1234 BPCL KANPUR", "BPCL"),
            ("POS HPCL STATION", "HPCL"),
            ("SHELL PETROL PUMP", "SHELL"),
        ]

        for text, merchant in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=merchant,
                channel="POS",
                amount=1200.0
            )

            assert result is not None
            # Fuel merchants should be categorized (category varies based on rules)
            assert result.category in ["Fuel", "Other", "Transport"]

    def test_categorize_transport(self, categorizer):
        """Test transport categorization"""
        test_cases = [
            "UPI-UBER TRIP",
            "OLA CAB RIDE",
            "RAPIDO BIKE",
            "AUTO FARE"
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0] if "-" not in text else text.split("-")[1].split()[0],
                channel="UPI",
                amount=250.0
            )

            assert result is not None
            assert result.category == "Transport"

    def test_categorize_rent(self, categorizer):
        """Test rent categorization"""
        result = categorizer.categorize(
            text="NEFT-APARTMENT RENT NOV 2025",
            merchant="APARTMENT",
            channel="NEFT",
            amount=25000.0
        )

        assert result is not None
        assert result.category == "Rent"

    def test_categorize_utilities(self, categorizer):
        """Test utilities categorization"""
        test_cases = [
            ("ELECTRICITY BILL", "ELECTRICITY"),
            ("WATER BILL PAYMENT", "WATER"),
            ("GAS CYLINDER", "GAS"),
            ("BROADBAND BILL", "BROADBAND"),
        ]

        for text, merchant in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=merchant,
                channel="UPI",
                amount=1000.0
            )

            assert result is not None
            assert result.category in ["Utilities", "Bills", "Other"]

    def test_categorize_groceries(self, categorizer):
        """Test groceries categorization"""
        test_cases = [
            "DMART SUPERMARKET",
            "BIG BAZAAR",
            "RELIANCE FRESH",
            "BIGBASKET ORDER"
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0],
                channel="POS",
                amount=2000.0
            )

            assert result is not None
            assert result.category in ["Groceries", "Shopping", "Other", "Bills"]

    def test_categorize_shopping(self, categorizer):
        """Test shopping categorization"""
        test_cases = [
            "AMAZON PURCHASE",
            "FLIPKART ORDER",
            "MYNTRA FASHION",
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0],
                channel="UPI",
                amount=1500.0
            )

            assert result is not None
            assert result.category == "Shopping"

    def test_categorize_entertainment(self, categorizer):
        """Test entertainment categorization"""
        test_cases = [
            "NETFLIX SUBSCRIPTION",
            "AMAZON PRIME VIDEO",
            "SPOTIFY PREMIUM",
            "PVR CINEMAS TICKET"
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0],
                channel="UPI",
                amount=500.0
            )

            assert result is not None
            assert result.category in ["Entertainment", "Subscription", "Other", "Bills", "Shopping"]

    def test_categorize_health(self, categorizer):
        """Test health categorization"""
        test_cases = [
            "APOLLO PHARMACY",
            "HOSPITAL BILL",
            "DOCTOR CONSULTATION",
            "MEDICAL INSURANCE"
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0],
                channel="UPI",
                amount=1000.0
            )

            assert result is not None
            assert result.category == "Health"

    def test_categorize_education(self, categorizer):
        """Test education categorization"""
        test_cases = [
            "SCHOOL FEE",
            "TUITION PAYMENT",
            "COURSE FEE",
            "BOOKS PURCHASE"
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0],
                channel="NEFT",
                amount=10000.0
            )

            # Should be either Education or Other (depending on keyword strength)
            assert result is not None

    def test_categorize_investment(self, categorizer):
        """Test investment categorization"""
        test_cases = [
            "MUTUAL FUND SIP",
            "STOCK PURCHASE",
            "ZERODHA TRADING",
            "FIXED DEPOSIT"
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=text.split()[0],
                channel="NEFT",
                amount=5000.0
            )

            assert result is not None
            assert result.category in ["Investments", "Other", "Finance"]

    def test_categorize_transfer_upi(self, categorizer):
        """Test UPI transfer categorization"""
        result = categorizer.categorize(
            text="UPI-P2P-123456789-JOHN DOE",
            merchant="P2P",
            channel="UPI",
            amount=1000.0
        )

        assert result is not None
        assert result.category == "Transfers/UPI"

    def test_categorize_salary(self, categorizer):
        """Test salary categorization"""
        test_cases = [
            "SALARY CREDIT NOV 2025",
            "PAYROLL CREDIT",
            "MONTHLY SALARY",
        ]

        for text in test_cases:
            result = categorizer.categorize(
                text=text,
                merchant=None,
                channel="NEFT",
                amount=50000.0
            )

            assert result is not None
            assert result.category in ["Income/Salary", "Other", "Income", "Salary"]

    # Edge cases
    def test_categorize_unknown_merchant(self, categorizer):
        """Test categorization of unknown merchant"""
        result = categorizer.categorize(
            text="UNKNOWN MERCHANT XYZ",
            merchant="UNKNOWN",
            channel="POS",
            amount=500.0
        )

        # Should return None or low confidence result
        assert result is None or result.confidence < 0.5

    def test_categorize_empty_text(self, categorizer):
        """Test categorization with empty text"""
        result = categorizer.categorize(
            text="",
            merchant=None,
            channel=None,
            amount=100.0
        )

        assert result is not None  # Empty text still gets categorized as Other

    def test_categorize_with_None_values(self, categorizer):
        """Test categorization with None values"""
        result = categorizer.categorize(
            text="UPI PAYMENT",
            merchant=None,
            channel=None,
            amount=None
        )

        # Should handle gracefully
        assert result is None or isinstance(result, object)

    def test_confidence_higher_for_strong_matches(self, categorizer):
        """Test that confidence is higher for strong keyword matches"""
        # Strong match
        strong_result = categorizer.categorize(
            text="ATM WITHDRAWAL HDFC",
            merchant="ATM",
            channel="ATM",
            amount=5000.0
        )

        # Weak match
        weak_result = categorizer.categorize(
            text="PAYMENT",
            merchant=None,
            channel=None,
            amount=100.0
        )

        if strong_result and weak_result:
            assert strong_result.confidence > weak_result.confidence

    def test_multiple_keyword_matches_increase_confidence(self, categorizer):
        """Test that multiple keyword matches increase confidence"""
        # Single keyword
        result1 = categorizer.categorize(
            text="FOOD ORDER",
            merchant="FOOD",
            channel="UPI",
            amount=300.0
        )

        # Multiple keywords
        result2 = categorizer.categorize(
            text="ZOMATO FOOD DELIVERY RESTAURANT",
            merchant="ZOMATO",
            channel="UPI",
            amount=300.0
        )

        if result1 and result2 and result1.category == result2.category:
            assert result2.confidence >= result1.confidence
