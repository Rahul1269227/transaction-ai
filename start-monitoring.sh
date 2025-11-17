#!/bin/bash

# Transaction AI - Monitoring Stack Startup Script
# This script starts Prometheus, Grafana, and related monitoring services

set -e

echo "🚀 Starting Transaction AI Monitoring Stack..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Enable Prometheus in .env if not already enabled
if [ -f .env ]; then
    if grep -q "PROMETHEUS_ENABLED=false" .env; then
        echo "📝 Enabling Prometheus in .env file..."
        sed -i.bak 's/PROMETHEUS_ENABLED=false/PROMETHEUS_ENABLED=true/g' .env
        echo "✅ Prometheus enabled"
    fi
else
    echo "⚠️  Warning: .env file not found. Creating from .env.example..."
    cp .env.example .env
    sed -i.bak 's/PROMETHEUS_ENABLED=false/PROMETHEUS_ENABLED=true/g' .env
fi

# Create monitoring directory if it doesn't exist
mkdir -p monitoring

# Start monitoring stack
echo ""
echo "🐳 Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check service health
echo ""
echo "🔍 Checking service status..."

SERVICES=("prometheus" "grafana" "node-exporter" "cadvisor")
ALL_HEALTHY=true

for service in "${SERVICES[@]}"; do
    CONTAINER_NAME="transaction-ai-$service"
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${GREEN}✅ $service is running${NC}"
    else
        echo -e "${YELLOW}⚠️  $service is not running${NC}"
        ALL_HEALTHY=false
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}🎉 Monitoring Stack Started Successfully!${NC}"
echo ""
echo "📊 Access your dashboards:"
echo ""
echo "  Grafana:        http://localhost:3001"
echo "    Username:     admin"
echo "    Password:     admin"
echo ""
echo "  Prometheus:     http://localhost:9090"
echo "  Node Exporter:  http://localhost:9100/metrics"
echo "  cAdvisor:       http://localhost:8080"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✅ All services are healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Some services may need a few more seconds to start.${NC}"
    echo "   Check status with: docker-compose -f docker-compose.monitoring.yml ps"
fi

echo ""
echo "💡 Tips:"
echo "  - View logs: docker-compose -f docker-compose.monitoring.yml logs -f"
echo "  - Stop stack: docker-compose -f docker-compose.monitoring.yml down"
echo "  - Read docs: cat MONITORING.md"
echo ""
echo "🔥 Don't forget to start your Transaction AI API with PROMETHEUS_ENABLED=true"
echo ""
