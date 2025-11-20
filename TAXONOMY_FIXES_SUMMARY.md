# Taxonomy Fixes - Complete Summary

## Date: 2025-11-20

## Issues Found in Original Taxonomy

### 1. **Subscriptions vs Bills Confusion**
- **Problem**: Bills category had "Subscription" as subcategory and contained Netflix, Spotify, YouTube Premium, etc.
- **Impact**: All subscription services (Netflix, Spotify, YouTube Premium) were incorrectly classified as "bills" instead of "subscriptions_memberships"
- **Root Cause**: Overlapping keywords and patterns between Bills and Subscriptions & Memberships categories

### 2. **Amazon Keyword Collision**
- **Problem**: Shopping category had generic "amazon" keyword
- **Impact**: All Amazon transactions (Amazon Prime, Amazon Electronics) defaulted to "shopping"
- **Root Cause**: No disambiguation between Amazon shopping vs Amazon services

### 3. **Missing Merchants in Gazetteer**
- **Problem**: Common merchants (Tesla Supercharger, State Farm, Costco, Best Buy, etc.) not in gazetteer
- **Impact**: Random fallback classifications with low confidence
- **Root Cause**: Gazetteer only had ~280 merchants, missing many US-based merchants

### 4. **Electronics Not Distinguished from Shopping**
- **Problem**: No specific patterns to distinguish electronics purchases from general shopping
- **Impact**: Best Buy, Amazon electronics all classified as "shopping" not "electronics_technology"
- **Root Cause**: Shopping patterns too broad, electronics patterns too narrow

---

## Fixes Applied

### 1. Bills Category Cleanup
**File**: `data/taxonomy.yaml` (lines 567-606)

**Removed from Bills**:
- Subcategory: "Subscription" ❌
- Keywords: subscription, recurring, monthly billing, netflix, amazon prime, spotify, youtube premium, apple music, icloud storage, office 365, etc. ❌
- Patterns: `(?i).*(subscription|subscribe).*`, `(?i).*recurring.*`, `(?i).*monthly.*billing.*` ❌

**Kept in Bills**:
- Utility-specific: electricity bill, water bill, phone bill, internet bill ✅
- EMI/Loan-specific: loan, emi, credit card ✅  
- Payment-specific: due payment, outstanding, invoice ✅

### 2. Shopping Category Fix
**File**: `data/taxonomy.yaml` (line 275)

**Changed**:
```yaml
# OLD:
- "(?i)amazon(?!.*pantry).*"

# NEW:
- "(?i)amazon(?!.*(prime|pantry|music|video|kindle)).*"
```

**Impact**: Amazon Prime, Amazon Music, Amazon Video now excluded from shopping

### 3. Electronics & Technology Enhancement  
**File**: `data/taxonomy.yaml` (lines 939-947)

**Added Keywords**:
- best buy
- apple store
- amazon electronics

**Added Pattern**:
```yaml
- "(?i)amazon.*(?=.*(laptop|phone|electronics|computer|tablet|ipad|watch|kindle|echo|fire|alexa))"
```

**Impact**: "Amazon laptop purchase" now routes to electronics_technology

### 4. Gazetteer Additions
**File**: `data/gazetteer/merchant_aliases.csv`

**Added 12 New Merchants**:
| Merchant | Category | Subcategory |
|----------|----------|-------------|
| Netflix | subscriptions_memberships | Streaming Services |
| Spotify | subscriptions_memberships | Music Streaming |
| YouTube Premium | subscriptions_memberships | Streaming Services |
| Amazon Prime | subscriptions_memberships | Streaming Services |
| Best Buy | electronics_technology | Electronics |
| Tesla Supercharger | fuel | Electric Charging |
| State Farm | insurance | Auto Insurance |
| Costco Gas | fuel | Gas Station |
| Costco | groceries | Wholesale |
| Chipotle | food_dining | Fast Food |
| Whole Foods | groceries | Organic |
| PlayStation Plus | subscriptions_memberships | Gaming |

---

## Expected Impact

### Before Fixes:
- Netflix → **bills** ❌
- Spotify Premium → **bills** ❌
- Amazon Electronics → **shopping** ❌
- Best Buy Laptop → **shopping** ❌
- Tesla Supercharger → **fees_charges** (random) ❌

### After Fixes:
- Netflix → **subscriptions_memberships** ✅
- Spotify Premium → **subscriptions_memberships** ✅
- Amazon Electronics → **electronics_technology** ✅
- Best Buy Laptop → **electronics_technology** ✅
- Tesla Supercharger → **fuel** ✅

### Accuracy Prediction:
- **Before**: 66% (33/50 correct)
- **After**: ~85-90% (43-45/50 correct)

---

## Next Steps

1. ✅ Taxonomy fixed
2. ✅ Gazetteer updated
3. ⏳ **Retrain model** with clean taxonomy
4. ⏳ Re-test with 50-transaction test set
5. ⏳ Verify accuracy >= 90%

---

## Files Modified

1. `data/taxonomy.yaml` - Bills, Shopping, Electronics categories cleaned
2. `data/gazetteer/merchant_aliases.csv` - Added 12 merchants (now 305 total)

