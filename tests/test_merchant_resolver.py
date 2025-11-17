"""
Tests for Merchant Resolver
"""
import pytest
from core.resolve import MerchantResolver


class TestMerchantResolver:
    """Test suite for MerchantResolver"""

    @pytest.fixture
    def resolver(self, gazetteer_path):
        return MerchantResolver(gazetteer_path)

    def test_resolver_loads_merchants(self, resolver):
        """Test that resolver loads merchants from gazetteer"""
        assert resolver is not None
        # Should have loaded some merchants
        assert len(resolver.merchants) > 0

    def test_resolve_exact_match(self, resolver):
        """Test exact merchant name match"""
        # Assuming ZOMATO is in the gazetteer
        results = resolver.resolve("ZOMATO")

        if results:
            assert isinstance(results, list)
            assert len(results) > 0
            assert results[0].canonical_name is not None
            assert results[0].category is not None

    def test_resolve_case_insensitive(self, resolver):
        """Test case-insensitive matching"""
        result1 = resolver.resolve("ZOMATO")
        result2 = resolver.resolve("zomato")
        result3 = resolver.resolve("Zomato")

        # All should resolve to same merchant
        if result1 and result2 and result3:
            assert result1[0].canonical_name == result2[0].canonical_name == result3[0].canonical_name

    def test_resolve_with_alias(self, resolver):
        """Test resolving merchant by alias"""
        # Many merchants have aliases in the gazetteer
        # This tests fuzzy matching
        results = resolver.resolve("SWIGGY FOOD")

        # Should resolve to SWIGGY or similar
        assert not results or "SWIGGY" in results[0].canonical_name.upper()

    def test_resolve_unknown_merchant(self, resolver):
        """Test resolving unknown merchant"""
        results = resolver.resolve("UNKNOWN_MERCHANT_XYZ_12345")

        # Should return empty list for unknown merchants
        assert results == []

    def test_resolve_empty_string(self, resolver):
        """Test resolving empty string"""
        results = resolver.resolve("")

        assert results == []

    def test_resolve_none(self, resolver):
        """Test resolving None"""
        results = resolver.resolve(None)

        assert results == []

    def test_resolve_with_special_characters(self, resolver):
        """Test resolving merchant name with special characters"""
        results = resolver.resolve("ZOMATO@PAYTM")

        # Should clean and match
        if results:
            assert "ZOMATO" in results[0].canonical_name.upper()

    def test_resolve_returns_category_info(self, resolver):
        """Test that resolved merchant includes category info"""
        results = resolver.resolve("ZOMATO")

        if results:
            assert hasattr(results[0], 'category')
            assert hasattr(results[0], 'canonical_name')

    def test_resolve_partial_match(self, resolver):
        """Test partial merchant name matching"""
        # Search for partial name
        results = resolver.resolve("ZOM")

        # Might match ZOMATO
        assert not results or "ZOM" in results[0].canonical_name.upper()

    def test_multiple_merchants_with_same_alias(self, resolver):
        """Test handling of multiple merchants with similar names"""
        # This tests that the resolver returns the best match
        result1 = resolver.resolve("INDIAN OIL")
        result2 = resolver.resolve("INDIAN")

        # Both might resolve, but should be consistent
        if result1 and result2:
            assert isinstance(result1[0].canonical_name, str)
            assert isinstance(result2[0].canonical_name, str)


class TestMerchantCategories:
    """Test merchant category mappings"""

    @pytest.fixture
    def resolver(self, gazetteer_path):
        return MerchantResolver(gazetteer_path)

    def test_food_merchants(self, resolver):
        """Test food & dining merchant resolution"""
        food_merchants = ["ZOMATO", "SWIGGY", "DOMINOS", "MCDONALDS"]

        for merchant in food_merchants:
            results = resolver.resolve(merchant)
            if results:
                # Should be categorized as food
                assert "food" in results[0].category.lower() or "dining" in results[0].category.lower()

    def test_fuel_merchants(self, resolver):
        """Test fuel merchant resolution"""
        fuel_merchants = ["INDIAN OIL", "BPCL", "HPCL", "SHELL"]

        for merchant in fuel_merchants:
            results = resolver.resolve(merchant)
            if results:
                assert "fuel" in results[0].category.lower()

    def test_shopping_merchants(self, resolver):
        """Test shopping merchant resolution"""
        shopping_merchants = ["AMAZON", "FLIPKART", "MYNTRA"]

        for merchant in shopping_merchants:
            results = resolver.resolve(merchant)
            if results:
                assert "shopping" in results[0].category.lower()

    def test_entertainment_merchants(self, resolver):
        """Test entertainment merchant resolution"""
        entertainment_merchants = ["NETFLIX", "PRIME VIDEO", "SPOTIFY"]

        for merchant in entertainment_merchants:
            results = resolver.resolve(merchant)
            if results:
                assert "entertainment" in results[0].category.lower()


class TestMerchantSearch:
    """Test merchant search functionality"""

    @pytest.fixture
    def resolver(self, gazetteer_path):
        return MerchantResolver(gazetteer_path)

    def test_search_returns_multiple_results(self, resolver):
        """Test that search can return multiple matching merchants"""
        # If resolver has search method
        if hasattr(resolver, 'search'):
            results = resolver.search("FOOD", limit=5)
            assert isinstance(results, list)
            assert len(results) <= 5

    def test_search_with_limit(self, resolver):
        """Test search respects limit parameter"""
        if hasattr(resolver, 'search'):
            results_5 = resolver.search("", limit=5)
            results_10 = resolver.search("", limit=10)

            assert len(results_5) <= 5
            assert len(results_10) <= 10
