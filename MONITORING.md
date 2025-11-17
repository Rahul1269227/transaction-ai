# Transaction AI - Monitoring & Observability Guide

## Overview

This system includes a comprehensive monitoring stack using **Prometheus** for metrics collection and **Grafana** for visualization. The monitoring solution provides real-time insights into system performance, ML model behavior, and infrastructure health.

## Architecture

```
┌─────────────────┐
│  Transaction AI │
│      API        │──────► Exposes /metrics endpoint
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Prometheus    │──────► Collects & stores metrics
└─────────────────┘
         │
         ▼
┌─────────────────┐
│    Grafana      │──────► Visualizes metrics
└─────────────────┘
```

## Quick Start

### 1. Enable Prometheus in API

Edit your `.env` file:
```bash
PROMETHEUS_ENABLED=true
```

### 2. Start Monitoring Stack

```bash
# Start Prometheus, Grafana, and exporters
docker-compose -f docker-compose.monitoring.yml up -d

# Check status
docker-compose -f docker-compose.monitoring.yml ps
```

### 3. Access Dashboards

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin` (change on first login)

- **Prometheus**: http://localhost:9090
  - Direct metrics query interface

- **Node Exporter**: http://localhost:9100/metrics
  - System-level metrics

- **cAdvisor**: http://localhost:8080
  - Container metrics

## Available Metrics

### Application Metrics

#### Request Metrics
```promql
# Total requests by endpoint
categorization_requests_total{endpoint="categorize"}

# Request rate (requests/sec)
rate(categorization_requests_total[5m])
```

#### Latency Metrics
```promql
# 95th percentile latency
histogram_quantile(0.95, sum(rate(categorization_latency_seconds_bucket[5m])) by (le))

# Average latency
histogram_quantile(0.50, sum(rate(categorization_latency_seconds_bucket[5m])) by (le))
```

#### ML Model Metrics
```promql
# Method usage distribution
sum(rate(method_usage_total[5m])) by (method)

# Review rate
categorization_requires_review_total / categorization_requests_total

# Ensemble agreement ratio
ensemble_agreement_ratio
```

#### Cache Metrics
```promql
# Cache hit rate
sum(rate(categorization_cache_events_total{result="hit"}[5m])) /
sum(rate(categorization_cache_events_total[5m]))

# Cache hits and misses
categorization_cache_events_total{result="hit"}
categorization_cache_events_total{result="miss"}
```

### Infrastructure Metrics

#### CPU Usage
```promql
# CPU usage percentage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

#### Memory Usage
```promql
# Memory usage percentage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

#### Disk Usage
```promql
# Disk space available percentage
(node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
```

## Grafana Dashboards

### Transaction AI Overview Dashboard

The pre-configured dashboard includes:

**Row 1: Request Metrics**
- Request Rate by Endpoint (graph)
- Response Latency Percentiles (p50, p95, p99)

**Row 2: Key Performance Indicators**
- Total Requests (24h)
- Average Latency (5m)
- Review Rate (%)
- Ensemble Agreement (%)

**Row 3: ML & Caching**
- Method Usage Distribution
- Cache Hit/Miss Rate

**Row 4: Infrastructure**
- CPU Usage
- Memory Usage

**Row 5: Detailed Tables**
- Recent Categorizations by Method

### Importing Custom Dashboards

1. Navigate to Grafana (http://localhost:3001)
2. Click **+** → **Import**
3. Upload `monitoring/grafana-dashboard.json`
4. Select **Prometheus** as data source
5. Click **Import**

## Alerts

### Configured Alerts

The system includes pre-configured alerts in `monitoring/alerts.yml`:

| Alert Name | Threshold | Severity | Description |
|------------|-----------|----------|-------------|
| **HighErrorRate** | >5% for 5m | Warning | Error rate exceeds 5% |
| **HighReviewRate** | >30% for 10m | Info | High manual review rate |
| **HighLatency** | >2s (p95) for 5m | Warning | API latency above 2 seconds |
| **APIDown** | API unavailable for 2m | Critical | API service is down |
| **LowEnsembleAgreement** | <60% for 15m | Warning | Low consensus among methods |
| **LowCacheHitRate** | <20% for 10m | Info | Cache not effective |
| **HighMemoryUsage** | >85% for 5m | Warning | Memory pressure |
| **HighCPUUsage** | >80% for 10m | Warning | CPU saturation |
| **LowDiskSpace** | <15% free for 5m | Critical | Disk space running out |

### Viewing Active Alerts

1. Open Prometheus: http://localhost:9090
2. Navigate to **Alerts** tab
3. View active alerts and their states

### Configuring Alert Notifications

Edit `monitoring/prometheus.yml` to add Alertmanager:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

Then deploy Alertmanager with notification channels (email, Slack, PagerDuty, etc.)

## Useful Queries

### Top 10 Slowest Requests
```promql
topk(10, histogram_quantile(0.95,
  sum(rate(categorization_latency_seconds_bucket[5m])) by (le, endpoint)
))
```

### Request Success Rate
```promql
sum(rate(categorization_requests_total[5m])) -
sum(rate(categorization_errors_total[5m])) /
sum(rate(categorization_requests_total[5m])) * 100
```

### Method Preference Distribution
```promql
sum by (method) (method_usage_total) /
sum(method_usage_total) * 100
```

### Cache Efficiency
```promql
sum(rate(categorization_cache_events_total{result="hit"}[10m])) /
sum(rate(categorization_cache_events_total[10m])) * 100
```

## Troubleshooting

### Prometheus Not Scraping Metrics

**Check API is exposing metrics:**
```bash
curl http://localhost:8000/metrics
```

**Verify Prometheus targets:**
1. Open http://localhost:9090/targets
2. Check if `transaction-ai-api` target is **UP**

**Common issues:**
- API not running
- `PROMETHEUS_ENABLED=false` in `.env`
- Network connectivity between containers

### Grafana Dashboard Not Showing Data

**Verify Prometheus datasource:**
1. Grafana → Configuration → Data Sources
2. Test **Prometheus** connection
3. Ensure URL is `http://prometheus:9090`

**Check metric availability:**
1. Open Prometheus → Graph
2. Run sample query: `up`
3. Verify metrics exist

### High Memory Usage

**Container resource limits:**
```bash
# Check container stats
docker stats transaction-ai-prometheus
docker stats transaction-ai-grafana

# Adjust retention in prometheus.yml
--storage.tsdb.retention.time=15d  # Reduce from 30d
```

## Production Recommendations

### Security

1. **Change default passwords:**
   ```bash
   # Grafana admin password
   docker exec -it transaction-ai-grafana grafana-cli admin reset-admin-password <new-password>
   ```

2. **Enable authentication on Prometheus:**
   Add basic auth using reverse proxy (nginx/traefik)

3. **Use HTTPS:**
   Deploy behind SSL termination

### Performance

1. **Adjust scrape intervals** based on load:
   ```yaml
   # prometheus.yml
   scrape_interval: 30s  # Reduce from 15s for high-scale
   ```

2. **Optimize retention:**
   ```yaml
   --storage.tsdb.retention.time=15d  # Adjust based on storage
   --storage.tsdb.retention.size=10GB  # Set max size
   ```

3. **Use recording rules** for complex queries:
   ```yaml
   # Create pre-computed metrics
   - record: job:api_request_rate:5m
     expr: sum(rate(categorization_requests_total[5m]))
   ```

### High Availability

1. **Prometheus HA:**
   - Deploy multiple Prometheus instances
   - Use remote storage (Thanos, Cortex, Mimir)

2. **Grafana HA:**
   - Use external database (PostgreSQL)
   - Deploy multiple Grafana instances behind load balancer

## Monitoring Checklist

- [ ] Enable Prometheus in `.env`
- [ ] Start monitoring stack with docker-compose
- [ ] Access Grafana and change default password
- [ ] Import dashboard from `monitoring/grafana-dashboard.json`
- [ ] Verify all targets are UP in Prometheus
- [ ] Configure alert notifications (optional)
- [ ] Set up backups for Grafana dashboards
- [ ] Review and adjust retention policies
- [ ] Test alerts by triggering conditions
- [ ] Document custom dashboards and queries

## Support & Resources

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **PromQL Guide**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Dashboard Examples**: https://grafana.com/grafana/dashboards/

## Maintenance

### Backup Grafana Dashboards

```bash
# Export dashboard
docker exec transaction-ai-grafana grafana-cli admin export-dashboards

# Backup Grafana data
docker cp transaction-ai-grafana:/var/lib/grafana ./backup/grafana-$(date +%Y%m%d)
```

### Backup Prometheus Data

```bash
# Create snapshot
docker exec transaction-ai-prometheus promtool tsdb snapshot /prometheus

# Copy snapshot
docker cp transaction-ai-prometheus:/prometheus/snapshots ./backup/
```

### Clean Old Data

```bash
# Prometheus auto-cleans based on retention
# Manual cleanup if needed:
docker exec transaction-ai-prometheus rm -rf /prometheus/wal
```

## Advanced Configuration

### Custom Metrics

Add custom metrics in your application:

```python
from prometheus_client import Counter, Histogram

# Custom counter
custom_counter = Counter('my_custom_metric', 'Description')
custom_counter.inc()

# Custom histogram
custom_histogram = Histogram('my_custom_duration', 'Description')
with custom_histogram.time():
    # Your code here
    pass
```

### Federation

Set up Prometheus federation for multi-cluster monitoring:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'federate'
    scrape_interval: 15s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="transaction-ai-api"}'
    static_configs:
      - targets:
        - 'prometheus-1:9090'
        - 'prometheus-2:9090'
```

---

**Last Updated:** 2024-01
**Version:** 1.0.0
