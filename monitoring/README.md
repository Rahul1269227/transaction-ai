# Transaction AI - Monitoring Stack

Complete monitoring solution for Transaction AI using Prometheus, Grafana, and exporters.

## 🎯 Overview

This monitoring stack provides:

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization dashboards
- **Node Exporter** - System metrics (CPU, memory, disk)
- **cAdvisor** - Container metrics
- **Pre-configured Dashboards** - Ready-to-use visualizations
- **Alerting** - Alert rules for critical issues

## 🚀 Quick Start

### 1. Start the Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Check status
docker-compose -f docker-compose.monitoring.yml ps

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### 2. Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:4000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **cAdvisor** | http://localhost:8080 | - |
| **Node Exporter** | http://localhost:9100/metrics | - |

### 3. View the Enhanced Dashboard

1. Open Grafana: http://localhost:4000
2. Login with `admin` / `admin`
3. The enhanced dashboard will load automatically
4. Or navigate to: **Dashboards** → **Transaction AI - Production Dashboard**

## 📊 Available Dashboards

### 1. Transaction AI - Production Dashboard (Enhanced)

The main comprehensive dashboard with:

#### Overview Section
- **Requests/sec** - Real-time request rate
- **p50/p95 Latency** - Response time percentiles
- **Auto-Accept Rate** - Percentage of auto-accepted categorizations
- **Cache Hit Rate** - Redis cache performance
- **Total Requests (24h)** - Daily volume

#### Performance & Throughput
- **Request Rate by Endpoint** - Traffic breakdown
- **Latency Percentiles** - p50, p95, p99 over time

#### ML Model Performance
- **Method Usage Distribution** - MCC, Rules, ML, LLM usage
- **Method Distribution Pie Chart** - Visual breakdown
- **Category Distribution** - Top 10 categories

#### Confidence & Quality
- **Confidence Distribution** - Histogram of confidence scores
- **Review Required vs Auto-Accept** - Quality metrics

#### Cache & Database
- **Cache Hit/Miss Rate** - Redis performance
- **Database Query Performance** - PostgreSQL latency

#### System Resources
- **CPU Usage** - System CPU utilization
- **Memory Usage** - RAM utilization
- **Disk I/O** - Read/write throughput

#### Error Tracking
- **Error Rate by Type** - Error breakdown
- **Recent Errors Table** - Last 5 minutes

### 2. Transaction AI - Overview (Basic)

Original simplified dashboard for quick monitoring.

## 📈 Key Metrics

### Application Metrics

| Metric | Description | Type |
|--------|-------------|------|
| `categorization_requests_total` | Total categorization requests | Counter |
| `categorization_latency_seconds` | Request latency histogram | Histogram |
| `categorization_requires_review_total` | Requests requiring manual review | Counter |
| `categorization_cache_events_total` | Cache hits/misses | Counter |
| `method_usage_total` | Method usage (MCC, Rules, ML, LLM) | Counter |
| `categorization_category_total` | Categories assigned | Counter |
| `categorization_confidence` | Confidence score histogram | Histogram |
| `categorization_errors_total` | Errors by type | Counter |
| `db_query_duration_seconds` | Database query latency | Histogram |
| `ensemble_agreement_ratio` | Ensemble agreement percentage | Gauge |

### System Metrics (Node Exporter)

- CPU usage per core
- Memory usage (total, available, used)
- Disk I/O (read/write bytes)
- Network traffic
- Filesystem usage

### Container Metrics (cAdvisor)

- Container CPU usage
- Container memory usage
- Container network I/O
- Container filesystem usage

## 🔔 Alerts

Alert rules are defined in `alerts.yml`:

### Critical Alerts

- **High Latency** - p95 latency > 500ms for 5 minutes
- **High Error Rate** - Error rate > 5% for 5 minutes
- **Low Auto-Accept Rate** - Auto-accept < 70% for 10 minutes
- **High Memory Usage** - Memory > 90% for 5 minutes
- **High CPU Usage** - CPU > 90% for 5 minutes

### Warning Alerts

- **Increased Latency** - p95 latency > 300ms for 5 minutes
- **Cache Performance** - Cache hit rate < 25% for 10 minutes
- **Review Rate Increase** - Review rate > 30% for 10 minutes

## 🛠️ Configuration

### Prometheus Configuration

Edit `prometheus.yml` to customize:

```yaml
global:
  scrape_interval: 15s     # How often to scrape targets
  evaluation_interval: 15s # How often to evaluate rules

scrape_configs:
  - job_name: 'transaction-ai'
    static_configs:
      - targets: ['api:8000']  # Your API endpoint
```

### Grafana Configuration

Grafana is pre-configured with:

- Prometheus datasource
- Enhanced dashboard auto-loaded
- Pie chart plugin installed
- Admin user: `admin` / `admin` (change on first login)

### Alert Configuration

Edit `alerts.yml` to customize alert thresholds and conditions.

## 📦 Directory Structure

```
monitoring/
├── README.md                          # This file
├── prometheus.yml                     # Prometheus configuration
├── alerts.yml                         # Alert rules
├── grafana-dashboard.json            # Basic dashboard
├── grafana-dashboard-enhanced.json   # Enhanced dashboard
├── grafana-datasource.yml            # Legacy datasource config
└── grafana/
    └── provisioning/
        ├── dashboards/
        │   ├── dashboard.yml         # Dashboard provisioning
        │   └── transaction-ai-enhanced.json
        └── datasources/
            └── prometheus.yml        # Datasource provisioning
```

## 🔧 Customization

### Add Custom Metrics

1. **In your application**, export metrics:

```python
from prometheus_client import Counter, Histogram

# Define metric
custom_metric = Counter(
    'custom_operation_total',
    'Description of custom operation',
    ['label1', 'label2']
)

# Increment metric
custom_metric.labels(label1='value1', label2='value2').inc()
```

2. **In Prometheus**, verify it's scraped:
   - Go to http://localhost:9090/targets
   - Check your endpoint is UP
   - Query: `custom_operation_total`

3. **In Grafana**, add panel:
   - Click "Add Panel"
   - Query: `rate(custom_operation_total[5m])`
   - Save

### Create Custom Dashboard

1. In Grafana, click **+** → **Dashboard**
2. Add panels with your queries
3. Save dashboard
4. Export as JSON: **Share** → **Export** → **Save to file**
5. Copy to `monitoring/grafana/provisioning/dashboards/`

### Modify Alert Thresholds

Edit `alerts.yml`:

```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, sum(rate(categorization_latency_seconds_bucket[5m])) by (le)) > 0.5
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High latency detected"
```

Change `> 0.5` to your desired threshold.

## 📊 Dashboard Tips

### Time Ranges

Use the time picker (top-right) to view:
- **Last 5 minutes** - Real-time monitoring
- **Last 1 hour** - Recent trends
- **Last 6 hours** - Default view
- **Last 24 hours** - Daily patterns
- **Last 7 days** - Weekly analysis

### Refresh Intervals

Set auto-refresh (top-right):
- **5s** - Live monitoring
- **10s** - Default
- **1m** - Reduced load
- **Off** - Manual refresh

### Variables

Create dashboard variables for filtering:
1. Dashboard Settings → Variables → Add Variable
2. Example: `endpoint` variable to filter by endpoint
3. Query: `label_values(categorization_requests_total, endpoint)`

### Annotations

Mark deployments or events:
- Deployments are auto-annotated (blue lines)
- Add manual annotations: Graph → Add annotation

## 🐛 Troubleshooting

### Grafana shows "No Data"

1. Check Prometheus is running:
   ```bash
   curl http://localhost:9090/-/healthy
   ```

2. Check datasource connection in Grafana:
   - Configuration → Data Sources → Prometheus
   - Click "Test" button

3. Verify metrics are being scraped:
   - Open Prometheus: http://localhost:9090
   - Status → Targets
   - Check if `transaction-ai` target is UP

### Metrics not appearing

1. Check application is exposing metrics:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify Prometheus scrape config includes your endpoint

3. Check Prometheus logs:
   ```bash
   docker-compose -f docker-compose.monitoring.yml logs prometheus
   ```

### High memory usage

Reduce retention time in `docker-compose.monitoring.yml`:

```yaml
command:
  - '--storage.tsdb.retention.time=15d'  # Reduced from 30d
```

### Dashboard not loading

1. Check dashboard JSON is valid
2. Restart Grafana:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart grafana
   ```

## 🔐 Security

### Change Default Credentials

After first login, change the admin password:
1. Click profile icon → Preferences
2. Change Password

Or set via environment variable:

```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=your_secure_password
```

### Disable Anonymous Access

Already disabled with `GF_USERS_ALLOW_SIGN_UP=false`.

### Secure Prometheus

To add authentication to Prometheus, use a reverse proxy (nginx, Caddy).

## 📚 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Node Exporter Metrics](https://github.com/prometheus/node_exporter)
- [cAdvisor Documentation](https://github.com/google/cadvisor)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)

## 🎉 Next Steps

1. **Explore the Dashboard** - Familiarize yourself with all panels
2. **Set Up Alerts** - Configure alert notifications (email, Slack, PagerDuty)
3. **Create Custom Views** - Build dashboards for your specific needs
4. **Monitor Long-term** - Analyze trends over weeks/months
5. **Optimize** - Use metrics to identify performance bottlenecks

---

**Dashboard Port**: http://localhost:4000
**Default Credentials**: admin / admin (change on first login)
**Support**: See main project README
