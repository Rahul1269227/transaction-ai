#!/bin/bash

echo "Testing ML Model Improvements - Bills Category"
echo "=============================================="
echo ""

test_transaction() {
    local txn="$1"
    echo "Testing: $txn"
    echo "────────────────────────────────────────────"

    response=$(curl -s -X POST http://localhost:8000/categorize \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"$txn\"}")

    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Category:   {data[\"category\"]}')
print(f'Confidence: {data[\"confidence\"]:.1%}')
print('')
if data.get('ensemble_votes'):
    votes = data['ensemble_votes']
    if votes.get('ml'):
        print(f'ML:   {votes[\"ml\"][\"category\"]:25s} ({votes[\"ml\"][\"confidence\"]:.1%})')
    if votes.get('rule'):
        print(f'Rule: {votes[\"rule\"][\"category\"]:25s} ({votes[\"rule\"][\"confidence\"]:.1%})')
    if votes.get('llm'):
        print(f'LLM:  {votes[\"llm\"][\"category\"]:25s} ({votes[\"llm\"][\"confidence\"]:.1%})')
"
    echo ""
    echo ""
}

# Test Bills transactions
test_transaction "ELECTRICITY BILL PAYMENT"
test_transaction "WATER BILL"
test_transaction "PHONE BILL AIRTEL"

# Test other categories
test_transaction "NETFLIX SUBSCRIPTION"
test_transaction "STARBUCKS COFFEE"

echo "=============================================="
echo "Test complete!"
