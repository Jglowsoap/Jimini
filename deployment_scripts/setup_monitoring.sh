#!/bin/bash
# Jimini Enterprise Monitoring Setup Script

set -e

echo "📊 Setting up Jimini Enterprise Monitoring..."

# Install monitoring stack
echo "📦 Installing monitoring components..."
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Configure Grafana dashboards
echo "📈 Configuring Grafana dashboards..."
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana-dashboard.json

echo "✅ Monitoring Setup Complete!"
echo "📊 Grafana: http://localhost:3000 (admin/admin)"
echo "📊 Prometheus: http://localhost:9090"
