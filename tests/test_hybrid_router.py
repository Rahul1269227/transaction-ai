from pathlib import Path

from core.model import HybridRouter


def test_hybrid_router_returns_rule_category():
    base_dir = Path(__file__).resolve().parents[1]
    router = HybridRouter(
        taxonomy_path=str(base_dir / "data" / "taxonomy.yaml"),
        gazetteer_path=str(base_dir / "data" / "gazetteer" / "merchant_aliases.csv"),
        model_path=None,
        auto_accept_threshold=0.85,
        review_threshold=0.60,
    )

    result = router.categorize(
        text="UPI-1234-ZOMATO PAY",
        amount=300.0,
        date="2025-11-11",
        currency="INR",
    )

    assert result.category == "Food & Dining"
    assert result.method in {"rule", "hybrid"}
    assert result.confidence > 0.5
