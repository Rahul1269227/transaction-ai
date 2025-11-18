#!/bin/bash
# Test complex and ambiguous transactions with the improved system

API_URL="http://localhost:8000/categorize"

echo "========================================================================"
echo "TESTING COMPLEX & AMBIGUOUS TRANSACTIONS"
echo "========================================================================"
echo ""

# Test 1: Apple Subscription (Fixed in improvements)
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 1: Apple Subscription (Should be Bills, not Utilities)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "INTL TRX APPLE.COM/BILL", "amount": 99.0, "date": "2025-11-15"}' \
  | python3 -m json.tool
echo ""

# Test 2: Netflix Subscription
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 2: Netflix Subscription (Should be Bills, not Entertainment)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Netflix monthly subscription", "amount": 499.0, "date": "2025-11-10"}' \
  | python3 -m json.tool
echo ""

# Test 3: Temporal Pattern - Salary on 1st of month
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 3: Salary Credit on 1st (Should boost with temporal pattern)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Salary credit from XYZ Corp", "amount": 85000.0, "date": "2025-11-01"}' \
  | python3 -m json.tool
echo ""

# Test 4: Temporal Pattern - Rent on month-end
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 4: Rent Payment on Month-End (Should boost with temporal pattern)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Payment to landlord for rent", "amount": 25000.0, "date": "2025-11-30"}' \
  | python3 -m json.tool
echo ""

# Test 5: Ambiguous - Unknown payment
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 5: Ambiguous Transaction (Should have high ambiguity score + alternatives)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "UNKNOWN MERCHANT PAYMENT", "amount": 1500.0}' \
  | python3 -m json.tool
echo ""

# Test 6: Complex - International transaction with MCC
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 6: International Transaction with MCC (Should detect fraud patterns)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "INTL TRX UNAUTHORIZED CHARGE", "amount": 2500.0, "mcc": "6011"}' \
  | python3 -m json.tool
echo ""

# Test 7: New merchant in gazetteer - Spotify
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 7: Spotify Premium (New merchant - should be Bills/Subscription)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Spotify Premium monthly", "amount": 119.0, "date": "2025-11-12"}' \
  | python3 -m json.tool
echo ""

# Test 8: Category-specific threshold - Critical category (Investments)
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 8: Investment Transaction (Critical category - high threshold)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Mutual fund SIP investment Zerodha", "amount": 10000.0, "date": "2025-11-05"}' \
  | python3 -m json.tool
echo ""

# Test 9: Category-specific threshold - Low-risk category (Food)
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 9: Starbucks Coffee (Low-risk - lower threshold)"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Starbucks coffee grande latte", "amount": 350.0}' \
  | python3 -m json.tool
echo ""

# Test 10: Complex - Multiple signals (MCC + keywords + temporal)
echo "═══════════════════════════════════════════════════════════════════════"
echo "TEST 10: Complex Multi-Signal Transaction"
echo "───────────────────────────────────────────────────────────────────────"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Electricity bill payment BESCOM", "amount": 1850.0, "date": "2025-11-18", "mcc": "4900"}' \
  | python3 -m json.tool
echo ""

echo "========================================================================"
echo "TEST SUITE COMPLETED"
echo "========================================================================"
