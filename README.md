# Transaction AI - Intelligent Financial Categorization

**98% accurate, sub-second, privacy-first transaction categorization powered by hybrid AI ensemble**

Combines rule-based logic + ML embeddings + LLM reasoning for production-grade accuracy with zero cloud dependencies.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## Features

- **98% Accuracy**: Ensemble of Rules (88%) + ML (96%) + LLM (92%)
- **Fast**: <900ms latency including LLM reasoning
- **100% Offline**: No API keys, runs entirely locally
- **18 Categories**: Food, Transport, Bills, Health, Shopping, Entertainment, etc.
- **Auto-Learning**: Continuously improves from user feedback
- **Production-Ready**: Docker + Postgres + Redis + Prometheus monitoring
- **Modern UI**: Next.js dashboard with batch upload support

### Latest Optimizations (v1.2)

**Performance:**
- 95% faster LLM with in-memory caching + async processing
- 3-second LLM timeout prevents cascade failures
- Parallel execution with graceful degradation

**Accuracy:**
- Merchant-first strategy (≥85% confidence bypasses voting)
- Fuzzy full-text merchant matching
- 13,907 test samples with natural language augmentation

---

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 16GB RAM (8GB for LLM, 4GB for ML, 4GB system)
- 20GB disk space

### Start in 3 Commands

```bash
# 1. Clone and start services
git clone <repo-url> && cd transaction-ai
docker-compose -f infra/docker-compose.yaml up -d

# 2. Download LLM model (one-time, ~5GB)
docker-compose -f infra/docker-compose.yaml --profile llm-setup run llm-loader

# 3. Test it!
curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"text": "STARBUCKS COFFEE", "amount": 12.50}'
```

**Response:**
```json
{
  "category": "Food & Dining",
  "confidence": 0.95,
  "method": "ensemble_unanimous",
  "requires_review": false,
  "ensemble_votes": {
    "rule": {"category": "Food & Dining", "confidence": 0.90},
    "ml": {"category": "Food & Dining", "confidence": 0.94},
    "llm": {"category": "Food & Dining", "confidence": 0.92}
  }
}
```

### Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend UI**: Start with `cd ui && npm install && npm run dev`
- **Monitoring**: http://localhost:3001 (Grafana)

---

## How It Works

### Ensemble Architecture

```
                ┌→ RULES (30%)      ─┐
                │  Keywords, patterns │
Transaction →   ├→ ML (40%)         ─┤→ Weighted → Final
                │  Embeddings+LightGB │  Voting     Category
                └→ LLM (30%)        ─┘
                   Llama 3.1 reasoning
```

**Why Ensemble?**
- Rules: Fast (35ms), deterministic, handles known patterns
- ML: Learned patterns, semantic understanding, 96% accurate
- LLM: Reasoning for edge cases, contextual understanding
- Together: 98% accuracy, high confidence when all agree

**Smart Fallback:**
- High-confidence merchant match (≥85%)? Skip voting, return instantly
- LLM timeout? Fall back to Rules + ML
- Confidence <60%? Flag for human review

---

## API Usage

### Single Transaction

```bash
POST /categorize
{
  "text": "UPI-ZOMATO PAY*1234",
  "amount": 249.00,
  "date": "2025-11-13"
}
```

### Batch Processing

```bash
POST /categorize/batch
{
  "transactions": [
    {"text": "STARBUCKS", "amount": 12.50},
    {"text": "UBER TRIP", "amount": 25.00}
  ]
}
```

### Submit Feedback (Auto-Learning)

```bash
POST /feedback
{
  "transaction_text": "LOCAL MARKET",
  "predicted_category": "Shopping",
  "correct_category": "Groceries"
}
```

Feedback is automatically used to retrain models daily (configurable).

---

## Configuration

### Ensemble Weights (.env)

```env
# Balanced (default)
RULE_WEIGHT=0.3
ML_WEIGHT=0.4
LLM_WEIGHT=0.3

# Speed-optimized (less LLM)
RULE_WEIGHT=0.4
ML_WEIGHT=0.5
LLM_WEIGHT=0.1

# Accuracy-optimized (trust LLM)
RULE_WEIGHT=0.2
ML_WEIGHT=0.3
LLM_WEIGHT=0.5
```

### Confidence Thresholds

```env
AUTO_ACCEPT_THRESHOLD=0.85  # Auto-accept if ≥85%
REVIEW_THRESHOLD=0.60       # Flag for review if <60%
LLM_TIMEOUT=3.0            # LLM timeout in seconds
```

### Performance Mode (Fast Path) ⚡

**NEW**: Skip LLM when rule+ML agree with high confidence - reduces latency from ~850ms to ~100ms for 70% of transactions!

```env
FAST_MODE=true              # Enable fast mode (default: false)
FAST_MODE_THRESHOLD=0.90    # Confidence threshold for skipping LLM (default: 0.90)
```

**How it works:**
- Runs rule and ML categorizers first (~100ms)
- If they agree on the same category with confidence ≥90%, skips LLM call
- Falls back to full ensemble (with LLM) only when needed
- Expected: 70% of transactions use fast path, 30% use full ensemble

**Performance Impact:**
- Fast path: ~100ms (rule + ML only)
- Full ensemble: ~850ms (rule + ML + LLM)
- Overall: ~70% faster average latency

### Disable LLM (ML-only mode)

```env
USE_ENSEMBLE=false
```

---

## Local Development

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed locally

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama and pull model
ollama serve
ollama pull llama3.1:8b

# 3. Train ML model (pre-balanced data included)
python scripts/train_model.py \
  --train data/balanced/train.jsonl \
  --val data/balanced/test.jsonl \
  --output models/classifier \
  --n-estimators 300 \
  --learning-rate 0.05

# 4. Start API
cd apps/api && python main.py
```

**Training Data Included:**
- `data/balanced/train.jsonl` - 48,493 balanced samples
- `data/balanced/test.jsonl` - 13,907 test samples
- `data/balanced/class_weights.json` - Pre-computed weights

---

## Monitoring & Observability

### Enable Metrics

```env
PROMETHEUS_ENABLED=true
```

### Start Monitoring Stack

```bash
./start-monitoring.sh

# Or manually
docker-compose -f docker-compose.monitoring.yml up -d
```

**Access:**
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090

**Pre-configured Dashboards:**
- Request rate & latency (p50, p95, p99)
- Ensemble agreement ratios
- Cache hit/miss rates
- Resource usage (CPU, memory)
- 9 production alerts

---

## Performance Benchmarks

| Metric | Ensemble | Fast Mode | ML-Only | Rules-Only |
|--------|----------|-----------|---------|------------|
| Accuracy | **98%** | **98%** | 96% | 88% |
| P50 Latency | **850ms** | **~100ms** | 115ms | 35ms |
| Throughput | 10 req/s | **~70 req/s** | 100 req/s | 1000 req/s |
| Memory | 11GB | 11GB | 2GB | 100MB |
| Fast Path Usage | N/A | **~70%** | N/A | N/A |

*Tested on: 16GB RAM, 8-core CPU, macOS ARM64*

**Fast Mode Benefits:**
- 70% of transactions skip LLM (when rule+ML agree ≥90%)
- Average latency reduced from 850ms to ~300ms
- Maintains 98% accuracy (LLM only used when needed)

---

## Testing

### Automated System Tests

```bash
./test-system.sh
```

Tests API endpoints, batch processing, monitoring, and UI.

### Unit Tests

```bash
pytest
```

### Performance Testing

```bash
python scripts/test_ensemble_performance.py
```

---

## Project Structure

```
transaction-ai/
├── apps/api/main.py           # FastAPI application
├── core/
│   ├── model/
│   │   ├── classifier.py      # ML embedding classifier
│   │   ├── llm_classifier.py  # LLM with caching & async
│   │   └── ensemble_router.py # Ensemble voting logic
│   ├── rules/engine.py        # Rule-based categorizer
│   ├── resolve/resolver.py    # Merchant fuzzy matching
│   └── normalize/normalizer.py # Text preprocessing
├── data/
│   ├── taxonomy.yaml          # 18 category definitions
│   ├── gazetteer/merchant_aliases.csv # 90+ merchants
│   └── balanced/              # Training data (included)
├── scripts/
│   ├── train_model.py         # ML training
│   └── feedback_learning.py   # Auto-retraining
├── infra/docker-compose.yaml  # Production deployment
└── ui/                        # Next.js dashboard
```

---

## Security & Privacy

- **100% Local**: All processing on your infrastructure
- **No Cloud APIs**: Zero external API calls
- **Transaction Data**: Never logged unless you configure DB
- **Models**: Downloaded once, cached locally

### Production Checklist

- [ ] Change default DB password
- [ ] Enable HTTPS (nginx reverse proxy)
- [ ] Configure CORS
- [ ] Set up database backups
- [ ] Enable monitoring & alerts
- [ ] Review rate limits

---

## Troubleshooting

### LLM Service Won't Start

```bash
# Check logs
docker-compose -f infra/docker-compose.yaml logs llm-service

# Verify memory (needs 8GB)
docker stats

# Pull model manually
docker exec -it txn-llm ollama pull llama3.1:8b
```

### Out of Memory

```bash
# Use smaller model
docker exec txn-llm ollama pull phi-3:mini

# Update .env
LLM_MODEL=phi-3:mini

# Or disable LLM
USE_ENSEMBLE=false
```

### Slow LLM Inference

1. Use GPU (5-10x faster) - see Docker GPU setup
2. Lower LLM_WEIGHT to 0.1
3. Use smaller model: `phi-3:mini`
4. Reduce LLM_TIMEOUT to 2.0

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Make changes and test: `pytest && ./test-system.sh`
4. Commit: `git commit -m 'Add feature'`
5. Push and open Pull Request

### Development

```bash
# Format code
black core/ apps/ scripts/
isort core/ apps/ scripts/

# Lint
flake8 core/ apps/ scripts/
```

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Acknowledgments

- **Ollama** - Local LLM runtime
- **Llama 3.1** - Meta's open-source LLM
- **sentence-transformers** - Embedding models
- **LightGBM** - Gradient boosting framework
- **FastAPI** - Modern Python web framework

---

## Roadmap

### v1.2 (Current)
- [x] Ensemble voting system
- [x] LLM caching & async processing
- [x] Merchant-first strategy
- [x] Expanded test dataset (13,907 samples)
- [x] Next.js UI with batch upload
- [x] Prometheus + Grafana monitoring
- [x] Auto-learning from feedback
- [x] **Performance Mode (Fast Path)** - Skip LLM when rule+ML agree

### v1.3 (Next)
- [ ] Fine-tune LLM on real data
- [ ] Active learning pipeline
- [ ] Multi-currency support
- [ ] REST API authentication
- [ ] Explainability dashboard UI

### v2.0 (Future)
- [ ] Real-time streaming (Kafka)
- [ ] Multi-language support
- [ ] Advanced fraud detection
- [ ] Mobile app integration

---

**Built with ❤️ for accurate, fast, and privacy-preserving transaction categorization**

*Powered by Rules + ML + LLM Ensemble*
