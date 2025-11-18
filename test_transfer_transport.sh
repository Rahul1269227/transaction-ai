#!/bin/bash

echo "=== Testing Transfer vs Transport Confusion ==="
echo ""

test_text() {
    local text="$1"
    local expected="$2"

    echo "Text: $text"
    echo "Expected: $expected"

    response=$(curl -s -X POST http://localhost:8000/categorize \
        -H "Content-Type: application/json" \
        -d "{\"text\": \"$text\"}")

    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Final: {data[\"category\"]}')
if 'ensemble_votes' in data:
    votes = data['ensemble_votes']
    if votes.get('ml'):
        print(f'ML:    {votes[\"ml\"][\"category\"]:25s} ({votes[\"ml\"][\"confidence\"]*100:.1f}%)')
    if votes.get('rule'):
        print(f'Rule:  {votes[\"rule\"][\"category\"]:25s} ({votes[\"rule\"][\"confidence\"]*100:.1f}%)')
"
    echo "---"
    echo ""
}

# Test Transfers
test_text "TRANSFER TO SAVINGS ACCOUNT" "Transfers/UPI"
test_text "FUND TRANSFER" "Transfers/UPI"
test_text "NEFT TRANSFER TO JOHN" "Transfers/UPI"

# Test Transport
test_text "UBER TRIP PAYMENT" "Transport"
test_text "METRO CARD RECHARGE" "Transport"
test_text "OLA CAB RIDE" "Transport"

echo "=== Done ==="
