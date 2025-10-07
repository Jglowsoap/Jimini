#!/bin/bash
# Jimini Enterprise Kubernetes Deployment Script

set -e

echo "☸️ Starting Jimini Kubernetes Deployment..."

# Apply Kubernetes configurations
echo "📦 Applying Kubernetes configurations..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/jimini-gateway -n jimini

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -n jimini
kubectl get services -n jimini

echo "✅ Jimini Kubernetes Deployment Complete!"
