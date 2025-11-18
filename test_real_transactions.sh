#!/bin/bash

# Test real-world transactions
transactions=(
  "Starbucks Coffee Downtown"
  "Whole Foods Market groceries"
  "Netflix monthly subscription"
  "Uber ride to airport"
  "Amazon electronics purchase"
  "Shell gas station"
  "CVS Pharmacy medicines"
  "Chase Bank ATM withdrawal"
  "Electric bill payment PSEG"
  "Zelle transfer to John"
  "Apple Store iPhone purchase"
  "Delta Airlines ticket to NYC"
  "Airbnb rental San Francisco"
  "Gym membership 24 Hour Fitness"
  "Target shopping misc items"
  "Costco groceries"
  "Spotify Premium subscription"
  "Blue Apron meal kit"
  "PetSmart dog food"
  "Home Depot home improvement"
)

for txn in "${transactions[@]}"
do
  echo "════════════════════════════════════════════════════════"
  echo "Testing: $txn"
  echo "────────────────────────────────────────────────────────"
  curl -s -X POST http://localhost:8000/categorize \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"$txn\"}" | python3 -m json.tool
  echo ""
done
