#!/bin/bash
# filepath: /workspaces/Jimini/scripts/docker_test.sh
# Test Jimini in Docker to verify container portability

set -e

echo "Building Jimini Docker image..."
docker build -t jimini:latest .

echo "Running container for testing..."
docker run -d --name jimini_test -p 9001:9000 jimini:latest

echo "Waiting for service to start..."
sleep 3

echo "Testing API..."
curl -s http://localhost:9001/health

echo -e "\nSending test request..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"api_key":"changeme","text":"test content","endpoint":"/test","direction":"inbound"}' \
  http://localhost:9001/v1/evaluate

echo -e "\n\nCleaning up container..."
docker stop jimini_test
docker rm jimini_test

echo "Docker test completed successfully!"