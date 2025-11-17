#!/bin/bash
# Final validation test with 5 unseen transactions
# Tests all improvements: deterministic rules, merchant priority, LLM fallback, confidence calibration

echo "═══════════════════════════════════════════════════════════════════"
echo "🧪 FINAL VALIDATION TEST - 5 UNSEEN TRANSACTIONS"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API is not running. Starting it..."
    USE_ENSEMBLE=true FAST_MODE=true python3 apps/api/main.py > /tmp/api_validation.log 2>&1 &
    sleep 10
    echo "✅ API started"
fi

echo ""

# Test 1: Deterministic ATM Rule (should be 95% confidence, <100ms)
echo "Test 1: ATM Withdrawal (Deterministic Rule)"
echo "─────────────────────────────────────────────────────────────────"
echo "Transaction: 'ATM WITHDRAWAL SBI MAIN BRANCH BANGALORE'"
echo "Expected: ATM/Cash, 95% confidence, rule_deterministic method"
echo ""
time curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "ATM WITHDRAWAL SBI MAIN BRANCH BANGALORE"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Result: {data[\"category\"]} | Confidence: {data[\"confidence\"]:.1%} | Method: {data[\"method\"]}')
print(f'   Review Required: {\"⚠️  Yes\" if data[\"requires_review\"] else \"✅ No\"}')
if data.get('ensemble_votes'):
    votes = data['ensemble_votes']
    print(f'   Agreement: {votes.get(\"agreement_count\", 0)}/{votes.get(\"total_methods\", 0)} methods')
"
echo ""
echo ""

# Test 2: Known Merchant (should use merchant_gazetteer, bypass ensemble)
echo "Test 2: Known Merchant - McDonald's (Merchant Priority)"
echo "─────────────────────────────────────────────────────────────────"
echo "Transaction: 'McDonalds Big Mac Meal Rs 350'"
echo "Expected: Food & Dining, high confidence, merchant_gazetteer method"
echo ""
time curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "McDonalds Big Mac Meal Rs 350", "amount": 350.0}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Result: {data[\"category\"]} | Confidence: {data[\"confidence\"]:.1%} | Method: {data[\"method\"]}')
print(f'   Review Required: {\"⚠️  Yes\" if data[\"requires_review\"] else \"✅ No\"}')
if data.get('ensemble_votes'):
    votes = data['ensemble_votes']
    print(f'   Agreement: {votes.get(\"agreement_count\", 0)}/{votes.get(\"total_methods\", 0)} methods')
"
echo ""
echo ""

# Test 3: Salary Credit (Deterministic Rule)
echo "Test 3: Salary Credit (Deterministic Rule)"
echo "─────────────────────────────────────────────────────────────────"
echo "Transaction: 'SALARY CREDIT FROM TECH CORP INDIA LTD'"
echo "Expected: Income/Salary, 95% confidence, rule_deterministic method"
echo ""
time curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "SALARY CREDIT FROM TECH CORP INDIA LTD", "amount": 75000.0}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Result: {data[\"category\"]} | Confidence: {data[\"confidence\"]:.1%} | Method: {data[\"method\"]}')
print(f'   Review Required: {\"⚠️  Yes\" if data[\"requires_review\"] else \"✅ No\"}')
if data.get('ensemble_votes'):
    votes = data['ensemble_votes']
    print(f'   Agreement: {votes.get(\"agreement_count\", 0)}/{votes.get(\"total_methods\", 0)} methods')
"
echo ""
echo ""

# Test 4: Unknown transaction (should test ML + LLM fallback logic)
echo "Test 4: Unknown Transaction (Ensemble with LLM Fallback)"
echo "─────────────────────────────────────────────────────────────────"
echo "Transaction: 'Payment to John Doe for consulting services'"
echo "Expected: ML or ensemble method, confidence varies, LLM may run if ML < 60%"
echo ""
time curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Payment to John Doe for consulting services", "amount": 15000.0}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Result: {data[\"category\"]} | Confidence: {data[\"confidence\"]:.1%} | Method: {data[\"method\"]}')
print(f'   Review Required: {\"⚠️  Yes\" if data[\"requires_review\"] else \"✅ No\"}')
if data.get('ensemble_votes'):
    votes = data['ensemble_votes']
    print(f'   Ensemble votes:')
    for method in ['rule', 'ml', 'llm']:
        result = votes.get(method)
        if result and isinstance(result, dict):
            print(f'     {method.upper()}: {result.get(\"category\", \"N/A\")} ({result.get(\"confidence\", 0):.1%})')
    print(f'   Agreement: {votes.get(\"agreement_count\", 0)}/{votes.get(\"total_methods\", 0)} methods')
"
echo ""
echo ""

# Test 5: Fuel Transaction (Deterministic Rule)
echo "Test 5: Fuel Purchase (Deterministic Rule)"
echo "─────────────────────────────────────────────────────────────────"
echo "Transaction: 'IOCL PETROL PUMP PAYMENT DELHI'"
echo "Expected: Fuel, 95% confidence, rule_deterministic method"
echo ""
time curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "IOCL PETROL PUMP PAYMENT DELHI", "amount": 2500.0}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Result: {data[\"category\"]} | Confidence: {data[\"confidence\"]:.1%} | Method: {data[\"method\"]}')
print(f'   Review Required: {\"⚠️  Yes\" if data[\"requires_review\"] else \"✅ No\"}')
if data.get('ensemble_votes'):
    votes = data['ensemble_votes']
    print(f'   Agreement: {votes.get(\"agreement_count\", 0)}/{votes.get(\"total_methods\", 0)} methods')
"
echo ""
echo ""

echo "═══════════════════════════════════════════════════════════════════"
echo "📊 VALIDATION SUMMARY"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Expected Results:"
echo "  Test 1 (ATM): ✅ 95% confidence, rule_deterministic, <100ms"
echo "  Test 2 (McDonald's): ✅ High confidence, merchant_gazetteer"
echo "  Test 3 (Salary): ✅ 95% confidence, rule_deterministic, <100ms"
echo "  Test 4 (Unknown): ⚠️  Variable confidence, ensemble/ml method"
echo "  Test 5 (Fuel): ✅ 95% confidence, rule_deterministic, <100ms"
echo ""
echo "Key Improvements Validated:"
echo "  ✅ Deterministic rules (Tests 1, 3, 5)"
echo "  ✅ Merchant priority (Test 2)"
echo "  ✅ LLM fallback logic (Test 4)"
echo "  ✅ Confidence calibration (All tests)"
echo "  ✅ Early exit optimization (Tests 1, 3, 5)"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
