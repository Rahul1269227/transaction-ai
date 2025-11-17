# Test Suite

Comprehensive test suite for Transaction AI Categorization System

## Test Coverage

Total: **75 tests** across 6 test files

### Test Files

1. **`conftest.py`** - Pytest fixtures and configuration
2. **`test_normalizer_comprehensive.py`** - 18 tests for normalization and feature extraction
3. **`test_rule_engine_comprehensive.py`** - 24 tests for rule-based categorization
4. **`test_ensemble_router.py`** - 18 tests for ensemble voting logic
5. **`test_merchant_resolver.py`** - 16 tests for merchant resolution
6. **`test_normalizer.py`** - 1 original test (kept for backwards compatibility)
7. **`test_rule_engine.py`** - 1 original test (kept for backwards compatibility)
8. **`test_hybrid_router.py`** - 1 original test (kept for backwards compatibility)

### Test Results Summary

```
26 PASSED (35%)
34 FAILED (45%) - mostly due to API mismatches to fix
15 ERRORS (20%) - need fixture updates
```

## Running Tests

### Run All Tests
```bash
python3 -m pytest tests/ -v
```

### Run Specific Test File
```bash
python3 -m pytest tests/test_normalizer_comprehensive.py -v
```

### Run Specific Test Class
```bash
python3 -m pytest tests/test_normalizer_comprehensive.py::TestTransactionNormalizer -v
```

### Run Specific Test
```bash
python3 -m pytest tests/test_normalizer_comprehensive.py::TestTransactionNormalizer::test_normalize_upi_transaction -v
```

### Run with Coverage
```bash
python3 -m pytest tests/ --cov=core --cov-report=html
```

## Test Coverage by Component

### 1. Transaction Normalizer (18 tests)
- ✅ UPI transaction normalization
- ✅ ATM transaction normalization
- ⚠️  POS transaction normalization
- ⚠️  NEFT/IMPS transaction normalization
- ✅ Special character handling
- ✅ Missing/invalid data handling

### 2. Feature Extractor (9 tests)
- ⚠️  Amount-based features
- ⚠️  Temporal features
- ⚠️  Text features
- ⚠️  Channel features
- ✅ Missing value handling
- ⚠️  Feature bucketing

### 3. Rule Categorizer (24 tests)
- ✅ ATM/Cash categorization
- ✅ Food & Dining categorization
- ⚠️  Fuel categorization
- ✅ Transport categorization
- ✅ Rent categorization
- ⚠️  Utilities categorization
- ⚠️  Groceries categorization
- ✅ Shopping categorization
- ⚠️  Entertainment categorization
- ✅ Health categorization
- ✅ Education categorization
- ⚠️  Investment categorization
- ✅ Transfers/UPI categorization
- ⚠️  Income/Salary categorization
- ✅ Edge cases (unknown, empty, None)

### 4. Ensemble Router (18 tests)
- ⚠️  Router initialization
- ⚠️  Rule-only categorization
- ✅ Weighted voting calculation
- ✅ Unanimous agreement boost
- ✅ Missing votes handling
- ⚠️  Edge cases (empty, None, special chars)

### 5. Merchant Resolver (16 tests)
- ✅ Merchant loading
- ⚠️  Exact/fuzzy matching
- ⚠️  Case sensitivity
- ⚠️  Alias resolution
- ⚠️  Unknown merchant handling
- ⚠️  Category mapping
- ✅ Search functionality

## Known Issues to Fix

### 1. Ensemble Router Tests
- **Issue**: `TypeError: __init__() got an unexpected keyword argument 'model_path'`
- **Fix needed**: Update fixture to match actual EnsembleRouter constructor

### 2. Merchant Resolver Tests
- **Issue**: `AttributeError: 'list' object has no attribute 'canonical_name'`
- **Fix needed**: Update tests to match actual return type (list vs object)

### 3. Normalizer Tests
- **Issue**: Some assertions don't match actual normalized output format
- **Fix needed**: Update assertions to match actual data structure

### 4. Rule Engine Tests
- **Issue**: Some categories not matching expected results
- **Fix needed**: Update test cases or improve keyword matching

## Next Steps

1. Fix API mismatches in ensemble router tests
2. Update merchant resolver tests to handle list returns
3. Align normalizer test assertions with actual output
4. Add integration tests for full pipeline
5. Add performance/benchmark tests
6. Increase coverage to 80%+

## Test Philosophy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test components working together
- **Edge Cases**: Test error handling and boundary conditions
- **Regression Tests**: Prevent bugs from reoccurring

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure existing tests still pass
3. Add edge case tests
4. Update this README

## References

- Pytest Documentation: https://docs.pytest.org
- Python Testing Best Practices: https://realpython.com/pytest-python-testing/
