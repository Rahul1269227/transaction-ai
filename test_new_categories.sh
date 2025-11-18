#!/bin/bash

echo "Testing New Categories..."
echo ""

# Test Insurance
echo "════════════════════════════════════════"
echo "1. Insurance - LIC Premium Payment"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "LIC Insurance Premium Payment"}' | python3 -m json.tool
echo ""

# Test Charity & Donations
echo "════════════════════════════════════════"
echo "2. Charity & Donations - Red Cross"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Donation to Red Cross India"}' | python3 -m json.tool
echo ""

# Test Personal Care
echo "════════════════════════════════════════"
echo "3. Personal Care - Urban Company"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Urban Company Salon Service"}' | python3 -m json.tool
echo ""

# Test Pets
echo "════════════════════════════════════════"
echo "4. Pets - Dog Food"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Pedigree Dog Food Purchase"}' | python3 -m json.tool
echo ""

# Test Home Improvement
echo "════════════════════════════════════════"
echo "5. Home Improvement - IKEA"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "IKEA Furniture Purchase"}' | python3 -m json.tool
echo ""

# Test Automotive
echo "════════════════════════════════════════"
echo "6. Automotive - Car Service"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Car Service - Maruti Suzuki"}' | python3 -m json.tool
echo ""

# Test Taxes & Government
echo "════════════════════════════════════════"
echo "7. Taxes & Government - Income Tax"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Income Tax Payment GST Portal"}' | python3 -m json.tool
echo ""

# Test Electronics & Technology
echo "════════════════════════════════════════"
echo "8. Electronics & Technology - iPhone"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "iPhone 15 Purchase Apple Store"}' | python3 -m json.tool
echo ""

# Test Professional Services
echo "════════════════════════════════════════"
echo "9. Professional Services - Legal"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Legal Consultation Fees Lawyer"}' | python3 -m json.tool
echo ""

# Test Kids & Family
echo "════════════════════════════════════════"
echo "10. Kids & Family - FirstCry"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "FirstCry Baby Products Purchase"}' | python3 -m json.tool
echo ""

# Test Subscriptions & Memberships
echo "════════════════════════════════════════"
echo "11. Subscriptions - Netflix"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Netflix Monthly Subscription"}' | python3 -m json.tool
echo ""

# Test Gifts & Special Occasions
echo "════════════════════════════════════════"
echo "12. Gifts & Occasions - Flowers"
echo "────────────────────────────────────────"
curl -s -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "Flowers from Ferns N Petals"}' | python3 -m json.tool
echo ""

echo "════════════════════════════════════════"
echo "Testing Complete!"
echo "════════════════════════════════════════"
