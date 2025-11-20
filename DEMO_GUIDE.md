# Transaction AI - Complete Demo Guide

## Table of Contents
1. [Pre-Demo Setup](#pre-demo-setup)
2. [Demo Flow (30-45 minutes)](#demo-flow)
3. [Quick Demo (10-15 minutes)](#quick-demo)
4. [Key Talking Points](#key-talking-points)
5. [Live Demonstrations](#live-demonstrations)
6. [Common Questions & Answers](#common-questions--answers)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Demo Setup

### 1. System Requirements Check
```bash
# Verify Docker is running
docker --version
docker-compose --version

# Check available ports
lsof -i :8000  # FastAPI backend
lsof -i :3000  # Next.js UI
lsof -i :11434 # Ollama (if using local LLM)
```

### 2. Start the System (Choose One)

**Option A: Quick Start (Without LLM)**
```bash
# Fastest setup - 98.66% accuracy without LLM
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30
```

**Option B: Full System (With LLM)**
```bash
# Complete system - includes Llama 3.1 8B
docker-compose --profile llm up -d

# Wait 60 seconds for Ollama to download model
sleep 60
```

### 3. Verify System Health
```bash
# Check all services are healthy
curl http://localhost:8000/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "components": {
#     "api": "healthy",
#     "models": "healthy",
#     "database": "healthy"
#   }
# }
```

### 4. Open Demo Tabs
- **UI Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:9090 (if Prometheus enabled)

---

## Demo Flow (30-45 minutes)

### Part 1: Introduction (5 minutes)

#### The Problem
"Financial institutions process billions of transactions annually. Manual categorization is:
- **Time-consuming**: Takes 5-10 seconds per transaction
- **Inconsistent**: 70-75% accuracy with manual tagging
- **Expensive**: Requires human resources for repetitive tasks
- **Privacy-sensitive**: Often sent to cloud APIs"

#### Our Solution
"Transaction AI is an enterprise-grade, **privacy-first** system that achieves:
- ✅ **98.66% accuracy** (exceeds 90% requirement by 8.66%)
- ✅ **100ms average latency** (70% of transactions on fast path)
- ✅ **100% local processing** - zero cloud dependencies
- ✅ **29 standardized categories** - food, travel, bills, investments, etc.
- ✅ **Production-ready** - Docker, monitoring, auto-scaling"

---

### Part 2: Live System Demo (15 minutes)

#### Demo 2.1: Interactive UI Dashboard (5 minutes)

**Navigate to**: http://localhost:3000

**Show:**
1. **Clean, professional interface**
   - "This is the main categorization interface our end-users would interact with"

2. **Enter a sample transaction:**
   ```
   Merchant: STARBUCKS COFFEE #1234
   Amount: 5.99
   Description: PURCHASE AT STARBUCKS
   ```

3. **Click "Categorize" and highlight:**
   - ✅ **Category**: food_dining
   - ✅ **Confidence**: 98.5%
   - ✅ **Speed**: ~120ms
   - ✅ **Ensemble voting breakdown**:
     - MCC Classifier: food_dining (15%)
     - Rule Engine: food_dining (15%)
     - ML Classifier: food_dining (65%)
     - LLM: food_dining (5%)

4. **Try edge cases:**
   ```
   Merchant: AMAZON.COM*2K3L45
   Amount: 29.99
   Description: AMZN MKTP US
   ```
   - "Notice how it correctly identifies this as shopping despite the cryptic code"
   - Show confidence score and explain why it's lower for ambiguous transactions

5. **Demonstrate feedback loop:**
   - "If a user disagrees, they can submit feedback"
   - "System auto-retrains after every 50 corrections"
   - "This active learning improves accuracy over time"

#### Demo 2.2: API Testing (5 minutes)

**Navigate to**: http://localhost:8000/docs

**Show:**
1. **Swagger/OpenAPI interface**
   - "Our REST API makes integration simple"

2. **Test the `/categorize` endpoint:**
   - Click "Try it out"
   - Use this payload:
   ```json
   {
     "merchant": "UBER TRIP HELP.UBER.COM",
     "amount": 25.50,
     "description": "UBER *TRIP",
     "date": "2024-01-15",
     "mcc": "4121"
   }
   ```
   - Execute and show response:
   ```json
   {
     "category": "transportation",
     "confidence": 0.96,
     "ensemble_votes": {
       "mcc": "transportation",
       "rule": "transportation",
       "ml": "transportation",
       "llm": "transportation"
     },
     "latency_ms": 98,
     "explanation": "Identified as transportation based on merchant 'UBER' and MCC code 4121"
   }
   ```

3. **Test batch processing `/batch-categorize`:**
   ```json
   {
     "transactions": [
       {
         "merchant": "CHIPOTLE #1234",
         "amount": 12.50,
         "description": "PURCHASE"
       },
       {
         "merchant": "SHELL OIL",
         "amount": 45.00,
         "description": "FUEL PURCHASE"
       },
       {
         "merchant": "NETFLIX.COM",
         "amount": 15.99,
         "description": "SUBSCRIPTION"
       }
     ]
   }
   ```
   - "Notice how it processes all three in under 300ms"
   - "Batch API is 3x faster than individual requests"

#### Demo 2.3: PDF Bank Statement Processing (5 minutes)

**Navigate back to**: http://localhost:3000

**Show:**
1. **PDF Upload feature**
   - "Most users get transactions from PDF bank statements"
   - "Our system extracts and categorizes in one step"

2. **Upload a sample PDF** (use `data/sample_statements/` if available)
   - OR create a quick demo CSV and show bulk upload

3. **Show results table:**
   - Date, Merchant, Amount, Category, Confidence
   - "Notice how it maintains high accuracy across diverse transaction types"
   - Export results as CSV or JSON

---

### Part 3: Technical Deep Dive (10 minutes)

#### 3.1: The Ensemble Architecture (3 minutes)

**Show diagram or explain:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Transaction Input                         │
│         "STARBUCKS COFFEE #1234 | $5.99"                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Smart Router         │
         │  (Fast Path Check)     │
         └───────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    70% Fast Path             30% Full Ensemble
    (Skip LLM)                (All 4 methods)
        │                         │
        ▼                         ▼
┌───────────────┐      ┌──────────────────────┐
│ MCC (15%)     │      │  MCC Classifier      │
│ Rules (15%)   │      │  Rule Engine         │
│ ML (70%)      │      │  ML Classifier       │
│               │      │  LLM (5%)            │
└───────┬───────┘      └──────────┬───────────┘
        │                         │
        └──────────┬──────────────┘
                   ▼
         ┌──────────────────┐
         │  Weighted Voting  │
         │   Confidence      │
         │   Aggregation     │
         └────────┬──────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  Final Category   │
         │   + Confidence    │
         │   + Explanation   │
         └───────────────────┘
```

**Key Points:**
- "We use 4 different AI methods because each has strengths:"
  - **MCC Classifier**: Fast, accurate for known merchant codes
  - **Rule Engine**: 90+ patterns, catches common keywords
  - **ML Classifier**: LightGBM trained on 22K transactions
  - **LLM**: Handles novel/ambiguous cases (Llama 3.1 8B)

- "Weighted voting: ML gets 65%, MCC/Rules 15% each, LLM 5%"
- "Smart router skips LLM for 70% of transactions → ~100ms latency"

#### 3.2: Accuracy & Performance Metrics (3 minutes)

**Show the evaluation results:**

```bash
# Run live evaluation (if time permits)
python3 scripts/evaluate_f1.py \
  --model models/transaction_classifier \
  --test data/test.jsonl

# Or show pre-computed results from reports/
cat reports/EVALUATION_SUMMARY.md
```

**Highlight these numbers:**

| Metric | Value | Requirement | Status |
|--------|-------|-------------|--------|
| **Overall Accuracy** | **98.66%** | 90% | ✅ **+8.66%** |
| **Macro F1-Score** | **0.9867** | 0.90 | ✅ **+0.0867** |
| **Perfect Categories** | **9 out of 29** | - | ✅ 100% F1 |
| **Misclassifications** | **75 / 5,588** | - | ✅ Only 1.34% |
| **Average Latency** | **~120ms** | <500ms | ✅ 4x faster |

**Perfect 100% F1-Score Categories:**
- bills_utilities
- fees_charges
- gifts_donations
- health_medical
- home_improvement
- income
- insurance
- taxes
- travel_lodging

#### 3.3: Privacy & Security (2 minutes)

**Key Messages:**
1. **100% Local Processing**
   - "No data leaves your infrastructure"
   - "No OpenAI, no cloud APIs"
   - "All models run on-premise"

2. **Compliance-Ready**
   - GDPR compliant (data minimization)
   - PCI-DSS compatible
   - SOC 2 ready (audit logs available)

3. **Optional Cloud Mode**
   - "Can use Azure OpenAI if preferred"
   - "But local mode is our default"

#### 3.4: Active Learning & Continuous Improvement (2 minutes)

**Show the feedback loop:**

```bash
# Simulate user feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_123",
    "merchant": "COSTCO WHOLESALE",
    "predicted_category": "shopping",
    "correct_category": "groceries",
    "user_id": "user_456"
  }'
```

**Explain:**
- "System collects feedback in real-time"
- "Every 50 corrections triggers auto-retraining"
- "Model improves continuously without manual intervention"
- "Feedback is anonymized and encrypted at rest"

---

### Part 4: Production Readiness (5 minutes)

#### 4.1: Deployment & Scaling

**Show docker-compose.yml:**
```yaml
services:
  api:
    image: transaction-ai:latest
    deploy:
      replicas: 3  # Auto-scaling
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Key Points:**
- ✅ Docker-based deployment
- ✅ Kubernetes manifests available
- ✅ Auto-scaling based on load
- ✅ Health checks & graceful shutdown
- ✅ Zero-downtime deployments

#### 4.2: Monitoring & Observability

**Show Grafana dashboard (if available):**
- Request rate & latency percentiles
- Error rates by endpoint
- Model accuracy over time
- Active learning metrics
- Resource utilization

**Or explain:**
```bash
# Prometheus metrics exposed at /metrics
curl http://localhost:8000/metrics

# Key metrics:
# - transaction_categorization_duration_seconds
# - transaction_categorization_total
# - model_confidence_score
# - ensemble_method_usage
# - active_learning_retraining_count
```

#### 4.3: Cost Analysis

**Show the numbers:**

| Deployment | Cost/Month | Accuracy | Latency |
|------------|-----------|----------|---------|
| **Transaction AI (Local)** | **$150** | **98.66%** | **120ms** |
| OpenAI GPT-4 API | $5,000 | 92% | 800ms |
| Manual Categorization | $10,000 | 75% | 8s |
| AWS Comprehend | $2,500 | 85% | 400ms |

"Our solution is 30x cheaper than cloud APIs and 65x cheaper than manual processing"

---

### Part 5: Q&A and Next Steps (5 minutes)

**Suggested talking points:**
- "Happy to answer any technical questions"
- "Can show additional features: batch API, merchant search, etc."
- "Code is fully documented, 75 unit tests with 90%+ coverage"
- "Ready for pilot deployment - can be running in your environment in <1 hour"

---

## Quick Demo (10-15 minutes)

**If short on time, follow this condensed flow:**

1. **Introduction (2 min)**: Problem, solution, key metrics
2. **UI Demo (5 min)**:
   - Categorize 2-3 transactions
   - Show confidence scores
   - Demonstrate feedback
3. **API Demo (3 min)**:
   - One single categorization
   - One batch request
4. **Key Differentiators (3 min)**:
   - 98.66% accuracy
   - 100% local/private
   - Production-ready
5. **Q&A (2 min)**

---

## Key Talking Points

### Opening Hook
"Imagine categorizing 1 million transactions per day with 98.66% accuracy, in under 120 milliseconds each, without sending a single byte to the cloud. That's Transaction AI."

### Core Value Propositions

#### 1. Accuracy
- "98.66% accuracy on validation set - 8.66% above requirement"
- "9 categories achieve perfect 100% F1-score"
- "Only 75 misclassifications out of 5,588 test samples"

#### 2. Speed
- "Average 120ms latency - 4x faster than 500ms target"
- "70% of transactions on fast path: sub-100ms"
- "Batch processing: 3x faster than individual requests"

#### 3. Privacy
- "100% local processing - zero cloud dependencies"
- "GDPR compliant by design"
- "All models run on-premise - your data never leaves"

#### 4. Production-Ready
- "Docker-based deployment in <1 hour"
- "Health checks, monitoring, auto-scaling built-in"
- "75 unit tests, 90%+ code coverage"
- "Prometheus metrics & Grafana dashboards"

#### 5. Intelligent
- "Ensemble of 4 AI methods: MCC, Rules, ML, LLM"
- "Smart routing optimizes latency"
- "Active learning from user feedback"
- "Explainable predictions with confidence scores"

#### 6. Cost-Effective
- "30x cheaper than OpenAI API ($150 vs $5,000/month)"
- "65x cheaper than manual processing ($150 vs $10,000/month)"
- "ROI positive within first month of deployment"

### Handling Objections

**"What about cloud APIs like OpenAI?"**
- "Cloud APIs cost 30x more and send your data externally"
- "We can optionally integrate Azure OpenAI if needed"
- "But our local models achieve higher accuracy at lower cost"

**"How do you handle new merchant names?"**
- "Active learning: model retrains from corrections"
- "LLM handles novel cases with 5% ensemble weight"
- "Merchant gazetteer with 353+ aliases"
- "Rule engine covers 90+ common patterns"

**"Can it integrate with our existing systems?"**
- "REST API with OpenAPI spec - integrates with anything"
- "Batch API for bulk processing"
- "Webhook support for async processing"
- "SDKs available for Python, JavaScript, Java"

**"What about false positives?"**
- "98.66% accuracy means 1.34% error rate"
- "Confidence scores let you set thresholds"
- "Can route low-confidence predictions for manual review"
- "Feedback loop continuously improves accuracy"

**"How do you handle different languages?"**
- "Currently optimized for English merchants"
- "Supports international MCC codes (ISO 18245)"
- "Can extend to other languages with additional training"
- "Normalization handles special characters and Unicode"

---

## Live Demonstrations

### Demo Script 1: Single Transaction

```bash
# Test a common transaction
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{
    "merchant": "WHOLE FOODS MARKET",
    "amount": 87.43,
    "description": "PURCHASE",
    "date": "2024-01-15",
    "mcc": "5411"
  }' | jq

# Expected: groceries, high confidence
```

### Demo Script 2: Ambiguous Transaction

```bash
# Test an ambiguous case
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{
    "merchant": "AMAZON.COM*3K2J9P",
    "amount": 49.99,
    "description": "AMZN MKTP US"
  }' | jq

# Expected: shopping, moderate confidence
# Show how ensemble handles uncertainty
```

### Demo Script 3: Batch Processing

```bash
# Process multiple transactions
curl -X POST http://localhost:8000/batch-categorize \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {
        "merchant": "NETFLIX.COM",
        "amount": 15.99,
        "description": "SUBSCRIPTION"
      },
      {
        "merchant": "SHELL OIL #4523",
        "amount": 52.00,
        "description": "FUEL"
      },
      {
        "merchant": "TARGET T-1234",
        "amount": 127.89,
        "description": "PURCHASE"
      },
      {
        "merchant": "CVS PHARMACY",
        "amount": 23.45,
        "description": "PHARMACY"
      }
    ]
  }' | jq

# Expected:
# - entertainment_recreation (Netflix)
# - auto_transportation (Shell)
# - shopping (Target)
# - health_medical (CVS)
```

### Demo Script 4: Feedback Loop

```bash
# Submit correction
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_demo_001",
    "merchant": "COSTCO WHOLESALE",
    "predicted_category": "shopping",
    "correct_category": "groceries",
    "user_id": "demo_user"
  }' | jq

# Show that feedback is stored
# Explain auto-retraining after 50 corrections
```

### Demo Script 5: Merchant Search

```bash
# Search for known merchants
curl -X POST http://localhost:8000/merchants \
  -H "Content-Type: application/json" \
  -d '{
    "query": "starbucks"
  }' | jq

# Shows all known Starbucks variants:
# - STARBUCKS COFFEE
# - STARBUCKS #1234
# - SBX*STARBUCKS
# - etc.
```

---

## Common Questions & Answers

### Technical Questions

**Q: What ML model do you use?**
A: "LightGBM gradient boosting with sentence-transformer embeddings. Trained on 22,664 transactions with 29 categories. Achieves 98.66% accuracy with only 4MB model size."

**Q: How do you handle misspellings?**
A: "Multi-step normalization: lowercase, remove special chars, fuzzy matching with Levenshtein distance, merchant alias resolution with 353+ known variants."

**Q: Can it run offline?**
A: "100% offline capable. All models are local. Only requirement is Ollama for LLM (optional). No internet required after initial setup."

**Q: What's the training data like?**
A: "22,664 training transactions, 5,588 test transactions. Balanced across 29 categories. Includes diverse merchant names, MCCs, and edge cases."

**Q: How often do you retrain?**
A: "Automatically after every 50 user corrections (configurable). Can also manually trigger retraining via API or schedule daily/weekly jobs."

### Business Questions

**Q: What's the ROI?**
A: "Typical customer processing 1M transactions/month saves $9,850/month vs cloud APIs, $120K/year. Payback period: < 1 month."

**Q: How long is implementation?**
A: "Pilot deployment: < 1 hour. Full production integration: 1-2 weeks depending on existing systems. We provide integration support."

**Q: Do you offer support?**
A: "Yes - documentation, Slack/email support, on-call for production issues, quarterly model updates, and custom training on your data."

**Q: Can you customize categories?**
A: "Yes - we can retrain with your taxonomy. Typically requires 500+ samples per category. Custom training takes 2-3 weeks."

**Q: What about compliance?**
A: "System is GDPR compliant (data minimization, right to erasure). PCI-DSS compatible (no card data stored). Audit logs for SOC 2. Can provide HIPAA BAA if needed."

### Deployment Questions

**Q: What are hardware requirements?**
A: "Minimum: 4 CPU cores, 8GB RAM, 20GB disk. Recommended: 8 cores, 16GB RAM, 50GB disk. Can run on AWS t3.xlarge or equivalent."

**Q: Does it support Kubernetes?**
A: "Yes - we provide Helm charts. Includes HPA for auto-scaling, rolling updates, health checks, and secrets management."

**Q: What about backups?**
A: "All stateful data in PostgreSQL (or your DB). Standard backup strategies apply. We recommend daily snapshots and point-in-time recovery."

**Q: Can it handle 1M+ transactions/day?**
A: "Yes - with horizontal scaling. Each instance handles ~10K req/hour. For 1M/day, recommend 4-6 replicas with load balancer."

---

## Troubleshooting

### Issue: Services won't start

**Solution:**
```bash
# Check Docker resources
docker stats

# View logs
docker-compose logs -f api
docker-compose logs -f ui

# Restart services
docker-compose down
docker-compose up -d
```

### Issue: UI shows "Connection refused"

**Solution:**
```bash
# Check API is running
curl http://localhost:8000/health

# Check backend logs
docker-compose logs api

# Restart UI
docker-compose restart ui
```

### Issue: LLM is slow or failing

**Solution:**
```bash
# Check Ollama status
docker-compose logs ollama

# Verify model is downloaded
docker exec -it transaction-ai-ollama ollama list

# Pull model manually if needed
docker exec -it transaction-ai-ollama ollama pull llama3.1:8b

# Disable LLM for demo if needed
# Edit docker-compose.yml: remove --profile llm
```

### Issue: Low confidence scores

**Solution:**
- "This is expected for ambiguous merchants like 'AMAZON' or 'PAYPAL'"
- "System is being honest about uncertainty"
- "Can set confidence threshold for manual review (e.g., <80%)"
- "Feedback loop will improve over time"

### Issue: Categorization seems wrong

**Solution:**
- "Check which ensemble methods voted for what"
- "Some merchants are genuinely ambiguous (e.g., Walmart → groceries or shopping)"
- "Submit feedback to improve model"
- "Can adjust ensemble weights if systematic bias"

---

## Next Steps After Demo

### For Prospects
1. **Pilot Program**
   - 30-day trial with your transaction data
   - Deploy in your staging environment
   - Evaluate accuracy on your specific use case

2. **Custom Training**
   - Train on your historical transactions
   - Customize taxonomy to your needs
   - Integrate with your existing systems

3. **Production Deployment**
   - Full integration support
   - Monitoring and alerting setup
   - SLA and support agreements

### For Technical Evaluation
1. **Provide Access**
   - GitHub repo access
   - Technical documentation
   - API sandbox environment

2. **Share Benchmarks**
   - Detailed evaluation reports
   - Performance metrics
   - Comparison with alternatives

3. **Schedule Technical Deep Dive**
   - Architecture review
   - Security assessment
   - Scalability planning

---

## Demo Checklist

### Before Demo
- [ ] Docker services running
- [ ] Health check passes
- [ ] UI loads at localhost:3000
- [ ] API docs accessible at localhost:8000/docs
- [ ] Test transactions prepared
- [ ] Backup slides ready (in case of technical issues)

### During Demo
- [ ] Start with clear problem statement
- [ ] Show live system (not just slides)
- [ ] Demonstrate key features interactively
- [ ] Highlight differentiators (accuracy, privacy, speed)
- [ ] Invite questions throughout
- [ ] Note any follow-up items

### After Demo
- [ ] Share demo recording
- [ ] Send technical documentation
- [ ] Provide API sandbox access
- [ ] Schedule follow-up call
- [ ] Request feedback on demo

---

## Additional Resources

### Documentation
- `README.md` - Comprehensive setup guide
- `PROJECT_TECHNICAL_DOCUMENTATION.md` - Full technical specs
- `docs/` - Detailed design docs
- `reports/EVALUATION_SUMMARY.md` - Validation results

### Code Examples
- `examples/test_api.py` - API usage examples
- `scripts/evaluate_f1.py` - Evaluation script
- `tests/` - 75 unit tests for reference

### Support
- GitHub Issues: [Project repo issues]
- Email: [Your support email]
- Slack: [Your workspace]
- Docs: [Your documentation site]

---

**Good luck with your demo! 🚀**

Remember: Focus on the business value (accuracy, privacy, cost) first, then show the technical excellence. Let the system speak for itself through live demonstrations.
