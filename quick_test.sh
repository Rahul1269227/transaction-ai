#!/bin/bash
echo "=== Quick Test After Cache Clear ==="
for txn in "WALMART SUPERCENTER" "TARGET STORE" "BEST BUY ELECTRONICS" "SHELL OIL STATION" "DOORDASH CHIPOTLE"
do
  echo ""
  echo "Testing: $txn"
  curl -s http://localhost:8000/categorize -H "Content-Type: application/json" -d "{\"text\": \"$txn\"}" | jq '{category, confidence}'
done
