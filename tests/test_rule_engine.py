from pathlib import Path

from core.rules import RuleCategorizer


def test_rule_engine_matches_food_category():
    taxonomy_path = Path(__file__).resolve().parents[1] / "data" / "taxonomy.yaml"
    categorizer = RuleCategorizer(str(taxonomy_path))

    result = categorizer.categorize(
        text="UPI-1234-ZOMATO PAY",
        merchant="ZOMATO",
        channel="UPI",
        amount=250.0,
    )

    assert result is not None
    assert result.category == "Food & Dining"
    assert result.confidence > 0.5
