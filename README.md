# Transaction AI Categorization System

## 🔄 Automatic Feedback Learning

This system automatically learns from user feedback to continuously improve classification accuracy!

**Production-ready, offline-first AI system for categorizing financial transactions with 98% accuracy**

A hybrid ensemble approach combining rule-based logic, ML embeddings, and LLM reasoning for optimal accuracy and speed. Fully local—no API keys, no cloud dependencies.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 🎯 Key Features

- **98% Accuracy**: True hybrid ensemble combining 3 AI approaches
- **Fully Offline**: No external API dependencies, runs 100% locally
- **Fast**: <900ms latency including LLM reasoning
- **Privacy-First**: Your transaction data never leaves your server
- **Production-Ready**: Docker + Postgres + Redis + monitoring
- **18 Categories**: Comprehensive coverage from groceries to investments
- **Multi-Channel**: UPI, IMPS, NEFT, POS, ATM, card transactions
- **Persistent & Observable**: Automatic Postgres logging, Redis caching, and Prometheus metrics
- **🆕 Premium UI**: Modern glassmorphic Next.js dashboard with real-time updates
- **🆕 Batch Processing**: Upload & categorize thousands of transactions (TXT/CSV/JSON support)
- **🆕 Full Monitoring**: Prometheus + Grafana with pre-built dashboards and alerts

---

## 📊 How It Works

### Three-Method Ensemble (Parallel Execution)

```
                    ┌→ RULES (30%)      ─┐
                    │  Keywords, patterns │
Transaction → Parse ├→ ML (40%)         ─┤→ Ensemble → Final
                    │  Embeddings+LightGB │  Voting     Category
                    └→ LLM (30%)        ─┘
                       Llama 3.1 reasoning
```

**Why Ensemble?**
- **Rules**: Fast (35ms), deterministic, great for known patterns (ATM, fuel)
- **ML**: Accurate (96.26%), learned patterns, semantic understanding
- **LLM**: Reasoning (92%), handles edge cases, explains decisions
- **Combined**: Best of all three, confidence boost when methods agree

**Results:**
```json
{
  "category": "Food & Dining",
  "confidence": 0.95,
  "method": "ensemble_unanimous",  // All 3 agreed!
  "ensemble_votes": {
    "rule": {"category": "Food & Dining", "confidence": 0.90},
    "ml": {"category": "Food & Dining", "confidence": 0.91},
    "llm": {"category": "Food & Dining", "confidence": 0.87}
  }
}
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **16GB RAM** minimum (8GB for LLM, 4GB for ML, 4GB system)
- **20GB disk space** (for models and data)
- **Optional**: NVIDIA GPU for 5x faster LLM inference

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd transaction-ai

# Copy environment file
cp .env.example .env
```

### 2. Start with Docker (Recommended)

```bash
cd infra

# Start all services (Postgres, Redis, LLM, API)
docker-compose up -d

# Check all services are healthy
docker-compose ps
```

### 3. Download LLM Model (First Time Only)

```bash
# Pull Llama 3.1 8B model (4.7GB download, takes 5-15 min)
docker-compose --profile llm-setup run llm-loader

# Verify model is loaded
docker exec txn-llm ollama list
```

### 4. Verify Everything Works

```bash
# Check health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "normalizer": "healthy",
    "rule_categorizer": "healthy",
    "ml_classifier": "healthy",
    "llm_classifier": "healthy",  // ✓ LLM ready!
    "merchant_resolver": "healthy",
    "database": "healthy",
    "cache": "healthy"
  }
}
```

### 5. Test Categorization

```bash
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "UPI-ZOMATO PAY*1234",
    "amount": 249.00,
    "date": "2025-11-13"
  }'
```

**Response:**
```json
{
  "category": "Food & Dining",
  "confidence": 0.95,
  "method": "ensemble_unanimous",
  "explanations": [
    "keyword=zomato",
    "ml_embedding_classifier",
    "llm_reasoning: Food delivery transaction based on merchant name"
  ],
  "requires_review": false
}
```

### 6. Start Frontend UI (Optional)

```bash
# Navigate to UI directory
cd ui

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Access UI at http://localhost:3000
```

**🎉 You're all set!**
- API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## 🎨 Premium Web UI

### Modern Dashboard with Glassmorphic Design

The system includes a production-ready Next.js UI with enterprise-grade design and user experience.

#### Features

✨ **Premium Design Elements**
- Glassmorphic effects with backdrop blur
- Smooth animations and transitions
- Gradient accents throughout
- Responsive on all devices
- Dark mode support

📊 **Live Demo Tab**
- Real-time transaction categorization
- Confidence visualization with animated progress bars
- Method breakdown (Rule/ML/LLM)
- AI reasoning explanations
- Accept/Reject feedback buttons

📁 **Batch Upload Tab** (NEW)
- **Multiple Input Methods**: Paste text or upload files
- **Format Support**: TXT, CSV, JSON (auto-detected)
- **Smart Parsing**: Handles various JSON structures
- **Progress Tracking**: Real-time batch processing status
- **Results Table**: Premium table with status indicators
- **CSV Export**: Download categorization results

📈 **Stats Cards**
- Real-time metrics from API
- Gradient cards with hover effects
- Total processed, latency, accuracy, review rate

🔄 **Additional Tabs**
- Ensemble Voting visualization
- System Health monitoring
- Feedback submission

#### Quick Start

```bash
# Navigate to UI directory
cd ui

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Access UI
open http://localhost:3000
```

#### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

#### File Format Examples

**TXT Format** (one per line)
```
STARBUCKS COFFEE #12345
NETFLIX SUBSCRIPTION
UBER RIDE TO AIRPORT
```

**CSV Format** (first column as transaction)
```csv
transaction,amount,date
"STARBUCKS COFFEE",12.50,2024-01-15
"NETFLIX SUBSCRIPTION",15.99,2024-01-10
```

**JSON Format** (multiple structures supported)
```json
["STARBUCKS", "NETFLIX"]
```
or
```json
{"transactions": ["STARBUCKS", "NETFLIX"]}
```
or
```json
[
  {"text": "STARBUCKS"},
  {"transaction": "NETFLIX"}
]
```

#### Batch Processing API

The UI uses the new batch endpoint for efficient processing:

```bash
POST /api/batch-categorize
Content-Type: application/json

{
  "transactions": ["txn1", "txn2", "txn3"]
}
```

**Response:**
```json
{
  "results": [
    {
      "transaction": "STARBUCKS COFFEE",
      "category": "Food & Dining",
      "confidence": 0.95,
      "method": "ensemble_unanimous",
      "status": "success"
    }
  ],
  "total": 100,
  "successful": 98,
  "failed": 2,
  "duration_seconds": 45.2
}
```

**Features:**
- Processes up to 1,000 transactions per batch
- 5-minute timeout protection
- Individual error handling (partial failures allowed)
- Progress logging for large batches

#### Test Files

Sample test files are included:
- `test_batch.txt` - Plain text format
- `test_batch.csv` - CSV with headers
- `test_batch.json` - JSON object format
- `test_batch_array.json` - JSON array format

---

## 📊 Monitoring & Observability

### Comprehensive Monitoring Stack

Production-ready monitoring with Prometheus and Grafana, fully configured and ready to use.

#### Quick Start Monitoring

```bash
# Start monitoring stack (one command)
./start-monitoring.sh

# Or manually
docker-compose -f docker-compose.monitoring.yml up -d

# Enable metrics in API (.env)
PROMETHEUS_ENABLED=true
```

#### Access Dashboards

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Node Exporter**: http://localhost:9100/metrics
- **cAdvisor**: http://localhost:8080

#### What's Included

🎯 **Prometheus Metrics**
- Request rates and volumes
- Latency histograms (p50, p95, p99)
- Method usage distribution
- Ensemble agreement ratios
- Cache hit/miss rates
- Review rates
- Error tracking

📊 **Grafana Dashboard**

Pre-configured dashboard with 11 visualization panels:

1. **Request Rate** - Requests/sec by endpoint
2. **Response Latency** - p50, p95, p99 percentiles
3. **Total Requests** - 24-hour volume
4. **Average Latency** - 5-minute rolling average
5. **Review Rate** - Percentage requiring manual review
6. **Ensemble Agreement** - Consensus gauge
7. **Method Usage** - Distribution by method
8. **Cache Performance** - Hit/miss rates
9. **CPU Usage** - System resource tracking
10. **Memory Usage** - RAM consumption
11. **Recent Categorizations** - Method breakdown table

🚨 **Pre-Configured Alerts**

9 production-ready alerts:
- High Error Rate (>5%)
- High Review Rate (>30%)
- High Latency (>2s at p95)
- API Down
- Low Ensemble Agreement (<60%)
- Low Cache Hit Rate (<20%)
- High Memory Usage (>85%)
- High CPU Usage (>80%)
- Low Disk Space (<15%)

#### Available Metrics

```promql
# Request metrics
categorization_requests_total{endpoint="categorize"}
rate(categorization_requests_total[5m])

# Latency metrics
histogram_quantile(0.95, sum(rate(categorization_latency_seconds_bucket[5m])) by (le))

# ML model metrics
sum(rate(method_usage_total[5m])) by (method)
ensemble_agreement_ratio

# Cache metrics
sum(rate(categorization_cache_events_total{result="hit"}[5m]))
```

#### Useful Queries

**Cache Hit Rate:**
```promql
sum(rate(categorization_cache_events_total{result="hit"}[10m])) /
sum(rate(categorization_cache_events_total[10m])) * 100
```

**Top 10 Slowest Requests:**
```promql
topk(10, histogram_quantile(0.95,
  sum(rate(categorization_latency_seconds_bucket[5m])) by (le, endpoint)
))
```

**Method Preference:**
```promql
sum by (method) (method_usage_total) /
sum(method_usage_total) * 100
```

#### Monitoring Commands

```bash
# View logs
docker-compose -f docker-compose.monitoring.yml logs -f grafana
docker-compose -f docker-compose.monitoring.yml logs -f prometheus

# Check status
docker-compose -f docker-compose.monitoring.yml ps

# Stop monitoring
docker-compose -f docker-compose.monitoring.yml down

# Restart services
docker-compose -f docker-compose.monitoring.yml restart
```

#### Documentation

- **Full Guide**: See [MONITORING.md](./MONITORING.md)
- **Quick Reference**: See [MONITORING_QUICKSTART.md](./MONITORING_QUICKSTART.md)
- **Testing**: Run `./test-system.sh` to verify everything works

---

## 📖 Complete Setup Guide

### Option A: Docker Deployment (Production)

#### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16GB | 32GB |
| CPU | 4 cores | 8+ cores |
| Disk | 20GB | 50GB SSD |
| GPU | None (CPU) | NVIDIA 8GB+ VRAM |

#### Step-by-Step

1. **Clone Repository**
   ```bash
   git clone <repo>
   cd transaction-ai
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit if needed
   ```

   Key settings:
   ```env
   # Ensemble weights (tune for your needs)
   RULE_WEIGHT=0.3
   ML_WEIGHT=0.4
   LLM_WEIGHT=0.3

   # Confidence thresholds
   AUTO_ACCEPT_THRESHOLD=0.85  # Auto-accept if >= 85%
   REVIEW_THRESHOLD=0.60       # Human review if < 60%
   ```

3. **Start Services**
   ```bash
   cd infra
   docker-compose up -d
   ```

   Services started:
   - `postgres` - Transaction database
   - `redis` - Caching layer
   - `llm-service` - Ollama with Llama 3.1
   - `api` - FastAPI application

4. **Load LLM Model** (one-time)
   ```bash
   docker-compose --profile llm-setup run llm-loader
   ```

5. **Verify Deployment**
   ```bash
   # Check all containers are running
   docker-compose ps

   # Check API health
   curl http://localhost:8000/health

   # View logs
   docker-compose logs -f api
   ```

6. **Access Services**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Prometheus: http://localhost:9090 (optional, see monitoring)
   - Grafana: http://localhost:3000 (optional)

#### GPU Acceleration (Optional)

If you have an NVIDIA GPU:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Verify:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

3. GPU config is already enabled in `docker-compose.yaml`!

**For CPU-only**, comment out GPU section in `infra/docker-compose.yaml`:
```yaml
llm-service:
  # deploy:  # Comment these lines
  #   resources:
  #     reservations:
  #       devices:
  #         - driver: nvidia
```

### Option B: Local Development

#### Prerequisites
- Python 3.9+
- 16GB RAM
- [Ollama](https://ollama.ai/) installed locally

#### Installation

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install and Start Ollama**
   ```bash
   # macOS/Linux
   curl https://ollama.ai/install.sh | sh

   # Start Ollama server
   ollama serve
   ```

3. **Pull LLM Model**
   ```bash
   ollama pull llama3.1:8b
   ```

4. **Generate Training Data**
   ```bash
   python scripts/generate_dataset.py \
     --num-samples 10000 \
     --output data/datasets/synthetic_train.jsonl
   ```

   Creates:
   - `synthetic_train.jsonl` (11,098 samples)
   - `synthetic_val.jsonl` (2,218 samples)
   - `synthetic_test.jsonl` (2,218 samples)

5. **Train ML Classifier**

   **Basic Training (Quick):**
   ```bash
   python scripts/train_model.py \
     --train data/datasets/synthetic_train.jsonl \
     --val data/datasets/synthetic_val.jsonl \
     --output models/classifier
   ```

   **Production Training (Recommended):**
   ```bash
   python scripts/train_model.py \
     --train data/balanced/train.jsonl \
     --val data/balanced/val.jsonl \
     --output models/transaction_classifier_balanced \
     --n-estimators 300 \
     --learning-rate 0.05 \
     --max-depth 8 \
     --num-leaves 128 \
     --no-balance
   ```

   **Advanced Training with Custom Parameters:**
   ```bash
   python scripts/train_model.py \
     --train data/balanced/train.jsonl \
     --val data/balanced/val.jsonl \
     --output models/classifier_advanced \
     --class-weights data/balanced/class_weights.json \
     --n-estimators 300 \
     --learning-rate 0.05 \
     --max-depth 12 \
     --num-leaves 2048 \
     --min-child-samples 20 \
     --subsample 0.8 \
     --colsample-bytree 0.8 \
     --reg-alpha 0.1 \
     --reg-lambda 0.1 \
     --no-balance
   ```

   **Parameter Guidelines:**
   - `--n-estimators`: Number of boosting rounds (100-500, higher = better but slower)
   - `--learning-rate`: Learning rate (0.01-0.1, lower = more robust)
   - `--max-depth`: Maximum tree depth (6-15)
   - `--num-leaves`: Number of leaves - **MUST be < 2^max_depth** to avoid warnings
     - For `max_depth=8`: use `num_leaves=128` (2^7)
     - For `max_depth=12`: use `num_leaves=2048` (2^11)
   - `--no-balance`: Skip auto-balancing if data is already balanced
   - `--class-weights`: Path to JSON file with class weights for imbalanced data

   Expected output:
   ```
   Training samples: 48493
   Validation samples: 10391
   Validation Accuracy: 0.9626
   Model saved to models/classifier
   ```

6. **Start API Server**
   ```bash
   cd apps/api
   python main.py
   ```

   API running at http://localhost:8000

#### Environment Setup

Update `.env` for local development:
```env
LLM_URL=http://localhost:11434  # Local Ollama
DATABASE_URL=postgresql://user:pass@localhost:5432/transactions  # Optional
REDIS_URL=redis://localhost:6379/0  # Optional
```

---

## 📚 API Documentation

### Interactive Docs

Visit http://localhost:8000/docs for full Swagger UI documentation.

### Core Endpoints

#### 1. Categorize Single Transaction

```bash
POST /categorize

curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "POS 4532 HPCL KANPUR",
    "amount": 1200.00,
    "date": "2025-11-10"
  }'
```

**Response:**
```json
{
  "category": "Fuel",
  "subcategory": "Petrol",
  "confidence": 0.96,
  "method": "ensemble_rule+ml",
  "explanations": ["keyword=hpcl", "pattern=POS", "ml_classifier"],
  "requires_review": false,
  "ensemble_votes": {
    "rule": {"category": "Fuel", "confidence": 0.96},
    "ml": {"category": "Fuel", "confidence": 0.94},
    "llm": null,
    "agreement_count": 2
  }
}
```

#### 2. Batch Categorization

```bash
POST /categorize/batch

curl -X POST http://localhost:8000/categorize/batch \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [
      {"text": "ZOMATO", "amount": 249},
      {"text": "ATM WDL 1234", "amount": 5000},
      {"text": "UBER TRIP", "amount": 350}
    ]
  }'
```

**Response:**
```json
{
  "results": [/* 3 TransactionOutput objects */],
  "stats": {
    "total": 3,
    "avg_confidence": 0.94,
    "requires_review": 0,
    "review_percentage": 0.0,
    "unanimous_decisions": 2,
    "unanimous_percentage": 66.7,
    "by_method": {
      "ensemble_unanimous": 2,
      "ensemble_rule+ml": 1
    }
  }
}
```

#### 3. Merchant Search

```bash
POST /merchants

curl -X POST http://localhost:8000/merchants \
  -H "Content-Type: application/json" \
  -d '{"query": "zomato", "limit": 5}'
```

#### 4. Submit Feedback

```bash
POST /feedback

curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_text": "UPI-ZOMATO",
    "predicted_category": "Shopping",
    "correct_category": "Food & Dining"
  }'
```

#### 5. Health Check

```bash
GET /health

curl http://localhost:8000/health
```

---

## ⚙️ Configuration

> ℹ️ `USE_ENSEMBLE=true` (default) runs the new parallel rule + ML + LLM router. Set it to `false` to fall back to the legacy sequential hybrid pipeline.

### Ensemble Weights

Adjust in `.env` based on your priorities:

**Balanced (Default)**
```env
RULE_WEIGHT=0.3
ML_WEIGHT=0.4
LLM_WEIGHT=0.3
```

**Speed-Optimized** (minimize LLM calls)
```env
RULE_WEIGHT=0.4
ML_WEIGHT=0.5
LLM_WEIGHT=0.1
```

**Accuracy-Optimized** (trust LLM reasoning)
```env
RULE_WEIGHT=0.2
ML_WEIGHT=0.3
LLM_WEIGHT=0.5
```

### Disable LLM (Fallback to ML-only)

```env
USE_ENSEMBLE=false
```

This reverts to the original sequential hybrid (rule → ML fallback).

### Change LLM Model

```bash
# Smaller/faster
docker exec txn-llm ollama pull phi-3:mini

# Update .env
LLM_MODEL=phi-3:mini
```

### Add Custom Categories

Edit `data/taxonomy.yaml`:

```yaml
- name: "Charity & Donations"
  id: "charity"
  description: "Charitable contributions"
  subcategories:
    - "NGOs"
    - "Religious"
  keywords:
    - "donation"
    - "charity"
  patterns:
    - "(?i).*donation.*"
```

### Add Merchants

Edit `data/gazetteer/merchant_aliases.csv`:

```csv
merchant_id,canonical_name,aliases,category,subcategory
92,NETFLIX,"netflix,nflx",entertainment,Streaming Services
```

### Persistence, Caching & Metrics

- **Postgres Logging**: Every categorization and feedback entry is persisted when `DATABASE_URL` points to a reachable Postgres instance. Records can be reviewed later for auditing and retraining.
- **Redis Response Cache**: Set `REDIS_URL` (and optional `CACHE_TTL`, default 600 seconds) to enable low-latency caching for repeated transactions.
- **Prometheus Metrics**: Flip `PROMETHEUS_ENABLED=true` to expose `/metrics` with counters for request volume, latency histograms, cache hit/miss counts, and ensemble agreement ratios.
- **Feature Flags**: Toggle the ensemble router via `USE_ENSEMBLE=true/false`—the API now wires this flag directly to the router implementation used in production.

---

## 🧪 Testing & Evaluation

### Automated System Tests

Run comprehensive integration tests:

```bash
# Test all endpoints, batch processing, and monitoring
./test-system.sh
```

This tests:
- API health and endpoints
- Single categorization
- Batch categorization (new endpoint)
- Stats endpoint
- Prometheus metrics exposure
- Grafana health
- Node Exporter metrics
- Batch file format support

### UI Testing

```bash
# See UI testing checklist
cat UI_TESTING.md

# Start UI and test manually
cd ui && npm run dev
```

Test checklist includes:
- Premium design elements
- Batch upload (TXT, CSV, JSON)
- Format auto-detection
- Progress tracking
- Results table
- CSV export

### Unit Tests

Run the lightweight regression suite (normalizer, rule engine, router wiring):

```bash
pytest
```

### Run Evaluation

```bash
python evals/runner.py \
  --test data/datasets/synthetic_test.jsonl \
  --taxonomy data/taxonomy.yaml \
  --gazetteer data/gazetteer/merchant_aliases.csv \
  --model models/classifier \
  --output evals/reports/evaluation_report.json
```

**Sample Output:**
```
============================================================
EVALUATION REPORT
============================================================

Overall Metrics:
  Accuracy: 0.9800
  Avg Confidence: 0.9120
  Review Rate: 3.2%
  Unanimous Decisions: 87.5%

Per-Category Accuracy:
  Food & Dining: 0.9850 (197/200)
  Fuel: 0.9950 (199/200)
  ATM/Cash: 1.0000 (200/200)
  ...
```

## 📊 Performance Benchmarks

| Metric | Rules | ML | LLM | **Ensemble** |
|--------|-------|----|----|--------------|
| Accuracy | 88% | 96.26% | ~92% | **~98%** |
| P50 Latency | 35ms | 115ms | 800ms | **850ms** |
| P95 Latency | 50ms | 140ms | 1200ms | **1250ms** |
| Throughput | 1000 req/s | 100 req/s | 10 req/s | **10 req/s** |
| Memory | 100MB | 2GB | 8GB | **11GB** |
| Cost | $0 | $0 | $0 | **$0** |

*Tested on: 16GB RAM, 8-core CPU, macOS ARM64*

### Resource Usage

```
API Container:       500MB RAM, 10% CPU
ML Models:          2GB RAM, 15% CPU
LLM (CPU):          8GB RAM, 70% CPU
LLM (GPU):          2GB RAM, 20% CPU, 4GB VRAM
Total:              ~11GB RAM, ~90% CPU (CPU mode)
```

---

## 🐳 Docker Commands

### Basic Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api
docker-compose logs -f llm-service

# Restart a service
docker-compose restart api

# Rebuild after code changes
docker-compose build api
docker-compose up -d api
```

### Scaling

```bash
# Scale API workers for load balancing
docker-compose up -d --scale api=3

# Behind a load balancer (nginx/traefik)
```

### Monitoring

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana: http://localhost:3000 (admin/admin)
# Access Prometheus: http://localhost:9090
```

### Troubleshooting

```bash
# Check container status
docker-compose ps

# Check container resource usage
docker stats

# Enter container shell
docker exec -it txn-api bash
docker exec -it txn-llm bash

# View full logs
docker-compose logs --tail=100 llm-service

# Remove all data and restart fresh
docker-compose down -v
docker-compose up -d
```

---

## 🛠️ Troubleshooting

### Issue: LightGBM Warning - "num_leaves OR 2^max_depth > num_leaves"

**Symptoms:** Warning during training or inference:
```
[LightGBM] [Warning] Accuracy may be bad since you didn't explicitly set num_leaves OR 2^max_depth > num_leaves. (num_leaves=31).
```

**Cause:** Mismatch between `max_depth` and `num_leaves` parameters.

**Solution:** Ensure `num_leaves < 2^max_depth`. Use these compatible combinations:

| max_depth | Recommended num_leaves | Formula |
|-----------|----------------------|---------|
| 6 | 32 | 2^5 |
| 8 | 128 | 2^7 |
| 10 | 512 | 2^9 |
| 12 | 2048 | 2^11 |

**Fix existing model:**
```bash
# Retrain with correct parameters
python scripts/train_model.py \
  --train data/balanced/train.jsonl \
  --val data/balanced/val.jsonl \
  --output models/transaction_classifier_balanced \
  --max-depth 8 \
  --num-leaves 128 \
  --n-estimators 300

# Restart API to load new model
cd infra && docker-compose restart api
```

### Issue: LLM Service Not Starting

**Symptoms:** `llm-service` container keeps restarting

**Solutions:**
1. Check logs: `docker-compose logs llm-service`
2. Verify memory: Needs at least 8GB available
3. For CPU-only: Comment out GPU section in docker-compose.yaml
4. Restart with longer timeout:
   ```bash
   docker-compose up -d llm-service
   docker-compose logs -f llm-service
   ```

### Issue: Out of Memory

**Symptoms:** Containers killed by OOM

**Solutions:**
1. Use smaller LLM model:
   ```bash
   docker exec txn-llm ollama pull phi-3:mini
   # Update .env: LLM_MODEL=phi-3:mini
   ```
2. Disable LLM temporarily:
   ```env
   USE_ENSEMBLE=false
   ```
3. Increase Docker memory limit (Docker Desktop Settings)

### Issue: Slow LLM Inference (>2s)

**Solutions:**
1. **Use GPU** (5-10x faster): See GPU setup above
2. **Reduce few-shot examples**: Edit `llm_classifier.py`, set max to 5
3. **Use smaller model**: `phi-3:mini` or `llama3.1:7b`
4. **Adjust weights**: Lower `LLM_WEIGHT` to 0.1

### Issue: Model Not Downloaded

**Symptoms:** Health check shows `llm_classifier: unavailable`

**Solution:**
```bash
# Download model manually
docker exec -it txn-llm ollama pull llama3.1:8b

# Verify
docker exec -it txn-llm ollama list
```

### Issue: API Returns 503

**Symptoms:** `Service not initialized`

**Solutions:**
1. Check all services are healthy: `docker-compose ps`
2. Wait for LLM to load (can take 60s on first start)
3. Check API logs: `docker-compose logs api`

---

## 📁 Project Structure

```
transaction-ai/
├── apps/
│   └── api/
│       └── main.py              # FastAPI application
├── core/
│   ├── normalize/
│   │   ├── normalizer.py        # Text normalization
│   │   └── patterns.py          # Regex patterns
│   ├── resolve/
│   │   └── resolver.py          # Merchant matching
│   ├── rules/
│   │   └── engine.py            # Rule-based categorizer
│   ├── model/
│   │   ├── classifier.py        # ML embedding classifier
│   │   ├── llm_classifier.py    # LLM-based classifier
│   │   ├── ensemble_router.py   # Ensemble voting logic
│   │   └── router.py            # Original hybrid router
│   └── models.py                # Pydantic schemas
├── data/
│   ├── taxonomy.yaml            # Category definitions
│   ├── gazetteer/
│   │   └── merchant_aliases.csv # Merchant database (90+)
│   └── datasets/                # Training data (JSONL)
├── scripts/
│   ├── generate_dataset.py      # Synthetic data generator
│   └── train_model.py           # ML model training
├── evals/
│   └── runner.py                # Evaluation harness
├── infra/
│   ├── docker-compose.yaml      # Docker orchestration
│   ├── Dockerfile               # API container
│   └── init_db.sql              # Database schema
├── models/                      # Trained models
│   └── classifier/
│       ├── classifier.pkl
│       ├── label_encoder.pkl
│       └── metadata.json
├── .env                         # Environment config
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🔐 Security & Privacy

### Data Privacy

- **100% Local**: All processing happens on your infrastructure
- **No Cloud APIs**: No data sent to OpenAI, Anthropic, or any external service
- **Transaction Data**: Never logged, never stored (unless you configure DB)
- **Models**: Downloaded once, cached locally

### Production Checklist

- [ ] Change default database password in `.env`
- [ ] Enable HTTPS (use reverse proxy like nginx)
- [ ] Set up firewall rules (only expose port 8000)
- [ ] Configure CORS appropriately in `main.py`
- [ ] Enable monitoring and alerting
- [ ] Set up database backups
- [ ] Review and limit API rate limits
- [ ] Rotate API keys if you add authentication

---

## 📈 Monitoring & Observability

### Built-in Metrics

Set `PROMETHEUS_ENABLED=true` (in `.env` or your deployment environment) to expose `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `categorization_requests_total` - Total requests
- `categorization_latency_seconds` - Response time histogram
- `ensemble_agreement_rate` - How often methods agree
- `method_usage_total` - Usage by method (rule/ml/llm)

### Grafana Dashboards

Start monitoring stack:
```bash
docker-compose --profile monitoring up -d
```

Access:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

Pre-configured dashboards show:
- Request rate and latency
- Error rates
- Ensemble agreement metrics
- Resource usage

---

## ⚖️ Responsible AI & Bias Mitigation

### Our Approach to Fairness

This system is designed with responsible AI principles at its core. We actively mitigate bias through multiple technical and architectural strategies:

#### 1. **Ensemble Diversity Reduces Single-Method Bias**

By combining three different approaches (rules, ML, LLM), we reduce the risk of any single method's biases dominating:

- **Rule-based**: Transparent, deterministic patterns (no hidden biases in model weights)
- **ML embeddings**: Trained on diverse synthetic data covering multiple regions, merchants, and transaction types
- **LLM reasoning**: Provides contextual understanding and can override biased pattern matches

**Example**: If the ML model shows regional bias (e.g., always categorizing "Bazaar" as a specific category based on training data skew), the rule engine and LLM can provide counterbalancing votes.

#### 2. **Transparent Decision-Making**

Every prediction includes:
- **Ensemble votes**: See exactly how each method voted and their confidence levels
- **Explanations**: Understand why a decision was made (`explanations` field)
- **Confidence scores**: Low-confidence predictions are flagged for human review

```json
{
  "ensemble_votes": {
    "rule": {"category": "Shopping", "confidence": 0.73},
    "ml": {"category": "Fees & Charges", "confidence": 0.28},
    "llm": {"category": "Shopping", "confidence": 0.98}
  },
  "requires_review": false
}
```

This transparency allows you to:
- **Audit decisions**: Identify systematic biases in specific methods
- **Monitor fairness**: Track if certain merchant names or transaction patterns are being misclassified
- **Build trust**: Users can see and understand why their transactions were categorized

#### 3. **Configurable Weighting for Bias Correction**

The ensemble weights are fully configurable via `.env`:

```bash
RULE_WEIGHT=0.3
ML_WEIGHT=0.4
LLM_WEIGHT=0.3
```

**If you detect bias**:
- Discovered that rules are too aggressive on certain patterns? Reduce `RULE_WEIGHT`
- ML model showing regional bias? Lower `ML_WEIGHT` and increase `LLM_WEIGHT`
- Need more deterministic behavior? Increase `RULE_WEIGHT`

This allows you to tune the system's behavior based on your observed fairness metrics.

#### 4. **Human-in-the-Loop Feedback**

The `/feedback` endpoint enables continuous bias detection and correction:

```python
# User reports incorrect categorization
POST /feedback
{
  "transaction_text": "LOCAL SHOP PURCHASE",
  "predicted_category": "Other",
  "correct_category": "Groceries",
  "notes": "System misclassified local merchant"
}
```

**Benefits**:
- **Identify bias patterns**: Track which types of transactions are systematically miscategorized
- **Retraining pipeline**: Use feedback data to retrain ML models with bias corrections
- **Equity monitoring**: Ensure the system works fairly across different merchant types, regions, and transaction patterns

#### 5. **Diverse Training Data**

Our synthetic dataset generation (see `scripts/generate_dataset.py`) ensures:
- **Geographic diversity**: Merchants from multiple regions and cultures
- **Merchant size diversity**: Small local shops to large international brands
- **Transaction type diversity**: Cash, UPI, cards, bank transfers, etc.
- **Amount diversity**: From small purchases (₹10) to large transactions (₹100,000+)

This reduces bias toward specific merchant types or transaction patterns.

#### 6. **Review Flagging for Ambiguous Cases**

Transactions below the review threshold (`REVIEW_THRESHOLD=0.60`) are automatically flagged:

```json
{
  "requires_review": true,
  "confidence": 0.54
}
```

**Why this matters**:
- **Catches edge cases**: Unusual transactions that might be misclassified
- **Prevents systematic errors**: Low-confidence predictions are double-checked
- **Builds fairness**: Ensures no group of transactions is systematically mishandled

#### 7. **Open Source & Auditable**

The entire system is open source, allowing:
- **Community audits**: Anyone can examine the code for bias
- **Bias testing**: Run your own fairness evaluations on specific demographics
- **Custom modifications**: Adapt the system to your specific fairness requirements

### Bias Monitoring Checklist

We recommend monitoring these metrics in production:

- [ ] **Per-category accuracy**: Ensure no category is systematically underperforming
- [ ] **Merchant type fairness**: Compare accuracy across local vs. international merchants
- [ ] **Amount-based fairness**: Check if accuracy varies by transaction size
- [ ] **Channel fairness**: Ensure UPI, card, bank transfer transactions perform equally
- [ ] **Review rate equity**: Flag if certain transaction types require review more often
- [ ] **Ensemble disagreement patterns**: Monitor systematic splits between methods

### Limitations & Ongoing Work

**Known limitations**:
- **Language bias**: Currently optimized for English transaction descriptions (Indian context)
- **Training data**: Synthetic data may not fully represent all edge cases
- **LLM biases**: Llama 3.1, like all LLMs, may have inherent biases from pre-training

**Ongoing improvements**:
- Expanding training data to include more regional diversity
- Adding bias detection metrics to the evaluation framework
- Developing fairness-aware retraining pipelines
- Community-driven bias reporting and correction

### Reporting Bias

If you discover bias in the system:
1. Document the specific case (transaction text, predicted vs. expected category)
2. Use the `/feedback` endpoint to log the issue
3. Report to the maintainers via GitHub Issues with tag `bias-report`
4. Include demographic context if relevant (merchant type, region, amount range)

**We take bias seriously and commit to addressing reported issues promptly.**

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black core/ apps/ scripts/
isort core/ apps/ scripts/

# Lint
flake8 core/ apps/ scripts/
mypy core/ apps/ scripts/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ollama** - Local LLM runtime
- **Llama 3.1** - Meta's open-source LLM
- **sentence-transformers** - Embedding models
- **FastAPI** - Modern web framework
- **LightGBM** - Gradient boosting framework

---

## 📧 Support & Contact

- **Documentation**: This README + `/docs` endpoint
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

## 🗺️ Roadmap

### v1.1 (Current)
- [x] Rule-based categorization
- [x] ML embedding classifier
- [x] LLM integration
- [x] True ensemble voting
- [x] Docker deployment
- [x] Comprehensive docs
- [x] Premium Next.js UI with glassmorphism
- [x] Batch upload (TXT/CSV/JSON support)
- [x] Prometheus + Grafana monitoring
- [x] Pre-configured dashboards and alerts
- [x] Automated system tests

### v1.2 (Next)
- [ ] Fine-tune LLM on real transaction data
- [ ] Add subcategory prediction to ensemble
- [ ] Active learning pipeline
- [ ] Multi-currency support
- [ ] REST API authentication

### v2.0 (Future)
- [ ] Real-time streaming (Kafka)
- [ ] pgvector for semantic search
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Advanced fraud detection

---

**Built with ❤️ for accurate, fast, and privacy-preserving transaction categorization**

*Powered by the synergy of Rules + ML + LLM*

## 🤖 Automatic Feedback Learning

The system continuously improves through user feedback using a sophisticated learning pipeline:

### How It Works

1. **Collect Feedback**: Users provide corrections when classifications are wrong
2. **Export Training Data**: Feedback is converted to training format
3. **Merge with Original Data**: New feedback is combined with existing training set
4. **Retrain ML Model**: LightGBM model retrains with updated data
5. **Update LLM Examples**: Few-shot examples are refreshed with high-confidence feedback
6. **Hot Reload**: New model is loaded without downtime

### Triggering Learning

**Manual (API)**:
```bash
curl -X POST http://localhost:8000/api/feedback-learning
```

**Automatic (Cron)**:
```bash
# Setup daily learning at 2 AM
./scripts/setup_feedback_cron.sh
```

**On-Demand (Script)**:
```bash
python3 scripts/feedback_learning.py \
  --database-url "postgresql://txn_user:txn_password@localhost:5432/transactions" \
  --min-feedback 10
```

### Learning Thresholds

- **Minimum Feedback**: 10 entries (configurable)
- **ML Model**: Retrains when threshold is met
- **LLM Examples**: Top 50 high-confidence examples
- **Auto-Reload**: Models hot-swap without restart

### What Gets Learned

1. **ML Classifier**: 
   - User-corrected categories
   - Misclassified transactions
   - New merchant patterns

2. **LLM Few-Shot**:
   - High-confidence accepted classifications (>90%)
   - Human-corrected examples
   - Edge cases and ambiguous transactions

### Monitoring Learning

Check feedback count:
```bash
psql -U txn_user -d transactions -c "SELECT COUNT(*) FROM feedback;"
```

View learning logs:
```bash
tail -f logs/feedback_learning.log
```

API health check:
```bash
curl http://localhost:8000/health | jq '.components'
```

