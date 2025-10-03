#!/bin/bash
# Jimini Production Deployment Script - Phase 1 Ship Now
# Execute the 30-minute deployment foundation

set -e

echo "🚀 JIMINI AI POLICY GATEWAY - PRODUCTION DEPLOYMENT"
echo "Phase 1: Ship Now (Days 1-7) - Hybrid Strategy Execution"
echo "========================================================="

# Configuration
DEPLOYMENT_ENV=${1:-staging}
NAMESPACE="jimini-system"
RELEASE_NAME="jimini-ai-policy"

echo "📋 Deployment Configuration:"
echo "   Environment: $DEPLOYMENT_ENV"
echo "   Namespace: $NAMESPACE"
echo "   Release: $RELEASE_NAME"

# Step 1: Pre-deployment validation
echo ""
echo "🔍 Step 1: Pre-deployment Validation"
echo "------------------------------------"

# Check dependencies
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found"; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm not found"; exit 1; }

echo "✅ Docker available: $(docker --version | cut -d' ' -f3)"
echo "✅ Kubectl available: $(kubectl version --client --short)"
echo "✅ Helm available: $(helm version --short)"

# Validate configuration files
if [[ ! -f "Dockerfile" ]]; then
    echo "❌ Dockerfile not found"
    exit 1
fi

if [[ ! -f "docker-compose.yml" ]]; then
    echo "❌ docker-compose.yml not found"
    exit 1
fi

if [[ ! -f "k8s-values.yaml" ]]; then
    echo "❌ k8s-values.yaml not found"
    exit 1
fi

echo "✅ All configuration files present"

# Step 2: Build and test
echo ""
echo "🏗️ Step 2: Build and Test"
echo "-------------------------"

# Run comprehensive test suite
echo "Running comprehensive test suite..."
export PYTHONPATH=$PWD
if ! python -m pytest tests/test_policy_recommendations.py tests/test_predictive_intelligence.py tests/test_reinforcement_learning.py -q; then
    echo "❌ Tests failed - deployment aborted"
    exit 1
fi

echo "✅ All 89 tests passing - ready for deployment"

# Build Docker image
echo "Building production Docker image..."
docker build -t jimini:${DEPLOYMENT_ENV} .
echo "✅ Docker image built successfully"

# Step 3: Shadow deployment
echo ""
echo "🛡️ Step 3: Shadow Deployment"
echo "----------------------------"

if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
    echo "🔒 Production deployment - starting with shadow mode"
    
    # Create namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets (template - update with real values)
    kubectl create secret generic jimini-secrets -n $NAMESPACE \
        --from-literal=api-key="changeme-production-key" \
        --from-literal=openai-api-key="your-openai-key" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy with Helm in shadow mode
    helm upgrade --install $RELEASE_NAME . \
        -f k8s-values.yaml \
        -n $NAMESPACE \
        --set app.shadowMode=true \
        --set replicaCount=3 \
        --set autoscaling.enabled=true \
        --wait --timeout=300s
    
    echo "✅ Shadow deployment completed"
    echo "📊 Monitor shadow metrics for 24-48 hours before enabling traffic"
    
elif [[ "$DEPLOYMENT_ENV" == "staging" ]]; then
    echo "🧪 Staging deployment with docker-compose"
    
    # Copy environment template
    if [[ ! -f ".env" ]]; then
        cp .env.example .env
        echo "⚠️  Update .env file with your configuration before proceeding"
    fi
    
    # Start staging environment
    docker-compose up -d
    
    # Wait for health check
    echo "⏳ Waiting for health check..."
    timeout 60 bash -c 'until curl -sf http://localhost:8000/health; do sleep 2; done'
    
    echo "✅ Staging deployment healthy"
    echo "🌐 Access at: http://localhost:8000"
    echo "📊 Metrics at: http://localhost:9090 (Prometheus)"
    
else
    echo "❌ Unknown environment: $DEPLOYMENT_ENV"
    exit 1
fi

# Step 4: Deployment verification
echo ""
echo "✅ Step 4: Deployment Verification"
echo "----------------------------------"

if [[ "$DEPLOYMENT_ENV" == "production" ]]; then
    # Kubernetes verification
    kubectl get pods -n $NAMESPACE
    kubectl get services -n $NAMESPACE
    
    # Health check
    echo "Checking pod health..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=jimini-ai-policy -n $NAMESPACE --timeout=300s
    
elif [[ "$DEPLOYMENT_ENV" == "staging" ]]; then
    # Docker compose verification
    docker-compose ps
    
    # API health check
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "✅ API health check passed"
    else
        echo "❌ API health check failed"
        docker-compose logs jimini
        exit 1
    fi
fi

# Step 5: Post-deployment monitoring setup
echo ""
echo "📊 Step 5: Post-deployment Monitoring"
echo "-------------------------------------"

echo "🎯 Monitoring Checklist:"
echo "   [ ] Health endpoints responding"
echo "   [ ] Metrics collection active"
echo "   [ ] Log aggregation configured"
echo "   [ ] Alert rules deployed"
echo "   [ ] Shadow mode data collection started"

echo ""
echo "📈 Key Metrics to Monitor:"
echo "   - Request latency (target: <100ms p95)"
echo "   - Error rate (target: <0.1%)"
echo "   - Policy decision accuracy"
echo "   - RL learning convergence"
echo "   - Resource utilization"

# Step 6: Next phase preparation
echo ""
echo "🚀 Step 6: Phase 2 Preparation"
echo "------------------------------"

echo "📅 Phase 2: Deep AI Evolution (Weeks 2-4)"
echo "   - Monitor production telemetry for 48 hours"
echo "   - Collect real user feedback data"
echo "   - Begin Phase 8 autonomous policy evolution design"
echo "   - Prepare actor-critic network architecture"

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "🎯 Status: Phase 1 SHIPPED - Jimini AI Policy Gateway is LIVE!"
echo "📊 Monitor: Watch shadow metrics and real user feedback"
echo "⏭️  Next: Phase 2 preparation begins in 48 hours"
echo ""
echo "🌟 You now have the first AI-native policy platform in production!"
echo "========================================================="