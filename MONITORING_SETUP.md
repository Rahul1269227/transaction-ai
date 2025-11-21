# Transaction AI - Monitoring Setup Guide

Complete guide to set up and use the monitoring stack for Transaction AI.

## 🎯 What You Get

A production-ready monitoring stack with:

✅ **Grafana Dashboard** - Beautiful visualizations
✅ **Prometheus** - Metrics storage and queries
✅ **Pre-configured Panels** - 27 panels across 7 sections
✅ **Alerts** - Critical and warning alerts
✅ **Auto-provisioning** - Dashboards load automatically

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Monitoring Stack

```bash
# Option A: Use the quick start script
./monitoring/start-monitoring.sh

# Option B: Use docker-compose directly
docker-compose -f docker-compose.monitoring.yml up -d
```

### Step 2: Access Grafana

Open your browser to: **http://localhost:4000**

- **Username**: `admin`
- **Password**: `admin` (change on first login)

### Step 3: View the Dashboard

The **Transaction AI - Production Dashboard** loads automatically!

## 📊 Dashboard Overview

The enhanced dashboard has **7 sections** with **27 panels**:

### 1. Overview - Key Metrics (6 panels)

Shows critical metrics at a glance:

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│ Requests/sec    │ p50 Latency     │ p95 Latency     │ Auto-Accept Rate│
│    12.5 req/s   │     45 ms       │    125 ms       │      87.2%      │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
┌─────────────────┬───────────────────────────────────────────────────────┐
│ Cache Hit Rate  │           Total Requests (24h)                       │
│     36.8%       │              125,430                                 │
└─────────────────┴───────────────────────────────────────────────────────┘
```

**What to watch**:
- 🟢 **Requests/sec** < 100 = Normal
- 🟢 **p95 Latency** < 200ms = Good
- 🟢 **Auto-Accept** > 85% = Target
- 🟢 **Cache Hit** > 30% = Expected

### 2. Performance & Throughput (2 panels)

Real-time performance graphs:

**Panel 1: Request Rate by Endpoint**
- Shows traffic distribution across endpoints
- `/categorize` vs `/health` vs `/batch`

**Panel 2: Latency Percentiles**
- p50, p95, p99 latency over time
- Color-coded: Green (p50), Yellow (p95), Red (p99)

### 3. ML Model Performance (3 panels)

ML method usage and distribution:

**Panel 1: Method Usage Distribution (Stacked Area)**
- MCC Lookup
- Rule-based
- ML Model
- LLM Fallback

**Panel 2: Method Distribution (Pie Chart)**
- Visual breakdown of method usage
- Shows which method is used most

**Panel 3: Category Distribution (Bar Chart)**
- Top 10 categories by volume
- Identifies most common transaction types

### 4. Confidence & Quality Metrics (2 panels)

Categorization quality:

**Panel 1: Confidence Distribution**
- Histogram of confidence scores
- Most should be > 85%

**Panel 2: Review Required vs Auto-Accept**
- Stacked area showing manual vs automatic
- Target: 85%+ auto-accept

### 5. Cache & Database Performance (2 panels)

Backend performance:

**Panel 1: Cache Hit/Miss Rate**
- Redis cache performance
- Green bars = hits, Red bars = misses

**Panel 2: Database Query Performance**
- PostgreSQL query latency
- p50, p95, p99 response times

### 6. System Resources (3 panels)

Infrastructure health:

**Panel 1: CPU Usage**
- Total CPU utilization %
- Alert if > 90% for 5+ minutes

**Panel 2: Memory Usage**
- RAM utilization %
- Alert if > 90% for 5+ minutes

**Panel 3: Disk I/O**
- Read/write throughput
- Shows storage bottlenecks

### 7. Error Tracking & Alerts (2 panels)

Error monitoring:

**Panel 1: Error Rate by Type**
- Categorization errors
- Database errors
- Cache errors
- Model errors

**Panel 2: Recent Errors Table**
- Last 10 errors in past 5 minutes
- Shows error type and endpoint

## 🎨 Dashboard Features

### Time Ranges

Click the time picker (top-right) to select:

- **Last 5 minutes** - Live monitoring
- **Last 1 hour** - Recent activity
- **Last 6 hours** - Default view (recommended)
- **Last 24 hours** - Daily trends
- **Last 7 days** - Weekly patterns
- **Custom** - Pick specific date/time range

### Refresh Intervals

Auto-refresh options (top-right):

- **5s** - Live updates (high CPU)
- **10s** - Default (balanced)
- **30s** - Reduced load
- **1m** - Minimal load
- **Off** - Manual refresh only

### Panel Features

Every panel supports:

- **Zoom** - Click and drag to zoom
- **Legend** - Click to show/hide series
- **Full Screen** - Click title → View
- **Inspect** - View raw data
- **Export** - Download as CSV/JSON

### Annotations

- **Blue vertical lines** = Deployments
- Shows when your application restarted
- Useful for correlating issues with deploys

## 🔔 Alerts (Pre-configured)

### Critical Alerts 🔴

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| High Latency | p95 > 500ms | 5 min | Investigate bottleneck |
| High Error Rate | Errors > 5% | 5 min | Check logs |
| Low Auto-Accept | Auto-accept < 70% | 10 min | Review model quality |
| High Memory | Memory > 90% | 5 min | Scale up or restart |
| High CPU | CPU > 90% | 5 min | Scale horizontally |

### Warning Alerts 🟡

| Alert | Condition | Duration | Action |
|-------|-----------|----------|--------|
| Increased Latency | p95 > 300ms | 5 min | Monitor closely |
| Cache Performance | Cache hit < 25% | 10 min | Check Redis |
| Review Rate | Review > 30% | 10 min | Check data quality |

## 📈 Key Metrics Explained

### Application Metrics

| Metric | What it measures | Good value | Bad value |
|--------|------------------|------------|-----------|
| **Requests/sec** | API throughput | 10-100 | > 200 (overload) |
| **p50 Latency** | Median response time | < 100ms | > 200ms |
| **p95 Latency** | 95th percentile | < 200ms | > 500ms |
| **Auto-Accept Rate** | % not requiring review | > 85% | < 70% |
| **Cache Hit Rate** | Redis effectiveness | > 30% | < 20% |
| **Error Rate** | % of failed requests | < 1% | > 5% |

### System Metrics

| Metric | What it measures | Good value | Bad value |
|--------|------------------|------------|-----------|
| **CPU Usage** | Processor utilization | < 70% | > 90% |
| **Memory Usage** | RAM utilization | < 80% | > 95% |
| **Disk I/O** | Storage throughput | Steady | Spikes |

## 🛠️ Common Tasks

### View Live Traffic

1. Set time range to "Last 5 minutes"
2. Set refresh to "5s"
3. Watch the "Request Rate" panel

### Investigate Slow Requests

1. Check "Latency Percentiles" panel
2. If p99 is high, drill down:
   - Check "Method Usage" - which method is slow?
   - Check "Database Query Performance" - DB bottleneck?
   - Check "Cache Hit Rate" - cache missing?

### Monitor a Deployment

1. Deploy your application
2. Watch for blue annotation line (deployment marker)
3. Monitor "Request Rate" and "Error Rate"
4. Check "Latency Percentiles" for performance change

### Find Which Categories are Popular

1. Go to "Category Distribution" bar chart
2. Shows top 10 categories by volume
3. Click bar to filter by that category (if variables configured)

### Check System Health

1. Scroll to "System Resources" section
2. Check CPU, Memory, Disk I/O
3. All should be stable and < 80%

## 🐛 Troubleshooting

### "No Data" in Grafana

**Cause**: Prometheus not scraping metrics

**Fix**:
1. Check Prometheus: http://localhost:9090/targets
2. Ensure your API is running and exposing `/metrics`
3. Restart monitoring stack:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart
   ```

### Dashboard Not Loading

**Cause**: Provisioning issue

**Fix**:
```bash
# Restart Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana

# Check logs
docker-compose -f docker-compose.monitoring.yml logs grafana
```

### High Memory Usage (Grafana/Prometheus)

**Cause**: Too much data retention

**Fix**: Reduce retention in `docker-compose.monitoring.yml`:
```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=15d'  # Reduced from 30d
```

### Metrics Stopped Updating

**Cause**: Application not running or not exposing metrics

**Fix**:
```bash
# Check if API is running
curl http://localhost:8000/health

# Check if metrics endpoint exists
curl http://localhost:8000/metrics

# Restart your application
docker-compose restart api
```

## 🔐 Security Tips

### Change Default Password

On first login, Grafana will prompt you to change the password. Or do it manually:

1. Click profile icon (bottom-left)
2. Preferences → Change Password

### Disable External Access

If running in production, bind only to localhost:

```yaml
grafana:
  ports:
    - "127.0.0.1:4000:3000"  # Only accessible from localhost
```

### Use Strong Passwords

Set via environment variable:

```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=YourStrongPassword123!
```

## 📚 Advanced Usage

### Create Custom Panels

1. Click "Add panel" button
2. Write PromQL query (see examples below)
3. Configure visualization
4. Save

**Example Queries**:

```promql
# Request rate by status code
sum(rate(categorization_requests_total[5m])) by (status_code)

# Average confidence score
avg(categorization_confidence)

# Top 5 slowest endpoints
topk(5, histogram_quantile(0.95,
  sum(rate(categorization_latency_seconds_bucket[5m])) by (le, endpoint)
))

# Cache efficiency
sum(rate(categorization_cache_events_total{result="hit"}[5m])) /
sum(rate(categorization_cache_events_total[5m])) * 100
```

### Set Up Alerting

1. **Grafana Alerting** (Contacts):
   - Configuration → Alerting → Contact points
   - Add Email, Slack, PagerDuty, etc.

2. **Prometheus Alertmanager** (Advanced):
   - Add alertmanager service to docker-compose
   - Configure `alertmanager.yml`
   - Alerts auto-forward from Prometheus

### Export Dashboard

1. Dashboard settings (⚙️ icon)
2. JSON Model
3. Copy JSON
4. Save to `monitoring/grafana/provisioning/dashboards/`

## 🎓 Learning Resources

### PromQL (Prometheus Query Language)

- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Query Functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)

### Grafana

- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [Panel Documentation](https://grafana.com/docs/grafana/latest/panels-visualizations/)
- [Variables Guide](https://grafana.com/docs/grafana/latest/dashboards/variables/)

## ✅ Checklist

Before going to production:

- [ ] Monitoring stack is running
- [ ] Grafana password changed from default
- [ ] Dashboard loads without errors
- [ ] All panels show data
- [ ] Alerts are configured
- [ ] Alert notifications set up (email/Slack)
- [ ] Tested a deployment (annotation appears)
- [ ] Documented your custom metrics
- [ ] Team trained on using dashboard

## 🎉 You're All Set!

Your monitoring stack is ready! Open the dashboard and start exploring:

**→ http://localhost:4000**

For detailed documentation, see: `monitoring/README.md`

---

**Need Help?** Check the troubleshooting section or open an issue on GitHub.
