#!/bin/bash
# filepath: /workspaces/Jimini/scripts/integration_test.sh
# Integration test script for Jimini

set -e

echo "Setting up environment..."
export JIMINI_API_KEY=test123
export JIMINI_RULES_PATH=packs/secrets/v1.yaml
export JIMINI_SHADOW=1
export AUDIT_LOG_PATH=logs/test_audit.jsonl

# Ensure logs directory exists
mkdir -p logs

echo "Starting server..."
uvicorn app.main:app --host 127.0.0.1 --port 9000 &
SERVER_PID=$!

# Make sure to kill server on script exit
trap "kill $SERVER_PID" EXIT

echo "Waiting for server to start..."
sleep 2

# Test health
echo -e "\n=== Health Check ==="
curl -s http://localhost:9000/health | jq

# Test evaluate with various payloads
echo -e "\n=== Testing Evaluate ==="

echo "1. Clean message (should pass):"
curl -s -X POST http://localhost:9000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"api_key": "test123", "content": "This is a clean message", "endpoint": "/test", "agent_id": "integration-test"}' | jq

echo "2. GitHub token (should detect):"
curl -s -X POST http://localhost:9000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"api_key": "test123", "content": "My GitHub token is ghp_1234567890abcdefghijklmnopqrstuvwxyz", "endpoint": "/test", "agent_id": "integration-test"}' | jq

# Check metrics
echo -e "\n=== Metrics ==="
curl -s http://localhost:9000/v1/metrics | jq

# Check SARIF output
echo -e "\n=== SARIF Export ==="
curl -s "http://localhost:9000/v1/audit/sarif?date_prefix=$(date +%F)" | head -20

# Verify audit chain
echo -e "\n=== Audit Chain Verification ==="
jimini verify-audit --path logs/test_audit.jsonl

echo -e "\n=== All tests completed successfully! ==="