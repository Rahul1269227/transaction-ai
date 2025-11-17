#!/bin/bash

# Transaction AI - System Integration Test Script
# Tests API endpoints, batch processing, and monitoring stack

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=$4

    echo -n "Testing $name... "

    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST -H "Content-Type: application/json" -d "$data" "$url" -w "\n%{http_code}")
    else
        response=$(curl -s "$url" -w "\n%{http_code}")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🧪 Transaction AI - System Tests${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# API TESTS
# ============================================================================
echo -e "${BLUE}📡 API Endpoint Tests${NC}"
echo ""

# Test 1: Health check
test_endpoint "Health Check" "$API_URL/health"

# Test 2: Root endpoint
test_endpoint "Root Endpoint" "$API_URL/"

# Test 3: Single categorization
SINGLE_DATA='{"text": "STARBUCKS COFFEE #12345", "amount": 12.50}'
test_endpoint "Single Categorization" "$API_URL/categorize" "POST" "$SINGLE_DATA"

# Test 4: Batch categorization (new endpoint)
BATCH_DATA='{"transactions": ["STARBUCKS COFFEE", "NETFLIX SUBSCRIPTION", "UBER RIDE"]}'
test_endpoint "Batch Categorization" "$API_URL/api/batch-categorize" "POST" "$BATCH_DATA"

# Test 5: Stats endpoint
test_endpoint "Stats Endpoint" "$API_URL/api/stats"

echo ""

# ============================================================================
# MONITORING TESTS
# ============================================================================
echo -e "${BLUE}📊 Monitoring Stack Tests${NC}"
echo ""

# Test 6: Prometheus health
test_endpoint "Prometheus Health" "$PROMETHEUS_URL/-/healthy"

# Test 7: Prometheus metrics endpoint
test_endpoint "Prometheus Metrics" "$PROMETHEUS_URL/api/v1/query?query=up"

# Test 8: API metrics exposure
test_endpoint "API Metrics Endpoint" "$API_URL/metrics"

# Test 9: Grafana health
test_endpoint "Grafana Health" "$GRAFANA_URL/api/health"

# Test 10: Node Exporter
test_endpoint "Node Exporter" "http://localhost:9100/metrics"

echo ""

# ============================================================================
# DETAILED BATCH TEST
# ============================================================================
echo -e "${BLUE}🔬 Detailed Batch Processing Test${NC}"
echo ""

echo "Testing batch with 5 transactions..."
BATCH_TEST='{
  "transactions": [
    "STARBUCKS COFFEE #12345",
    "NETFLIX MONTHLY SUBSCRIPTION",
    "UBER RIDE TO AIRPORT",
    "AMAZON PURCHASE ELECTRONICS",
    "WALMART GROCERY SHOPPING"
  ]
}'

response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "$BATCH_TEST" "$API_URL/api/batch-categorize" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$response" ]; then
    echo -e "${GREEN}✓ Batch request successful${NC}"

    # Parse results
    total=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null || echo "0")
    successful=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('successful', 0))" 2>/dev/null || echo "0")
    failed=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('failed', 0))" 2>/dev/null || echo "0")

    echo "  Total: $total"
    echo "  Successful: $successful"
    echo "  Failed: $failed"

    if [ "$successful" -gt 0 ]; then
        echo -e "${GREEN}✓ Batch processing working correctly${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ No successful categorizations${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}✗ Batch request failed${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

# ============================================================================
# PROMETHEUS METRICS TEST
# ============================================================================
echo -e "${BLUE}📈 Prometheus Metrics Test${NC}"
echo ""

echo "Checking if API metrics are being collected..."
METRICS_QUERY="categorization_requests_total"
metrics_response=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$METRICS_QUERY" 2>/dev/null)

if echo "$metrics_response" | grep -q "success"; then
    echo -e "${GREEN}✓ Metrics are being collected${NC}"
    PASSED=$((PASSED + 1))

    # Show sample metrics
    echo ""
    echo "Sample metrics from Prometheus:"
    echo "$metrics_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('status') == 'success':
        results = data.get('data', {}).get('result', [])
        for r in results[:3]:
            metric = r.get('metric', {})
            value = r.get('value', [None, None])[1]
            print(f\"  - {metric.get('endpoint', 'unknown')}: {value}\")
except:
    pass
" 2>/dev/null || echo "  (Could not parse metrics)"
else
    echo -e "${RED}✗ Metrics collection not working${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

# ============================================================================
# FILE FORMAT TESTS
# ============================================================================
echo -e "${BLUE}📁 Batch File Format Tests${NC}"
echo ""

# Test JSON file
if [ -f "test_batch.json" ]; then
    echo -n "Testing JSON batch file... "
    json_content=$(cat test_batch.json)
    response=$(curl -s -X POST -H "Content-Type: application/json" \
      --data-binary "@test_batch.json" "$API_URL/api/batch-categorize" 2>/dev/null)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ JSON format working${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ JSON format failed${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠ test_batch.json not found, skipping${NC}"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📊 Test Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "✅ API endpoints working"
    echo "✅ Batch processing functional"
    echo "✅ Monitoring stack operational"
    echo "✅ Metrics being collected"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please check:"
    echo "  - Is the API running? (python -m apps.api.main)"
    echo "  - Is PROMETHEUS_ENABLED=true in .env?"
    echo "  - Is monitoring stack running? (./start-monitoring.sh)"
    echo ""
    exit 1
fi
