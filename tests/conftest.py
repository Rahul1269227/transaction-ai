"""
Pytest configuration and fixtures
"""
import pytest
from pathlib import Path


@pytest.fixture
def base_dir():
    """Get base directory of the project"""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def taxonomy_path(base_dir):
    """Get path to taxonomy file"""
    return str(base_dir / "data" / "taxonomy.yaml")


@pytest.fixture
def gazetteer_path(base_dir):
    """Get path to gazetteer file"""
    return str(base_dir / "data" / "gazetteer" / "merchant_aliases.csv")


@pytest.fixture
def model_path(base_dir):
    """Get path to trained model"""
    model_dir = base_dir / "models" / "transaction_classifier"
    if model_dir.exists():
        return str(model_dir)
    return None


@pytest.fixture
def sample_transactions():
    """Sample transactions for testing"""
    return [
        {
            "text": "UPI-ZOMATO PAY*1234",
            "amount": 249.0,
            "date": "2025-11-10",
            "currency": "INR",
            "expected_category": "Food & Dining"
        },
        {
            "text": "ATM WDL 123456",
            "amount": 5000.0,
            "date": "2025-11-10",
            "currency": "INR",
            "expected_category": "ATM/Cash"
        },
        {
            "text": "POS 4532 INDIAN OIL",
            "amount": 1200.0,
            "date": "2025-11-10",
            "currency": "INR",
            "expected_category": "Fuel"
        },
        {
            "text": "NEFT-APARTMENT RENT",
            "amount": 25000.0,
            "date": "2025-11-01",
            "currency": "INR",
            "expected_category": "Rent"
        },
        {
            "text": "UPI-UBER TRIP",
            "amount": 250.0,
            "date": "2025-11-10",
            "currency": "INR",
            "expected_category": "Transport"
        }
    ]
