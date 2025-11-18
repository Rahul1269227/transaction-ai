#!/bin/bash

echo "════════════════════════════════════════════════════════════════════"
echo "🧪 Testing Transaction Categorization API with Redis Caching"
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Test transactions
transactions=(
  "Netflix monthly subscription"
  "Starbucks coffee Grande"
  "Uber ride to airport"
  "Amazon electronics shopping"
  "CVS Pharmacy medicines"
  "LIC Insurance Premium"
  "IKEA furniture purchase"
  "Gym membership fee"
)

for txn in "${transactions[@]}"; do
  echo "════════════════════════════════════════════════════════════════════"
  echo "Testing: $txn"
  echo "────────────────────────────────────────────────────────────────────"

  # First request (should use model, then cache)
  echo "First request (caching):"
  curl -s -X POST http://localhost:8000/categorize \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$txn\"}" | python3 -m json.tool

  echo ""
  echo "Second request (should use cache):"
  # Second request (should use cache)
  curl -s -X POST http://localhost:8000/categorize \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$txn\"}" | python3 -m json.tool

  echo ""
done

echo "════════════════════════════════════════════════════════════════════"
echo "✅ Testing Complete!"
echo "════════════════════════════════════════════════════════════════════"
