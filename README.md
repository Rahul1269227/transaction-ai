
# 🤖 Transaction AI - Intelligent Transaction Categorization System

> **Enterprise-grade AI system that achieves 98% accuracy in categorizing financial transactions using an ensemble of MCC codes, rules, machine learning, and LLMs.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.6-orange.svg)](https://github.com/microsoft/LightGBM)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Performance](#-performance)
- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration)
- [Training & Evaluation](#-training--evaluation)
- [Monitoring](#-monitoring)
- [Project Structure](#-project-structure)
- [Development](#-development)

---

## 🎯 Overview

Transaction AI is a **privacy-first, production-ready** system for automatically categorizing financial transactions with high accuracy. It combines multiple AI techniques in an intelligent ensemble to achieve **98%+ accuracy** while maintaining fast response times (~100ms in fast mode).

## March 2026 Refresh

- Repository maintenance update pushed for current-month activity
- Historical evaluation-log cleanup completed for public history hygiene
- Documentation re-reviewed for public presentation

### Why Transaction AI?

- **🎯 High Accuracy**: 98.38% validation accuracy, 69.2% on real-world data
- **🔒 Privacy-First**: 100% local processing, no cloud APIs required
- **⚡ Fast Performance**: ~100ms latency with intelligent fast-path optimization
- **🧠 Hybrid Intelligence**: Ensemble of MCC codes, rules, ML embeddings, and LLMs
- **📊 Production-Ready**: Docker deployment, monitoring, health checks, auto-retraining
- **📄 PDF Support**: Extract and categorize transactions from bank statements
- **🔄 Active Learning**: Auto-retrains from user feedback every 50 corrections

---

## ✨ Key Features

### 🤖 Ensemble Categorization (4 Methods)

1. **MCC Classifier** (15% weight)
   - Uses ISO 18245 merchant category codes
   - 85-95% confidence on transactions with MCC data
   - Instant categorization for MCC-enabled transactions

2. **Rule-Based Engine** (15% weight)
   - 90+ keyword patterns across 29 categories
   - Regex matching for merchant names
   - 90-98% confidence, <35ms latency

3. **ML Embedding Classifier** (65% weight - highest)
   - LightGBM model trained on 22,664+ transactions
   - sentence-transformers embeddings (all-MiniLM-L6-v2)
   - 96%+ accuracy with semantic understanding

4. **LLM Classifier** (5% weight)
   - Llama 3.1 8B (Ollama) or Azure GPT-4/GPT-4o
   - Few-shot learning with 5 category examples
   - 92% accuracy, handles edge cases

### ⚡ Smart Routing

- **Fast Mode**: Skips LLM when Rule + ML agree (≥90% confidence)
  - 70% of transactions use fast path
  - ~100ms latency vs 850ms with full ensemble
  - Maintains 98% accuracy

- **Early Exit**: High-confidence merchant/MCC matches skip ensemble entirely

- **Category-Specific Thresholds**:
  - Critical categories (Investments, Rent): 90% auto-accept
  - Medium categories (Travel, Health): 85% auto-accept
  - Low-risk (Food, Shopping): 80% auto-accept

### 📊 29 Standardized Categories

```
food_dining         groceries           transport                travel
bills               utilities           fuel                     health
education           shopping            entertainment            subscriptions
income_salary       transfers_upi       investments              atm_cash
rent                insurance           professional_services    automotive
electronics         home_improvement    pets                     kids_family
personal_care       gifts_occasions     charity_donations        taxes_government
fees_charges        fraud_security      other
```

### 🔄 Active Learning Pipeline

- User feedback stored in corrections.jsonl + database
- Auto-retraining triggered every 50 corrections
- Hot model reload with zero downtime
- User-corrected categories cached for instant future lookups

### 📄 PDF Bank Statement Processing

- Upload PDF bank statements (PhonePe, ICICI, etc.)
- Automatic transaction extraction using pdfplumber
- Batch categorization of all extracted transactions
- Supports multi-page statements (tested up to 26 pages)

### 🎨 Interactive Dashboard

- Single transaction categorization
- Batch CSV/text upload (max 1000 transactions)
- PDF bank statement upload
- Real-time ensemble voting visualization
- System health monitoring (7 components)
- Performance statistics
- User feedback submission

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Transaction AI System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Next.js    │  │   FastAPI    │  │  PostgreSQL  │           │
│  │  Dashboard   │──│   REST API   │──│   Database   │           │
│  │  (Port 3000) │  │  (Port 8000) │  │  (Port 5432) │           │
│  └──────────────┘  └───────┬──────┘  └──────────────┘           │
│                            │                                    │
│                    ┌───────┴───────┐                            │
│                    │               │                            │
│         ┌──────────▼────┐  ┌───────▼─────┐                      │
│         │  Redis Cache  │  │   Ollama    │                      │
│         │  (Port 6379)  │  │ LLM Service │                      │
│         └───────────────┘  │ (Port 11435)│                      │
│                            └─────────────┘                      │
│                                                                 │
│  ┌────────────────── Ensemble Router ─────────────────┐         │
│  │                                                    │         │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐  │         │
│  │  │   MCC   │  │  Rules  │  │   ML    │  │  LLM  │  │         │
│  │  │ (15%)   │  │  (15%)  │  │  (65%)  │  │  (5%) │  │         │
│  │  └─────────┘  └─────────┘  └─────────┘  └───────┘  │         │
│  │       ▲            ▲            ▲            ▲     │         │
│  │       └────────────┴────────────┴────────────┘     │         │
│  │              Weighted Voting System                │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                 │
│  ┌─────────── Monitoring Stack ────────────┐                    │
│  │  Prometheus (Metrics) + Grafana (Viz)   │                    │
│  └─────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Processing Flow

```
Input Transaction
      │
      ▼
┌─────────────┐
│ Preprocessor│ ── Extract MCC, amount, date, merchant
└──────┬──────┘
       ▼
┌─────────────┐
│ Normalizer  │ ── Clean text, resolve merchant aliases
└──────┬──────┘
       ▼
┌─────────────┐
│   Router    │ ── Fast path check (high confidence?)
└──────┬──────┘
       │
       ├─── YES ──▶ Return category (< 35ms)
       │
       NO
       ▼
┌─────────────────────────────┐
│        Ensemble Voting      │
│  ┌─────┬─────┬─────┬─────┐  │
│  │ MCC │ Rule│ ML  │ LLM │  │
│  │ 15% │ 15% │ 65% │ 5%  │  │
│  └─────┴─────┴─────┴─────┘  │
│           │                 │
│      Weighted Vote          │
│           │                 │
│    ┌──────▼──────┐          │
│    │  Confidence │          │
│    │  >= 80%?    │          │
│    └──────┬──────┘          │
│           │                 │
│      YES  │  NO             │
│      ▼    ▼                 │ 
│   Accept  Flag for Review   │
└─────────────────────────────┘
       │
       ▼
   Return Result + Cache
```

---

## 📊 Performance

### Accuracy Metrics

| Dataset | Accuracy | Samples |
|---------|----------|---------|
| Validation Set | **98.38%** | 5,600 |
| Real-World (PhonePe) | 66.7% | 12 |
| Real-World (ICICI) | 71.4% | 14 |
| Well-Known Brands | **95%+** | - |

### Latency Benchmarks

| Mode | P50 | P95 | P99 | Throughput |
|------|-----|-----|-----|------------|
| **Fast Mode** (70% of traffic) | 100ms | 150ms | 200ms | ~70 req/s |
| **Full Ensemble** | 850ms | 1200ms | 1500ms | ~10 req/s |
| **Rules Only** | 35ms | 50ms | 75ms | ~1000 req/s |
| **ML Only** | 115ms | 180ms | 250ms | ~100 req/s |

### Resource Requirements

- **RAM**: 16GB (8GB LLM, 4GB ML, 4GB system)
- **Disk**: 20GB
- **CPU**: 8 cores recommended (4 minimum)
- **GPU**: Optional (5-10x faster LLM inference)

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 16GB RAM, 20GB disk space
- (Optional) NVIDIA GPU for faster LLM inference

### 1. Clone Repository

```bash
git clone https://github.com/Rahul1269227/transaction-ai
cd transaction-ai
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env to configure database passwords, LLM provider, etc.
```

Key configurations:
```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# LLM Provider (choose one)
LLM_PROVIDER=ollama              # Local LLM (recommended)
# LLM_PROVIDER=azure             # Azure OpenAI

# Ensemble Weights
MCC_WEIGHT=0.15
RULE_WEIGHT=0.15
ML_WEIGHT=0.65
LLM_WEIGHT=0.05

# Performance
FAST_MODE=true
FAST_MODE_THRESHOLD=0.90
```

### 3. Start Services

#### Option A: Full Stack with LLM (Recommended)

```bash
# First time: Download LLM model (llama3.1:8b ~5GB)
docker-compose --profile llm-setup up llm-loader

# Start all services
docker-compose --profile llm up -d
```

#### Option B: Without LLM (Faster startup, 96% accuracy)

```bash
docker-compose up -d postgres redis api ui
```

#### Option C: With Monitoring (Production)

```bash
docker-compose --profile llm --profile monitoring up -d
```

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Check all services
docker-compose ps
```

### 5. Access Applications

- **Dashboard UI**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:4000 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## 🔌 API Endpoints

### Core Categorization

#### Single Transaction

```bash
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Payment to Starbucks Coffee",
    "amount": 5.50,
    "currency": "USD",
    "mcc": "5814"
  }'
```

**Response:**
```json
{
  "category": "food_dining",
  "subcategory": "Cafes & Coffee",
  "confidence": 0.95,
  "method": "merchant_gazetteer",
  "ensemble_votes": {
    "mcc": "food_dining",
    "rule": "food_dining",
    "ml": "food_dining",
    "llm": null
  },
  "requires_review": false
}
```

#### Batch Processing

```bash
curl -X POST http://localhost:8000/batch-categorize \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      "Netflix monthly subscription",
      "Uber ride to airport",
      "Whole Foods groceries"
    ]
  }'
```

#### PDF Bank Statement Upload

```bash
curl -X POST http://localhost:8000/upload-pdf \
  -F "file=@bank_statement.pdf"
```

### Feedback & Learning

#### Submit User Correction

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_text": "Payment to Netflix",
    "predicted_category": "entertainment",
    "correct_category": "subscriptions_memberships",
    "was_incorrect": true
  }'
```

#### Trigger Retraining

```bash
curl -X POST http://localhost:8000/feedback-learning
```

### Monitoring

#### System Health

```bash
curl http://localhost:8000/health
```

#### Statistics

```bash
curl http://localhost:8000/stats
```

#### Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

---

## ⚙️ Configuration

### Environment Variables

#### Database Configuration
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=transactions
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

#### LLM Configuration

**Ollama (Local)**
```bash
LLM_PROVIDER=ollama
LLM_URL=http://llm-service:11434
LLM_MODEL=llama3.1:8b
LLM_TIMEOUT=120.0
```

**Azure OpenAI**
```bash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

#### Ensemble Configuration
```bash
# Weights (must sum to 1.0)
MCC_WEIGHT=0.15
RULE_WEIGHT=0.15
ML_WEIGHT=0.65
LLM_WEIGHT=0.05

# Thresholds
ML_CONFIDENCE_THRESHOLD=0.80
RULE_CONFIDENCE_THRESHOLD=0.80

# Performance
USE_ENSEMBLE=true
FAST_MODE=true
FAST_MODE_THRESHOLD=0.90
ENABLE_PARALLEL=true
```

#### Auto-Retraining
```bash
AUTO_RETRAIN_ENABLED=true
AUTO_RETRAIN_THRESHOLD=50  # Retrain after 50 corrections
```

### Taxonomy Configuration

Edit `data/taxonomy.yaml` to add/modify categories:

```yaml
categories:
  - name: "Food & Dining"
    id: "food_dining"
    description: "Restaurants, food delivery, cafes"
    mcc_codes:
      - "5812"  # Restaurants
      - "5814"  # Fast Food
    keywords:
      - "restaurant"
      - "cafe"
      - "starbucks"
    patterns:
      - "(?i).*restaurant.*"
      - "(?i).*cafe.*"
```

### Merchant Gazetteer

Add merchant aliases in `data/gazetteer/merchant_aliases.csv`:

```csv
merchant_id,canonical_name,aliases,category,subcategory
1,STARBUCKS,"starbucks,starbuck,sbux",food_dining,Cafes & Coffee
2,NETFLIX,"netflix,netflix.com",subscriptions_memberships,Streaming Services
```

---

## 🎓 Training & Evaluation

### Training a New Model

#### Quick Training

```bash
python3 scripts/train.py
```

#### Advanced Training with Hyperparameters

```bash
python3 scripts/train_model.py \
  --train data/train.jsonl \
  --val data/test.jsonl \
  --output models/transaction_classifier \
  --n-estimators 200 \
  --learning-rate 0.05 \
  --max-depth 10
```

**Hyperparameters:**
- `n_estimators`: Number of boosting rounds (default: 200)
- `learning_rate`: Learning rate (default: 0.05)
- `max_depth`: Maximum tree depth (default: 10)
- `num_leaves`: Maximum number of leaves (default: 50)
- `min_child_samples`: Minimum samples per leaf (default: 20)

### Evaluation

#### F1 Score Evaluation

```bash
python3 scripts/evaluate_f1.py \
  --model models/transaction_classifier \
  --test data/test.jsonl
```

#### Bias & Fairness Evaluation

```bash
python3 scripts/evaluate_bias.py \
  --model models/transaction_classifier \
  --test data/test.jsonl \
  --output reports/bias_report.json
```

### Active Learning with User Feedback

```bash
# Retrain with user corrections
python3 scripts/retrain_with_corrections.py \
  --corrections data/corrections/corrections.jsonl \
  --model-path models/transaction_classifier

# Background auto-retraining
python3 scripts/feedback_learning.py
```

---

## 📊 Monitoring

### Prometheus Metrics

```bash
# Access metrics endpoint
curl http://localhost:8000/metrics
```

**Available Metrics:**
- `categorization_requests_total` - Total requests by endpoint
- `categorization_latency_seconds` - Latency histogram
- `method_usage_total` - Usage by method (rule/ml/llm)
- `categorization_requires_review_total` - Review rate
- `categorization_cache_events_total` - Cache hit/miss
- `ensemble_agreement_ratio` - Method agreement rate

### Grafana Dashboard

1. Access Grafana: http://localhost:4000
2. Login: admin/admin
3. Navigate to pre-configured dashboard: "Transaction AI Performance"

**Dashboard Panels:**
- Request Rate & Throughput
- P50/P95/P99 Latency
- Cache Hit Ratio
- Method Distribution
- Review Rate Trends
- Resource Usage (CPU, Memory)

### Health Monitoring

```bash
# Component-level health
curl http://localhost:8000/health | jq

# Response:
{
  "status": "healthy",
  "components": {
    "router": "healthy",
    "normalizer": "healthy",
    "rule_categorizer": "healthy",
    "ml_classifier": "healthy",
    "llm_classifier": "healthy",
    "merchant_resolver": "healthy",
    "database": "healthy",
    "cache": "healthy"
  }
}
```

---

## 📁 Project Structure

```
transaction-ai/
├── apps/
│   └── api/
│       └── main.py              # FastAPI application (1,480 lines)
├── core/
│   ├── model/
│   │   ├── ensemble_router.py   # Ensemble voting system
│   │   ├── llm_classifier.py    # LLM categorization
│   │   ├── classifier.py        # ML classifier
│   │   ├── mcc_classifier.py    # MCC code classifier
│   │   └── router.py            # Hybrid router
│   ├── rules/
│   │   └── engine.py            # Rule-based categorization
│   ├── normalize/
│   │   └── normalizer.py        # Text normalization
│   ├── resolve/
│   │   └── resolver.py          # Merchant resolution
│   ├── parsers/
│   │   └── pdf_parser.py        # PDF bank statement parser
│   └── models.py                # Pydantic models
├── data/
│   ├── taxonomy.yaml            # 29 category definitions
│   ├── gazetteer/
│   │   └── merchant_aliases.csv # Merchant aliases (353+)
│   ├── train.jsonl              # Training data (22,664)
│   ├── test.jsonl               # Test data (5,600)
│   └── corrections/
│       └── corrections.jsonl    # User feedback
├── scripts/
│   ├── train.py                 # Training script
│   ├── evaluate_f1.py           # F1 evaluation
│   ├── evaluate_bias.py         # Fairness evaluation
│   └── feedback_learning.py     # Auto-retraining
├── ui/                          # Next.js dashboard
│   ├── app/
│   ├── components/
│   └── package.json
├── infra/
│   ├── docker-compose.yaml      # Multi-container orchestration
│   └── Dockerfile               # API container
├── monitoring/
│   ├── prometheus.yml           # Metrics config
│   ├── grafana-dashboard.json   # Pre-built dashboard
│   └── alerts.yml               # Alert rules
├── tests/                       # Test suite (15+ files)
├── models/                      # Trained models
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Rahul1269227/transaction-ai
cd transaction-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install UI dependencies
cd ui && npm install && cd ..
```

### Run Services Locally

```bash
# Terminal 1: Start database & cache
docker-compose up -d postgres redis

# Terminal 2: Start API
MODEL_PATH=models/transaction_classifier \
python3 -m uvicorn apps.api.main:app --reload --port 8000

# Terminal 3: Start UI
cd ui && npm run dev
```

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_ensemble_router.py

# With coverage
pytest --cov=core --cov-report=html
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Adding New Categories

1. Edit `data/taxonomy.yaml`:
```yaml
- name: "New Category"
  id: "new_category"
  description: "Description"
  keywords: ["keyword1", "keyword2"]
  patterns: ["(?i)pattern.*"]
```

2. Add training examples to `data/train.jsonl`:
```json
{"text": "Example transaction", "label": "new_category"}
```

3. Retrain model:
```bash
python3 scripts/train.py
```

### Adding Merchant Aliases

Edit `data/gazetteer/merchant_aliases.csv`:
```csv
100,NEW_MERCHANT,"merchant,alias1,alias2",category,subcategory
```

Reload API to apply changes.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LightGBM** - Microsoft's gradient boosting framework
- **sentence-transformers** - Hugging Face semantic embeddings
- **Ollama** - Local LLM inference
- **FastAPI** - Modern Python web framework
- **Next.js** - React framework for production

---

## 📞 Support

- **Documentation**: [https://transaction-ai.readthedocs.io/en/latest/](https://transaction-ai.readthedocs.io/en/latest/)
- **Issues**: GitHub Issues
- **Real-World Testing**: See [REAL_WORLD_TEST_RESULTS.md](REAL_WORLD_TEST_RESULTS.md)

---

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Real-time transaction streaming
- [ ] Multi-language support
- [ ] Custom category training UI
- [ ] Fraud detection integration
- [ ] Export to accounting software (QuickBooks, Xero)
- [ ] Smart budgeting recommendations
- [ ] Transaction deduplication

---

**Built with ❤️ for accurate, private, and intelligent transaction categorization**
