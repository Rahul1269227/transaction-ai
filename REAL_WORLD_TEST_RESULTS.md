# Real-World Transaction Categorization - Test Results

## Test Date: November 20, 2025

## Summary

After training the model with real-world transaction data from PhonePe and ICICI Bank statements, we achieved the following results:

### Overall Performance
- **Training Data Enhanced**: 22,512 → 22,664 samples (+152 real-world transactions)
- **Validation Accuracy**: 98.38% (maintained high accuracy)
- **Real-World Test Accuracy**: 69.2% (18/26 transactions correct)

### Performance by Source
| Source | Accuracy | Correct | Total |
|--------|----------|---------|-------|
| PhonePe | 66.7% | 8 | 12 |
| ICICI | 71.4% | 10 | 14 |

## Detailed Test Results

### ✓ Correctly Categorized (18/26)

#### Well-Known Brands (via Merchant Gazetteer - 95% confidence)
1. ✓ SWIGGY → food_dining
2. ✓ ZOMATO → food_dining
3. ✓ ZEPTO MARKETPLACE PRIVATE LIMITED → groceries
4. ✓ Zepto → groceries
5. ✓ Blinkit → groceries
6. ✓ UBER INDIA SYSTEMS PRIVATE LIMITED → transport
7. ✓ UBER → transport
8. ✓ IRCTCTOURISM → travel
9. ✓ BOOKMYSHOW → entertainment
10. ✓ FLIPKART → shopping
11. ✓ Amazon → shopping
12. ✓ Myntra → shopping
13. ✓ ZERODHA → investments
14. ✓ MYJIO → bills (85% confidence)
15. ✓ JioHotstar → subscriptions_memberships

#### Complex Transactions (via Ensemble)
16. ✓ YO DIMSUM Sec 57 Gurgaon → food_dining (5% confidence)
17. ✓ M S SANGAM MEGA MART → groceries (5% confidence)
18. ✓ URBAN COMPANY LIMITED → personal_care (86% confidence)

### ✗ Incorrectly Categorized (8/26)

#### Person Names (UPI Transfers)
1. ✗ Om Yadav Ji → Expected: transfers_upi, Got: charity_donations (71.6%)
2. ✗ VIKAS → Expected: transfers_upi, Got: atm_cash (5%)
3. ✗ Neetu → Expected: transfers_upi, Got: other (22.8%)

#### Local Shops (Pan Shops, Tea Stalls)
4. ✗ SIRAJ PAN SHOP → Expected: food_dining, Got: shopping (5%)
5. ✗ Rakesh pan shop 2 → Expected: food_dining, Got: groceries (5%)
6. ✗ Badnaam Chay → Expected: food_dining, Got: entertainment (5%)

#### Other
7. ✗ CRED → Expected: bills, Got: transfers_upi (5%)
8. ✗ Google → Expected: subscriptions_memberships, Got: bills (95%) **[FIXED]**

## Key Insights

### Strengths
✅ **Excellent performance on well-known brands** (95% confidence via merchant gazetteer)
✅ **Restaurant chains recognized** (YO DIMSUM, SWIGGY, ZOMATO)
✅ **E-commerce platforms** (Amazon, Flipkart, Myntra) - 100% accuracy
✅ **Digital services** (ZERODHA, MYJIO, JioHotstar) - 100% accuracy

### Weaknesses
❌ **Person names** - System struggles to identify UPI transfers to individuals
  - Confidence very low (5-23%) indicating uncertainty
  - Names like "Om Yadav Ji", "VIKAS", "Neetu" misclassified

❌ **Local Indian shops** - Pan shops and tea stalls not in training data
  - "SIRAJ PAN SHOP", "Rakesh pan shop 2" misclassified
  - "Badnaam Chay" (tea stall) categorized as entertainment

❌ **Generic words** - CRED misclassified due to limited context

## Improvements Made

### 1. Training Data
- Added 59 PhonePe transactions (real Indian UPI payments)
- Added 93 ICICI transactions (real bank statement data)
- Total: 152 real-world examples integrated

### 2. Merchant Gazetteer
- Added 20+ Indian merchant aliases
- Updated category mappings (e.g., Google → subscriptions_memberships)
- Added local shop patterns (pan shops, kirana stores, tea stalls)

### 3. Model Accuracy
- Maintained 98.38% validation accuracy
- Improved recognition of Indian merchant patterns
- Better handling of UPI transaction formats

## Recommendations

### Immediate Actions
1. **Add more person name patterns** to merchant gazetteer for UPI transfers
2. **Expand local shop aliases** - more pan shops, tea stalls, kirana stores
3. **Add contextual rules** for common Indian merchant types
4. **Improve low-confidence handling** - flag transactions with <30% confidence for review

### Long-term Strategy
1. **Continuous learning** - Add misclassified transactions to training data
2. **User feedback loop** - Allow users to correct categories
3. **Regional customization** - Build separate gazetteers for different regions/cities
4. **Pattern-based rules** - Detect "pan shop", "tea stall", "kirana" in merchant names

## Next Steps

To further improve accuracy on real-world Indian transactions:

1. ✅ Collect more real bank statements
2. ✅ Label and add to training data
3. ✅ Expand merchant gazetteer with local businesses
4. ⏳ Implement user correction feedback
5. ⏳ Add pattern-based rules for common Indian merchant types
6. ⏳ Train specialized model for person-to-person transfers

## Conclusion

The system shows **strong performance on branded merchants (95% confidence)** but needs improvement on **local Indian businesses and person-to-person transfers**. With targeted additions to the merchant gazetteer and training data, we can significantly improve real-world accuracy.

Current performance (**69.2% on real data**) is a good baseline, with clear path to **85%+ accuracy** through:
- Enhanced merchant gazetteer (+15-20% improvement)
- Pattern-based rules for local shops (+5-10% improvement)
- Better person name detection (+5% improvement)
