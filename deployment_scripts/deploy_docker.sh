#!/bin/bash
# Jimini Enterprise Docker Deployment Script

set -e

echo "🚀 Starting Jimini Enterprise Deployment..."

# Build Docker image
echo "📦 Building Docker image..."
docker build -t jimini-gateway:latest .

# Create network
echo "🌐 Creating Docker network..."
docker network create jimini-network || true

# Deploy with docker-compose
echo "🚀 Deploying with Docker Compose..."
docker-compose up -d

# Verify deployment
echo "✅ Verifying deployment..."
sleep 10
curl -f http://localhost:9000/health || { echo "❌ Health check failed"; exit 1; }

echo "✅ Jimini Enterprise Deployment Complete!"
echo "📊 Dashboard: http://localhost:5000"
echo "🔒 API: http://localhost:9000"
