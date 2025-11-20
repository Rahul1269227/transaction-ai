# Configuration Guide

This guide explains how to configure the Transaction AI system using environment variables.

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Start the services:**
   ```bash
   # With Docker
   cd infra && docker-compose up -d

   # Without Docker (local development)
   export MODEL_PATH=models/transaction_classifier
   python3 -m uvicorn apps.api.main:app --reload
   ```

## Configuration Sections

### Database Configuration

```env
# PostgreSQL connection
DATABASE_URL=postgresql://txn_user:txn_password@localhost:5432/transactions

# Individual components (used by Docker)
POSTGRES_DB=transactions
POSTGRES_USER=txn_user
POSTGRES_PASSWORD=txn_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

**Important:**
- For Docker: Use service names (`postgres`, `redis`) as hosts
- For local dev: Use `localhost` or `127.0.0.1`

### Redis Cache Configuration

```env
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=600  # seconds
```

**Cache TTL:**
- Development: 300-600 seconds (5-10 minutes)
- Production: 1800-3600 seconds (30-60 minutes)
- High-traffic: 300 seconds (5 minutes) for fresher results

### Application Paths

```env
TAXONOMY_PATH=data/taxonomy.yaml
GAZETTEER_PATH=data/gazetteer/merchant_aliases.csv
MODEL_PATH=models/transaction_classifier
FEW_SHOT_EXAMPLES_PATH=data/few_shot_examples.jsonl
```

**Available Models:**
- `models/transaction_classifier` (recommended) - Best overall performance
- `models/transaction_classifier` - Standard model
- Custom trained models in `models/` directory

### API Server Configuration

```env
API_HOST=0.0.0.0  # Listen on all interfaces
API_PORT=8000
API_RELOAD=true   # Auto-reload on code changes (dev only)
LOG_LEVEL=INFO    # DEBUG|INFO|WARNING|ERROR|CRITICAL
```

**Log Levels:**
- `DEBUG`: Verbose logging for troubleshooting
- `INFO`: Normal operation logs (recommended for dev)
- `WARNING`: Only warnings and errors (recommended for production)
- `ERROR`: Only errors
- `CRITICAL`: Only critical errors

### Confidence Thresholds

```env
AUTO_ACCEPT_THRESHOLD=0.85  # 85% confidence to auto-accept
REVIEW_THRESHOLD=0.60       # Below 60% requires review
```

**Tuning Guidelines:**
- **Conservative** (fewer errors, more reviews): `AUTO_ACCEPT=0.90`, `REVIEW=0.70`
- **Balanced** (recommended): `AUTO_ACCEPT=0.85`, `REVIEW=0.60`
- **Aggressive** (fewer reviews, more errors): `AUTO_ACCEPT=0.75`, `REVIEW=0.50`

### Ensemble Mode Configuration

```env
USE_ENSEMBLE=false           # Enable multi-model ensemble
FAST_MODE=false              # Skip LLM when Rule+ML agree
FAST_MODE_THRESHOLD=0.90     # Agreement threshold for fast mode
ENABLE_PARALLEL=true         # Parallel method execution
```

**Modes:**
1. **Hybrid Mode** (`USE_ENSEMBLE=false`) - Fast, Rules + ML only
   - Best for: High-throughput, cost-sensitive deployments
   - Latency: ~100-300ms
   - Accuracy: ~85-90%

2. **Ensemble Mode** (`USE_ENSEMBLE=true`) - Accurate, All methods
   - Best for: Maximum accuracy, complex transactions
   - Latency: ~500-2000ms (with LLM)
   - Accuracy: ~92-95%

3. **Fast Ensemble** (`USE_ENSEMBLE=true`, `FAST_MODE=true`) - Balanced
   - Best for: Production with good accuracy/speed balance
   - Latency: ~200-500ms (LLM only for edge cases)
   - Accuracy: ~90-93%

### Ensemble Weights

```env
MCC_WEIGHT=0.25   # Merchant Category Code (highly accurate)
RULE_WEIGHT=0.25  # Deterministic rules (fast & reliable)
ML_WEIGHT=0.30    # ML classifier (semantic understanding)
LLM_WEIGHT=0.20   # LLM reasoning (edge cases)
```

**Weight Tuning:**
- Weights should sum to 1.0
- Increase `RULE_WEIGHT` for more predictable results
- Increase `ML_WEIGHT` for better semantic matching
- Increase `LLM_WEIGHT` for better ambiguous transaction handling
- Increase `MCC_WEIGHT` if you have reliable MCC codes

### LLM Service Configuration

```env
LLM_URL=http://localhost:11434        # Ollama service URL
LLM_MODEL=llama3.1:8b                 # Model name
LLM_TIMEOUT=3.0                       # Request timeout (seconds)
```

**Supported LLM Backends:**

1. **Ollama** (default, local)
   ```env
   LLM_URL=http://localhost:11434
   LLM_MODEL=llama3.1:8b
   ```

2. **OpenAI** (cloud, requires API key)
   ```env
   LLM_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4
   OPENAI_API_KEY=sk-...
   ```

3. **Custom endpoint**
   ```env
   LLM_URL=http://your-llm-service:8080
   LLM_MODEL=your-model
   ```

**Model Recommendations:**
- **Fastest:** `llama3:8b`, `mistral:7b` (~500ms)
- **Balanced:** `llama3.1:8b`, `gemma:7b` (~1000ms)
- **Best Quality:** `llama3.1:70b`, `gpt-4` (~2000ms+)

### Monitoring Configuration

```env
PROMETHEUS_ENABLED=false  # Enable /metrics endpoint
METRICS_PORT=9090
```

**Monitoring Stack:**
- Prometheus: Metrics collection (`http://localhost:9090`)
- Grafana: Visualization (`http://localhost:3000`)

Enable with Docker profiles:
```bash
docker-compose --profile monitoring up -d
```

### Docker Configuration

```env
# Port mappings (host:container)
POSTGRES_EXTERNAL_PORT=5432
REDIS_EXTERNAL_PORT=6379
API_EXTERNAL_PORT=8000
LLM_EXTERNAL_PORT=11434
PROMETHEUS_EXTERNAL_PORT=9090
GRAFANA_EXTERNAL_PORT=3000

# Container names
POSTGRES_CONTAINER=txn-postgres
REDIS_CONTAINER=txn-redis
API_CONTAINER=txn-api
LLM_CONTAINER=txn-llm

# Network
NETWORK_NAME=txn-network
```

**Port Conflicts:**
If default ports are in use, change external ports:
```env
API_EXTERNAL_PORT=8080  # Map to different host port
POSTGRES_EXTERNAL_PORT=5433
REDIS_EXTERNAL_PORT=6380
```

## Environment-Specific Configurations

### Development

```env
# .env.development
LOG_LEVEL=DEBUG
API_RELOAD=true
USE_ENSEMBLE=false          # Faster responses
FAST_MODE=false
PROMETHEUS_ENABLED=true
CACHE_TTL=300               # 5 minutes
```

### Production

```env
# .env.production
LOG_LEVEL=WARNING
API_RELOAD=false
USE_ENSEMBLE=true
FAST_MODE=true              # Balance speed and accuracy
PROMETHEUS_ENABLED=true
CACHE_TTL=1800              # 30 minutes
AUTO_ACCEPT_THRESHOLD=0.90  # More conservative
```

### Testing

```env
# .env.test
LOG_LEVEL=INFO
API_RELOAD=false
USE_ENSEMBLE=false
DATABASE_URL=postgresql://txn_user:txn_password@localhost:5432/transactions_test
REDIS_URL=redis://localhost:6379/1  # Different DB
CACHE_TTL=60                # Short cache for testing
```

## Docker Usage

### Start All Services

```bash
cd infra
docker-compose up -d
```

### Start with LLM Model Download

```bash
docker-compose --profile llm-setup up -d
```

### Start with Monitoring

```bash
docker-compose --profile monitoring up -d
```

### Override Environment Variables

```bash
# Temporary override
LLM_MODEL=llama3:8b docker-compose up -d

# Or create .env.local
cp .env .env.local
# Edit .env.local
docker-compose --env-file .env.local up -d
```

### Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# With timestamps
docker-compose logs -f --timestamps api
```

## Troubleshooting

### Database Connection Failed

```bash
# Check if postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection string
echo $DATABASE_URL
```

### Redis Connection Failed

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### LLM Service Unavailable

```bash
# Check LLM service
docker-compose ps llm-service

# Download model manually
docker-compose exec llm-service ollama pull llama3.1:8b

# Test LLM
curl http://localhost:11434/api/tags
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
API_EXTERNAL_PORT=8080 docker-compose up -d
```

## Security Best Practices

1. **Never commit `.env` to git**
   - `.env` is in `.gitignore`
   - Only commit `.env.example`

2. **Use strong passwords in production**
   ```env
   POSTGRES_PASSWORD=$(openssl rand -hex 32)
   ```

3. **Restrict API access**
   ```env
   API_HOST=127.0.0.1  # Localhost only
   # Use nginx/traefik for external access
   ```

4. **Enable HTTPS in production**
   - Use reverse proxy (nginx, traefik)
   - Configure SSL certificates

5. **Rotate credentials regularly**
   - Database passwords
   - API keys
   - Admin passwords

## Performance Tuning

### High-Throughput Scenario

```env
USE_ENSEMBLE=false          # Skip LLM
ENABLE_PARALLEL=true
CACHE_TTL=1800              # Longer cache
POSTGRES_MAX_CONNECTIONS=100
REDIS_MAX_CONNECTIONS=50
```

### High-Accuracy Scenario

```env
USE_ENSEMBLE=true
FAST_MODE=false             # Always use LLM
LLM_TIMEOUT=5.0             # Allow more time
ML_WEIGHT=0.25              # Balance all methods
LLM_WEIGHT=0.30             # Higher LLM influence
```

### Low-Latency Scenario

```env
USE_ENSEMBLE=false
FAST_MODE=true
LLM_TIMEOUT=1.0             # Aggressive timeout
CACHE_TTL=3600              # Maximum caching
ENABLE_PARALLEL=true
```

## Additional Resources

- [Main README](../README.md) - Project overview
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/)
- [PostgreSQL Configuration](https://www.postgresql.org/docs/current/runtime-config.html)
- [Redis Configuration](https://redis.io/docs/management/config/)
