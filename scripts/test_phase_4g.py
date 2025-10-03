#!/usr/bin/env python3
"""
Phase 4G: Observability & Monitoring Validation
Tests monitoring endpoints, telemetry, and alert systems.
"""

import json
import requests
import time
from datetime import datetime


def test_health_endpoints():
    """Test health and monitoring endpoints"""
    base_url = "http://localhost:9000"
    
    print("🏥 Testing Health & Monitoring Endpoints")
    print("-" * 40)
    
    endpoints = [
        ("/health", "Basic health check"),
        ("/ready", "Readiness check with dependencies"),
        ("/v1/resilience", "Circuit breaker and resilience status"),
        ("/about", "Configuration disclosure"),
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint} ({response.status_code}): {description}")
                
                # Validate response structure
                if endpoint == "/health":
                    required_fields = ["status", "shadow_mode", "loaded_rules", "version"]
                elif endpoint == "/ready":
                    required_fields = ["ready", "loaded_rules", "resilience"]
                elif endpoint == "/v1/resilience":
                    required_fields = ["circuit_breakers", "dead_letter_queue"]
                elif endpoint == "/about":
                    required_fields = ["service", "version", "data_flows"]
                
                missing_fields = [f for f in required_fields if f not in data]
                if missing_fields:
                    print(f"   ⚠️ Missing fields: {missing_fields}")
                    results.append(False)
                else:
                    print(f"   ✅ All required fields present")
                    results.append(True)
            else:
                print(f"❌ {endpoint} ({response.status_code}): {response.text[:100]}")
                results.append(False)
                
        except requests.RequestException as e:
            print(f"❌ {endpoint}: Connection error - {e}")
            results.append(False)
    
    return all(results)


def test_metrics_endpoint():
    """Test metrics endpoint with authentication"""
    print("\n📊 Testing Metrics Endpoint")
    print("-" * 40)
    
    # This would normally require proper JWT token
    print("ℹ️ Metrics endpoint requires RBAC authentication")
    print("   Endpoint: GET /admin/metrics")
    print("   Required: JWT Bearer token with ADMIN role")
    print("   Response: Comprehensive metrics dump")
    
    # Test without auth - should get 403
    try:
        response = requests.get("http://localhost:9000/admin/metrics", timeout=5)
        if response.status_code == 403:
            print("✅ Properly protected - returns 403 without auth")
            return True
        else:
            print(f"⚠️ Expected 403, got {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def test_security_headers():
    """Test security headers in responses"""
    print("\n🛡️ Testing Security Headers")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:9000/health", timeout=5)
        
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Content-Security-Policy"
        ]
        
        present_headers = []
        missing_headers = []
        
        for header in security_headers:
            if header in response.headers:
                present_headers.append(header)
                print(f"✅ {header}: {response.headers[header]}")
            else:
                missing_headers.append(header)
                print(f"❌ Missing: {header}")
        
        success_rate = len(present_headers) / len(security_headers)
        print(f"\n📈 Security Headers: {len(present_headers)}/{len(security_headers)} present ({success_rate:.1%})")
        
        return success_rate >= 0.8  # 80% success rate
        
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def test_error_handling():
    """Test error handling and responses"""
    print("\n🚨 Testing Error Handling")
    print("-" * 40)
    
    test_cases = [
        ("Invalid JSON", {"invalid": "json", "missing": "required_fields"}),
        ("Missing API key", {"text": "test", "endpoint": "/test", "direction": "request"}),
        ("Invalid endpoint", None)  # Invalid request to trigger error
    ]
    
    results = []
    
    for description, payload in test_cases:
        try:
            if payload:
                response = requests.post("http://localhost:9000/v1/evaluate", 
                                       json=payload, timeout=5)
            else:
                response = requests.get("http://localhost:9000/nonexistent", timeout=5)
            
            # Should get proper error response
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    if "error" in error_data or "detail" in error_data:
                        print(f"✅ {description}: Proper error response ({response.status_code})")
                        results.append(True)
                    else:
                        print(f"⚠️ {description}: No error field in response")
                        results.append(False)
                except json.JSONDecodeError:
                    print(f"⚠️ {description}: Non-JSON error response")
                    results.append(False)
            else:
                print(f"❌ {description}: Expected error, got {response.status_code}")
                results.append(False)
                
        except requests.RequestException as e:
            print(f"❌ {description}: Connection error - {e}")
            results.append(False)
    
    return all(results)


def check_opentelemetry():
    """Check OpenTelemetry configuration"""
    print("\n📡 OpenTelemetry Integration")
    print("-" * 40)
    
    import os
    
    otel_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    if otel_endpoint:
        print(f"✅ OTEL endpoint configured: {otel_endpoint}")
        return True
    else:
        print("ℹ️ OTEL endpoint not configured (optional)")
        print("   Set OTEL_EXPORTER_OTLP_ENDPOINT to enable distributed tracing")
        return True  # Not required for this test


def main():
    """Run all Phase 4G observability tests"""
    print("🔍 Phase 4G: Observability & Monitoring Validation")
    print("=" * 60)
    print(f"Test Run: {datetime.now().isoformat()}")
    print()
    
    # Start a test server if needed
    print("🚀 Starting validation against local server...")
    print("   Ensure server is running: uvicorn app.main:app --port 9000")
    print()
    
    test_results = []
    
    # Run all tests
    test_results.append(test_health_endpoints())
    test_results.append(test_metrics_endpoint()) 
    test_results.append(test_security_headers())
    test_results.append(test_error_handling())
    test_results.append(check_opentelemetry())
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n{'='*60}")
    print(f"Phase 4G Observability Tests: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All observability and monitoring tests PASSED!")
        print("\nObservability features verified:")
        print("  • Health check endpoints responding correctly")
        print("  • Security headers implemented and working")
        print("  • Error handling providing structured responses")
        print("  • RBAC protection on admin endpoints")
        print("  • OpenTelemetry integration available")
        
        print(f"\n📊 Production Monitoring Checklist:")
        print("  ✅ Health endpoints for load balancer checks")
        print("  ✅ Readiness probe for Kubernetes deployment")
        print("  ✅ Resilience status for operational monitoring")
        print("  ✅ Configuration disclosure for compliance audits")
        print("  ✅ Structured error responses for debugging")
        
    else:
        print("❌ Some observability tests FAILED - review implementation")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)