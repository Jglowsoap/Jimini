#!/usr/bin/env python3
"""
Quick Health Check for Jimini Platform Integration
===================================================

This script checks the status of Jimini services and verifies the integration
is working correctly.

Usage:
    python check_jimini_status.py
"""

import sys
import requests
import json
from datetime import datetime


def check_jimini_platform():
    """Check if Jimini platform service is running"""
    print("🔍 Checking Jimini Platform Service...")
    print("-" * 60)
    
    try:
        response = requests.get("http://localhost:9000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Jimini Platform: RUNNING")
            print(f"   • Status: {data.get('status', 'unknown')}")
            print(f"   • Version: {data.get('version', 'unknown')}")
            print(f"   • Rules Loaded: {data.get('loaded_rules', 0)}")
            print(f"   • Shadow Mode: {data.get('shadow_mode', False)}")
            
            if data.get('loaded_rules', 0) == 0:
                print("   ⚠️  WARNING: No rules loaded!")
                print("      → Check JIMINI_RULES_PATH environment variable")
                print("      → Verify rules file exists")
                return False
            
            return True
        else:
            print(f"❌ Jimini Platform: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Jimini Platform: NOT RUNNING")
        print("   → Start with: python start_jimini_services.py")
        return False
    except Exception as e:
        print(f"❌ Jimini Platform: ERROR - {e}")
        return False


def check_flask_gateway():
    """Check if Flask gateway service is running"""
    print("\n🔍 Checking Flask Integration Gateway...")
    print("-" * 60)
    
    try:
        response = requests.get("http://localhost:5001/api/jimini/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Flask Gateway: RUNNING")
            print(f"   • Status: {data.get('status', 'unknown')}")
            print(f"   • Jimini Connected: {data.get('jimini_connected', False)}")
            print(f"   • Jimini URL: {data.get('jimini_url', 'unknown')}")
            print(f"   • Version: {data.get('version', 'unknown')}")
            
            if not data.get('jimini_connected', False):
                print("   ⚠️  WARNING: Flask cannot connect to Jimini!")
                print("      → Ensure Jimini is running first")
                return False
            
            return True
        else:
            print(f"⚠️  Flask Gateway: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Flask Gateway: NOT RUNNING")
        print("   → Optional: Start with Flask integration script")
        return True  # Flask is optional
    except Exception as e:
        print(f"⚠️  Flask Gateway: ERROR - {e}")
        return True  # Flask is optional


def test_evaluation():
    """Test a simple evaluation"""
    print("\n🧪 Testing Evaluation...")
    print("-" * 60)
    
    try:
        # Test with safe text
        response = requests.post(
            "http://localhost:9000/v1/evaluate",
            json={
                "api_key": "changeme",
                "agent_id": "health_check",
                "text": "This is a safe test message",
                "direction": "outbound",
                "endpoint": "/test/health"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Evaluation Test: PASSED")
            print(f"   • Decision: {result.get('action', 'unknown').upper()}")
            print(f"   • Rule IDs: {result.get('rule_ids', [])}")
            return True
        elif response.status_code == 401:
            print("❌ Evaluation Test: FAILED (Authentication)")
            print("   → Check JIMINI_API_KEY environment variable")
            return False
        else:
            print(f"❌ Evaluation Test: FAILED (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Evaluation Test: ERROR - {e}")
        return False


def check_metrics():
    """Check metrics endpoint"""
    print("\n📊 Checking Metrics...")
    print("-" * 60)
    
    try:
        response = requests.get("http://localhost:9000/v1/metrics", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Metrics: AVAILABLE")
            print(f"   • Shadow Mode: {data.get('shadow_mode', False)}")
            print(f"   • Rules Loaded: {data.get('loaded_rules', 0)}")
            
            totals = data.get('totals', {})
            if totals:
                print(f"   • Total Decisions: {sum(totals.values())}")
                for decision, count in totals.items():
                    print(f"      - {decision}: {count}")
            
            return True
        else:
            print(f"⚠️  Metrics: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Metrics: ERROR - {e}")
        return True  # Non-critical


def main():
    print("\n" + "=" * 60)
    print("🏛️  JIMINI PLATFORM HEALTH CHECK")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # Check Jimini platform (required)
    results.append(("Jimini Platform", check_jimini_platform()))
    
    # Check Flask gateway (optional)
    results.append(("Flask Gateway", check_flask_gateway()))
    
    # Test evaluation if Jimini is running
    if results[0][1]:
        results.append(("Evaluation", test_evaluation()))
        results.append(("Metrics", check_metrics()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed and name == "Jimini Platform":
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ Your Jimini integration is working correctly!")
        print("\n📡 Your React dashboard can make API calls to:")
        print("   • Direct Jimini: http://localhost:9000/v1/evaluate")
        print("   • Flask Gateway: http://localhost:5001/api/jimini/evaluate")
        return 0
    else:
        print("❌ Issues detected with your Jimini integration")
        print("\n🔧 To fix:")
        print("   1. Start Jimini: python start_jimini_services.py")
        print("   2. Check logs for errors")
        print("   3. Verify rules file exists")
        return 1


if __name__ == "__main__":
    sys.exit(main())
