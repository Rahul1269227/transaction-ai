#!/bin/bash

# Transaction AI - Monitoring Stack Startup Script
# This script starts the complete monitoring stack

set -e

echo "🚀 Starting Transaction AI Monitoring Stack..."
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose.monitoring.yml exists
if [ ! -f "docker-compose.monitoring.yml" ]; then
    echo "❌ Error: docker-compose.monitoring.yml not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "📦 Pulling latest images..."
docker-compose -f docker-compose.monitoring.yml pull

echo ""
echo "🏗️  Starting services..."
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are running
echo ""
echo "✅ Service Status:"
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Monitoring Stack is Ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Access Points:"
echo "  • Grafana Dashboard:  http://localhost:4000"
echo "    Credentials:        admin / admin"
echo ""
echo "  • Prometheus:         http://localhost:9090"
echo "  • cAdvisor:           http://localhost:8080"
echo "  • Node Exporter:      http://localhost:9100/metrics"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Quick Tips:"
echo "  • Change admin password on first login"
echo "  • Enhanced dashboard loads automatically"
echo "  • View logs: docker-compose -f docker-compose.monitoring.yml logs -f"
echo "  • Stop stack: docker-compose -f docker-compose.monitoring.yml down"
echo ""
echo "📚 Full documentation: monitoring/README.md"
echo ""
