#!/usr/bin/env python3
"""
Debug the API response to understand the error
"""

import asyncio
import json
from pathlib import Path
import tempfile
import os


def debug_api_response():
    """Debug API response format"""
    
    print("🔍 Debugging API Response Format")
    print("=" * 50)
    
    # Set up a temporary audit log for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_audit_log = Path(temp_dir) / "debug_audit.jsonl"
        
        # Set environment variable for audit log
        os.environ['AUDIT_LOG_PATH'] = str(test_audit_log)
        
        # Import the server after setting the environment
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test single request
        test_request = {
            "text": "This is safe content",
            "api_key": "changeme", 
            "agent_id": "debug-client",
            "endpoint": "/test/api",
            "direction": "inbound"
        }
        
        print(f"Making request: {test_request}")
        
        response = client.post("/v1/evaluate", json=test_request)
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"Response JSON: {response.json()}")
        else:
            print(f"Response text: {response.text}")


if __name__ == "__main__":
    debug_api_response()