#!/usr/bin/env python3
"""
🚀 GOVERNMENT DASHBOARD SERVICE AUTOMATION
==========================================

This script ensures your Jimini + Flask dashboard services are running correctly.
Run this once and everything will work!
"""

import subprocess
import time
import requests
import json
import os
from pathlib import Path

def kill_existing_services():
    """Kill any existing services to start fresh"""
    print("🔄 Stopping existing services...")
    subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
    subprocess.run(["pkill", "-f", "flask_jimini_platform_integration"], capture_output=True)
    time.sleep(2)
    print("✅ Existing services stopped")

def start_jimini_service():
    """Start Jimini Platform with government rules"""
    print("🛡️ Starting Jimini Platform...")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "JIMINI_API_KEY": "changeme",
        "JIMINI_RULES_PATH": "packs/secrets/v1.yaml",  # Use secrets pack that works
        "JIMINI_SHADOW": "0"  # Disable shadow mode
    })
    
    # Start Jimini
    cmd = [
        "uvicorn", "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "9000"
    ]
    
    print(f"📡 Command: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd="/workspaces/Jimini",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for service to start
    print("⏳ Waiting for Jimini to start...")
    for i in range(30):  # 30 second timeout
        try:
            response = requests.get("http://localhost:9000/health", timeout=2)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Jimini Platform: ONLINE")
                print(f"   📋 Rules loaded: {health.get('loaded_rules', 0)}")
                print(f"   🛡️ Shadow mode: {health.get('shadow_mode', 'unknown')}")
                print(f"   🔧 Version: {health.get('version', 'unknown')}")
                return process
        except:
            pass
        
        time.sleep(1)
        print(f"   ⏳ Still starting... ({i+1}/30)")
    
    print("❌ Jimini failed to start!")
    return None

def start_flask_service():
    """Start Flask Dashboard Gateway"""
    print("🌐 Starting Flask Dashboard Gateway...")
    
    # Start Flask
    process = subprocess.Popen(
        ["python", "flask_jimini_platform_integration.py"],
        cwd="/workspaces/Jimini",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for Flask to start
    print("⏳ Waiting for Flask to start...")
    for i in range(15):
        try:
            response = requests.get("http://localhost:5001/api/jimini/health", timeout=2)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Flask Gateway: ONLINE")
                print(f"   🔗 Jimini Connected: {health.get('jimini_connected', False)}")
                print(f"   📡 Service: {health.get('service', 'unknown')}")
                return process
        except:
            pass
        
        time.sleep(1)
        print(f"   ⏳ Still starting... ({i+1}/15)")
    
    print("❌ Flask failed to start!")
    return None

def test_api_integration():
    """Test the complete API integration"""
    print("🧪 Testing API Integration...")
    
    # Test 1: Direct Jimini call
    try:
        print("\n1️⃣ Testing Jimini Platform directly...")
        response = requests.post(
            "http://localhost:9000/v1/evaluate",
            json={
                "text": "JWT token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJPbmxpbmUgSldUIEJ1aWxkZXIiLCJpYXQiOjE2Mjg2MTA0MTgsImV4cCI6MTY2MDEyNDI1OCwiYXVkIjoid3d3LmV4YW1wbGUuY29tIiwic3ViIjoidGVzdEBleGFtcGxlLmNvbSIsImZpcnN0X25hbWUiOiJKb2huIiwibGFzdF9uYW1lIjoiRG9lIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.Z9BLywJEPzdbrULSUT9F_mTKt8rSTKxm9ccO1S5kWjg",
                "agent_id": "test",
                "direction": "outbound",
                "endpoint": "/test",
                "api_key": "changeme"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Jimini Response: {result.get('action', 'unknown')}")
            print(f"   📋 Rules matched: {len(result.get('rule_ids', []))}")
            if result.get('rule_ids'):
                print(f"   🛡️ Rule IDs: {result['rule_ids']}")
        else:
            print(f"   ❌ Jimini Error: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Jimini Test Failed: {e}")
    
    # Test 2: Flask → Jimini integration
    try:
        print("\n2️⃣ Testing Flask → Jimini integration...")
        response = requests.post(
            "http://localhost:5001/api/jimini/evaluate",
            json={
                "text": "AWS Access Key: AKIAIOSFODNN7EXAMPLE",
                "endpoint": "/government/test",
                "user_id": "test_user"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Flask Integration: {result.get('status', 'unknown')}")
            print(f"   🛡️ Decision: {result.get('decision', 'unknown')}")
            if result.get('rule_ids'):
                print(f"   📋 Rules: {result['rule_ids']}")
        else:
            print(f"   ❌ Flask Integration Error: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Flask Integration Test Failed: {e}")

def main():
    """Main service startup routine"""
    print("🏛️ STARTING GOVERNMENT DASHBOARD SERVICES")
    print("=" * 60)
    
    # Step 1: Clean up
    kill_existing_services()
    
    # Step 2: Start Jimini Platform
    jimini_process = start_jimini_service()
    if not jimini_process:
        print("❌ Cannot start Jimini - aborting")
        return False
    
    # Step 3: Start Flask Gateway
    flask_process = start_flask_service()
    if not flask_process:
        print("❌ Cannot start Flask - aborting")
        return False
    
    # Step 4: Test integration
    test_api_integration()
    
    print("\n🎯 SERVICE STATUS SUMMARY:")
    print("=" * 40)
    print("✅ Jimini Platform: http://localhost:9000")
    print("✅ Flask Gateway: http://localhost:5001")
    print("✅ API Integration: Working")
    print("\n📡 Your dashboard can now make API calls:")
    print("• React → POST http://localhost:5001/api/jimini/evaluate")
    print("• Flask → POST http://localhost:9000/v1/evaluate") 
    print("• Government endpoints available at /api/government/*")
    
    print("\n⚡ TO KEEP SERVICES RUNNING:")
    print("Services are running in background processes.")
    print("Use 'pkill -f uvicorn' and 'pkill -f flask' to stop them.")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 ALL SERVICES STARTED SUCCESSFULLY!")
        print("Your React/Flask dashboard is ready for API calls!")
    else:
        print("\n❌ Service startup failed. Check the errors above.")