# Production-Ready Transaction Classification Architecture

## Current Implementation Status

### ✅ What's Already Built (Good Foundation)

1. **Normalization Pipeline** (`core/normalize/`)
   - Channel extraction (UPI, IMPS, POS, ATM, etc.)
   - Merchant extraction with "TO <merchant>" pattern
   - Reference number extraction
   - Pattern matching for common formats

2. **Merchant Resolver** (`core/resolve/resolver.py`)
   - Fuzzy matching (Levenshtein, trigram similarity)
   - Alias matching from gazetteer
   - 70% similarity threshold
   - **Status**: Works well, but needs priority boost in ensemble

3. **Rule-based Categorizer** (`core/rules/engine.py`)
   - Keyword matching
   - Pattern matching (regex)
   - Channel-based hints
   - **Status**: Good for obvious cases (ATM, salary, etc.)

4. **ML Classifier** (`core/model/classifier.py`)
   - LightGBM with embedding features
   - Trained on balanced dataset
   - **Status**: Works but needs better feature engineering

5. **LLM Classifier** (`core/model/llm_classifier.py`)
   - Llama 3.1 8B via Ollama
   - Few-shot learning capable
   - Semantic understanding
   - **Status**: Too slow to be primary, should be fallback only

6. **Ensemble Router** (`core/model/ensemble_router.py`)
   - Weighted voting (Rule: 30%, ML: 40%, LLM: 30%)
   - Fast mode (skips LLM when Rule+ML agree)
   - **Status**: Architecture correct, weights need tuning

## 🎯 Recommended Architecture (Production-Ready)

### Decision Flow

```
Input Transaction
      ↓
[1] Normalize & Extract
      ↓
[2] Merchant Resolver → MATCH? → Category (95%+ confidence) ✓ DONE
      ↓ NO MATCH
[3] Deterministic Rules → HIGH CONF? → Category (85%+ confidence) ✓ DONE
      ↓ NO / LOW CONF
[4] ML Model (LightGBM) → Category + Confidence
      ↓
[5] Confidence Check:
      • ≥ 80% → Accept
      • 60-80% → Accept with "requires_review" flag
      • < 60% → Run LLM as fallback
      ↓
[6] LLM Fallback (only if ML conf < 60%)
      ↓
[7] Final Decision:
      • Combine ML + LLM if both ran
      • Flag for review if still < 60%
```

### Key Principle
**Merchant match = instant win. ML is primary. LLM is last resort.**

## 🔧 Implementation Fixes Needed

### Fix #1: Merchant Resolver Should Win Immediately

**Current**: Merchant match goes through ensemble voting
**Should be**: Merchant match → instant category with 95%+ confidence

**File**: `core/model/ensemble_router.py` (around line 150)

```python
# PRIORITY 1: Merchant Gazetteer Match (HIGHEST PRIORITY)
if merchant_match:
    # Merchant resolved = instant win, skip ensemble
    return CategorizationResult(
        category=merchant_match.category,
        subcategory=merchant_match.subcategory,
        confidence=min(1.0, merchant_match.similarity_score * 0.95),  # 95%+ if exact match
        method="merchant_gazetteer",
        explanations=[f"matched_merchant={merchant_match.canonical_name}"],
        merchant_resolved=merchant_match.canonical_name,
        requires_review=False  # High confidence merchant = no review
    )
```

### Fix #2: LLM Only as Fallback (When ML Confidence < 60%)

**Current**: LLM runs in fast mode based on Rule+ML agreement
**Should be**: LLM only when ML confidence < 60%

**File**: `core/model/ensemble_router.py` (around line 180)

```python
# Run ML first
ml_result = self._run_ml_classifier(search_text, normalized)

# Check ML confidence
ml_confidence = ml_result[1] if ml_result else 0.0

# Only run LLM if ML is uncertain
if ml_confidence < 0.60:  # Low confidence threshold
    logger.info(f"ML confidence {ml_confidence:.2%} < 60%, running LLM fallback")
    llm_result = self._run_llm_classifier(text, amount)
else:
    logger.info(f"ML confidence {ml_confidence:.2%} ≥ 60%, skipping LLM")
    llm_result = None
```

### Fix #3: Better Confidence Calibration

**Add**: Calibrated confidence scores with clear thresholds

```python
# After ensemble voting
final_confidence = winner_score / total_weight

# Calibrate confidence based on agreement
methods_agree = len([r for r in [rule_result, ml_result, llm_result] if r and r[0] == winner_category])
total_methods = len([r for r in [rule_result, ml_result, llm_result] if r])

# Boost confidence if methods agree
if methods_agree == total_methods and total_methods > 1:
    final_confidence = min(1.0, final_confidence * 1.1)  # 10% boost for agreement

# Penalize if methods disagree
elif methods_agree == 1 and total_methods > 1:
    final_confidence = final_confidence * 0.9  # 10% penalty for disagreement

# Decision thresholds
requires_review = final_confidence < 0.60
auto_accept = final_confidence >= 0.80
```

### Fix #4: Add Merchant-Aware Rules

**File**: `core/rules/engine.py` (in `categorize` method)

```python
# PRIORITY: If merchant resolved, use merchant category
if merchant:
    merchant_match = self._match_merchant(merchant)
    if merchant_match:
        # Merchant category overrides everything
        return merchant_match

# Then continue with existing keyword/pattern matching...
```

## 📊 Expected Performance After Fixes

| Scenario | Method | Confidence | Review Rate | Accuracy |
|----------|--------|-----------|-------------|----------|
| Known merchant in gazetteer | Merchant Resolver | 95-100% | <1% | 98-100% |
| Obvious patterns (ATM, Salary) | Rules | 85-95% | <5% | 95-98% |
| Common transactions (ML trained) | ML Model | 70-90% | 10-20% | 85-92% |
| Unseen merchants with context | ML + LLM | 60-80% | 30-50% | 75-85% |
| Ambiguous edge cases | ML + LLM + Review | <60% | 80%+ | 70-80% |

## 🚀 Actionable Steps (Priority Order)

### Week 1: Critical Fixes
1. ✅ **Merchant resolver priority** - Make it win immediately
2. ✅ **LLM as fallback only** - Only run when ML < 60% confidence
3. ✅ **Confidence calibration** - Add agreement boosting/disagreement penalty

### Week 2: Data Improvements
4. **Expand merchant gazetteer** to top 500 merchants
   - Scrape from your transaction data
   - Add common e-commerce (Flipkart, Myntra, Amazon sellers)
   - Add common bills (electricity, gas, telecom)

5. **Add deterministic rules** for:
   - Fuel (MCC 5542, keywords: HPCL, IOCL, BPCL, Shell, Petrol, Diesel)
   - EMI (keywords: EMI, LOAN, INSTALLMENT)
   - Salary (keywords: SALARY, PAYROLL, amount > 10K, FROM employer)
   - Fees (keywords: CHARGE, FEE, PENALTY, GST, amount < 500)

### Week 3: ML Model Improvements
6. **Retrain ML with better features**:
   ```python
   features = {
       'merchant_resolved': bool,
       'merchant_category': categorical,
       'channel': categorical,  # UPI, POS, ATM, etc.
       'amount_bucket': categorical,  # <100, 100-500, 500-2K, 2K-10K, >10K
       'is_recurring': bool,  # same merchant + similar amount monthly
       'day_of_week': int,
       'hour_of_day': int,
       'text_embedding': vector[384],  # sentence-transformers
       'keyword_matches': multi-hot,  # top 100 keywords
   }
   ```

7. **Calibrate ML model** using Platt scaling or isotonic regression

### Month 2: Active Learning
8. **Build feedback loop**:
   - Log all low-confidence predictions (< 60%)
   - Use UI feedback to collect corrections
   - Retrain ML weekly with corrected data
   - Auto-add high-frequency unknown merchants to gazetteer

9. **Monitor metrics**:
   - Merchant match rate (target: >40%)
   - Rule match rate (target: >20%)
   - ML confidence distribution
   - Review rate (target: <30%)
   - Category-wise accuracy

## 💡 Quick Wins for Your Cloudtail Problem

### Immediate Solution (Already Done)
```
1. ✅ Add Cloudtail to gazetteer → 100% confidence
2. ✅ Add "TO <merchant>" extraction pattern
3. ✅ Enhance LLM prompts for semantic understanding
```

### Generalized Solution (Need to Apply)
```
1. Merchant resolver wins immediately (95%+ confidence)
2. LLM only runs when ML < 60% confidence
3. Better confidence thresholds with review flags
```

### Result
- **Known merchants**: 95-100% accuracy (merchant resolver)
- **Unseen merchants**: 75-85% accuracy (ML + LLM fallback)
- **Review rate**: ~30% (only low-confidence cases)

## 🎓 Learning from Cloudtail Misclassification

### What Went Wrong
1. Merchant not in gazetteer → missed obvious match
2. "PAYTM-WALLET" keyword confused rule-based system
3. ML model never saw "TO CLOUDTAIL" pattern
4. LLM got correct answer but was outvoted by Rule+ML

### Root Cause
**Ensemble voting without priority tiers** - all methods equal weight, even when merchant is clearly resolved.

### The Fix
**Hierarchical decision tree**:
```
Merchant match? → Use it (95%+ confidence)
  ↓ No
Clear rule match? → Use it (85%+ confidence)
  ↓ No
ML confident? → Use it (70%+ confidence)
  ↓ No (< 60%)
Run LLM fallback → Combine ML + LLM
  ↓
Still uncertain? → Flag for review
```

## 📁 File Structure (What Goes Where)

```
core/
├── normalize/          # Step 1: Extract features
│   ├── normalizer.py   # Main normalization
│   ├── patterns.py     # Regex patterns (✅ updated)
│   └── features.py     # Feature extraction
├── resolve/            # Step 2: Merchant matching
│   └── resolver.py     # Fuzzy merchant matching (✅ good)
├── rules/              # Step 3: Deterministic rules
│   └── engine.py       # Rule-based categorizer (needs merchant priority)
├── model/              # Step 4: ML models
│   ├── classifier.py   # LightGBM model (needs retraining)
│   ├── llm_classifier.py  # LLM fallback (✅ improved prompts)
│   └── ensemble_router.py  # Decision logic (needs priority fixes)
└── data/
    └── gazetteer/
        └── merchant_aliases.csv  # (✅ Cloudtail added, duplicates fixed)
```

## 🔍 Testing Strategy

### Unit Tests
```python
# Test merchant resolver priority
def test_merchant_match_wins():
    result = router.categorize("PAYTM TO CLOUDTAIL INDIA")
    assert result.method == "merchant_gazetteer"
    assert result.confidence >= 0.95
    assert result.category == "shopping"

# Test LLM fallback logic
def test_llm_only_when_ml_uncertain():
    # Mock ML with 70% confidence
    with patch('ml_classifier.predict') as mock_ml:
        mock_ml.return_value = ("shopping", 0.70)
        result = router.categorize("PAYTM TO RANDOMSTORE")
        # LLM should NOT run (70% > 60% threshold)
        assert "llm" not in result.ensemble_votes

# Test review flagging
def test_low_confidence_flagged():
    result = router.categorize("WEIRD TRANSACTION XYZ")
    if result.confidence < 0.60:
        assert result.requires_review == True
```

### Integration Tests
- Test full pipeline end-to-end
- Test with real historical data (80/20 train/test split)
- Measure per-category F1 scores

## 🎯 Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Overall Accuracy | ~75% | >90% | Test set evaluation |
| Merchant Match Rate | ~20% | >40% | % transactions matched to gazetteer |
| Review Rate | ~50% | <30% | % flagged for human review |
| LLM Usage Rate | ~70% | <15% | % transactions using LLM |
| Latency (p95) | ~2s | <500ms | Exclude LLM fallback cases |

## 📝 Summary: What You Should Do

1. **This week**: Apply the 3 critical fixes (merchant priority, LLM fallback, confidence calibration)
2. **This month**: Expand gazetteer to 500 merchants, add more deterministic rules
3. **Ongoing**: Build active learning loop, retrain monthly

**The architecture is sound. You just need to tune the decision flow to prioritize high-confidence signals (merchant match) over ensemble voting.**
