#!/bin/bash
# Test script for all improvements

echo "=================================================="
echo "TESTING ALL IMPROVEMENTS"
echo "=================================================="
echo ""

# Test 1: Deterministic ATM rule
echo "Test 1: ATM deterministic rule (should be 95% confidence)"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"ATM CASH WDL ICICI BANK\"}" | python3 -m json.tool | grep -E "(category|confidence|method)"
echo ""

# Test 2: EMI rule
echo "Test 2: EMI deterministic rule (should be 95% confidence)"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"HOME LOAN EMI PAYMENT\"}" | python3 -m json.tool | grep -E "(category|confidence|method)"
echo ""

# Test 3: Fuel rule
echo "Test 3: Fuel deterministic rule (should be 95% confidence)"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"HPCL PETROL PUMP BANGALORE\"}" | python3 -m json.tool | grep -E "(category|confidence|method)"
echo ""

# Test 4: Merchant match (Starbucks)
echo "Test 4: Merchant priority (Starbucks, should be merchant_gazetteer)"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Starbucks coffee\"}" | python3 -m json.tool | grep -E "(category|confidence|method)"
echo ""

# Test 5: Normal transaction (should test LLM fallback)
echo "Test 5: Unknown merchant (should test ensemble)"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Random Store XYZ purchase\"}" | python3 -m json.tool | grep -E "(category|confidence|method)"
echo ""

echo "=================================================="
echo "TESTS COMPLETE"
echo "=================================================="
