#!/bin/bash
# Docker quick start script

set -e

echo "🐳 Transaction AI Categorization - Docker Quick Start"
echo "====================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose detected"

# Navigate to infra directory
cd infra

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking API health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API is healthy!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "✅ All services are up!"
echo ""
echo "📝 Service URLs:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "🧪 Test the API:"
echo "  curl -X POST http://localhost:8000/categorize \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"text\": \"UPI-ZOMATO\", \"amount\": 249}'"
echo ""
echo "📊 View logs:"
echo "  docker-compose logs -f api"
echo ""
echo "🛑 Stop services:"
echo "  docker-compose down"
echo ""
