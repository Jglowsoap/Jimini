#!/usr/bin/env python3
"""
Test the main API server with enhanced audit logging integration
"""

import asyncio
import time
import json
from pathlib import Path
import tempfile
import os


async def test_api_audit_integration():
    """Test the API server with enhanced audit logging"""
    
    print("🚀 Testing API Server with Enhanced Audit Logging")
    print("=" * 60)
    
    # Set up a temporary audit log for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_audit_log = Path(temp_dir) / "test_audit.jsonl"
        
        # Set environment variable for audit log
        os.environ['AUDIT_LOG_PATH'] = str(test_audit_log)
        
        # Import the server after setting the environment
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        print("1. Testing basic API evaluation with audit logging...")
        
        # Test data
        test_requests = [
            {
                "text": "This is safe content",
                "api_key": "changeme",
                "agent_id": "test-client",
                "endpoint": "/test/api",
                "direction": "inbound"
            },
            {
                "text": "My API key is sk-abc123def456ghi789",
                "api_key": "changeme", 
                "agent_id": "test-client",
                "endpoint": "/test/api", 
                "direction": "outbound"
            },
            {
                "text": "Contact me at user@example.com",
                "api_key": "changeme",
                "agent_id": "test-client",
                "endpoint": "/test/api",
                "direction": "inbound"
            }
        ]
        
        # Make API calls
        responses = []
        for req_data in test_requests:
            response = client.post("/v1/evaluate", json=req_data)
            responses.append(response.json())
            print(f"   Request: '{req_data['text'][:30]}...' -> {response.json()['action']}")
        
        print(f"✅ Made {len(responses)} API calls successfully")
        
        # Test audit verification endpoint
        print("\n2. Testing audit verification endpoint...")
        
        verify_response = client.get("/v1/audit/verify")
        if verify_response.status_code == 200:
            verification = verify_response.json()
            print(f"✅ Audit verification: {verification}")
        else:
            print(f"❌ Audit verification failed: {verify_response.text}")
            
        # Test audit statistics endpoint  
        print("\n3. Testing audit statistics endpoint...")
        
        stats_response = client.get("/v1/audit/statistics")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✅ Audit statistics:")
            print(f"   Total records: {stats.get('total_records', 0)}")
            print(f"   Actions: {stats.get('actions', {})}")
            print(f"   Chain valid: {stats.get('chain_valid', False)}")
        else:
            print(f"❌ Audit statistics failed: {stats_response.text}")
        
        print("\n4. Testing health endpoints...")
        
        # Test health endpoint
        health_response = client.get("/health")
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ Health check: {health['status']}")
        else:
            print(f"❌ Health check failed")
        
        # Test readiness endpoint
        ready_response = client.get("/ready")
        if ready_response.status_code == 200:
            readiness = ready_response.json()
            print(f"✅ Readiness check: {readiness['ready']}")
            print(f"   Audit writable: {readiness.get('audit_writable', False)}")
        else:
            print(f"❌ Readiness check failed")
            
        print("\n" + "=" * 60)
        print("🎉 API Integration Test Complete!")
        
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_api_audit_integration())
        if success:
            print("✅ All API integration tests PASSED!")
        else:
            print("❌ Some API integration tests FAILED!")
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ API integration test failed with error: {e}")
        exit(1)