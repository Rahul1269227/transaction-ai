# Monitoring Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start Monitoring Stack
```bash
./start-monitoring.sh
```

Or manually:
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### Step 2: Enable Metrics in API

Edit `.env`:
```bash
PROMETHEUS_ENABLED=true
```

Restart your API:
```bash
# If running with docker
docker-compose restart api

# If running locally
python -m apps.api.main
```

### Step 3: Access Dashboards

Open in your browser:
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## 📊 What You Get

### Grafana Dashboard Includes:

✅ **Request Metrics**
- Total requests per second
- Request rate by endpoint
- Success/error rates

✅ **Performance Metrics**
- Latency percentiles (p50, p95, p99)
- Average response time
- Throughput trends

✅ **ML Model Insights**
- Method usage (Rule-based, ML, LLM)
- Ensemble agreement ratio
- Review rate percentage

✅ **Cache Performance**
- Hit/miss rates
- Cache efficiency
- Response time impact

✅ **Infrastructure**
- CPU usage
- Memory consumption
- Disk space
- Container metrics

### Prometheus Metrics Exposed:

```
# Request metrics
categorization_requests_total
categorization_latency_seconds

# ML metrics
method_usage_total
ensemble_agreement_ratio
categorization_requires_review_total

# Cache metrics
categorization_cache_events_total
```

## 🎯 Key Dashboards

### 1. Transaction AI Overview
Pre-configured dashboard showing:
- Real-time request rate
- Latency trends
- Method distribution
- System health

### 2. Alerts
9 pre-configured alerts for:
- High error rates
- High latency
- Low ensemble agreement
- Resource saturation
- Service downtime

## 🔧 Common Tasks

### View Logs
```bash
docker-compose -f docker-compose.monitoring.yml logs -f grafana
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

### Stop Monitoring
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose.monitoring.yml restart
```

### Check Service Status
```bash
docker-compose -f docker-compose.monitoring.yml ps
```

## 📈 Example Queries

### Top Categories by Volume
```promql
topk(10, sum by (category) (method_usage_total))
```

### Average Response Time (5m)
```promql
histogram_quantile(0.5, sum(rate(categorization_latency_seconds_bucket[5m])) by (le))
```

### Cache Hit Rate
```promql
sum(rate(categorization_cache_events_total{result="hit"}[5m])) /
sum(rate(categorization_cache_events_total[5m])) * 100
```

### Requests Per Minute
```promql
sum(rate(categorization_requests_total[1m])) * 60
```

## 🛠️ Troubleshooting

### No Data in Grafana?

1. **Check API is exposing metrics:**
   ```bash
   curl http://localhost:8000/metrics
   ```

2. **Verify Prometheus is scraping:**
   - Open http://localhost:9090/targets
   - Look for `transaction-ai-api` - should be **UP**

3. **Check API environment:**
   ```bash
   grep PROMETHEUS_ENABLED .env
   # Should show: PROMETHEUS_ENABLED=true
   ```

### Services Not Starting?

```bash
# Check logs
docker-compose -f docker-compose.monitoring.yml logs

# Restart problematic service
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### Can't Access Dashboards?

```bash
# Check if ports are already in use
lsof -i :3001  # Grafana
lsof -i :9090  # Prometheus

# Verify containers are running
docker ps | grep transaction-ai
```

## 📚 Full Documentation

For comprehensive details, see [MONITORING.md](./MONITORING.md)

## 🎓 Learn More

- Query metrics in Prometheus: http://localhost:9090/graph
- Explore pre-built dashboards: https://grafana.com/grafana/dashboards/
- PromQL tutorial: https://prometheus.io/docs/prometheus/latest/querying/basics/

---

**Quick Links:**
- [Full Monitoring Guide](./MONITORING.md)
- [API Documentation](./README.md)
- [Configuration Guide](.env.example)
