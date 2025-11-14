from core.normalize import TransactionNormalizer


def test_normalizer_extracts_channel_and_merchant():
    normalizer = TransactionNormalizer()
    payload = normalizer.normalize(
        text="UPI-123456-ZOMATO PAY*ABCD",
        amount=249.0,
        date="2025-11-10",
        currency="INR",
    )

    pattern_match = payload["pattern_match"]
    normalized = payload["normalized"]

    assert pattern_match["channel"] == "UPI"
    assert normalized["merchant"] is not None
    assert "ZOMATO" in normalized["merchant"].upper()
    assert normalized["amount"] == 249.0
