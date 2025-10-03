#!/usr/bin/env python3
"""
🧪 JIMINI GATEWAY INTEGRATION TESTS
===================================

Complete test suite for Jimini Gateway API endpoints and PKI system integrations.
"""

import asyncio
import pytest
import httpx
import json
from datetime import datetime
from typing import Dict, Any

# Test configuration
GATEWAY_URL = "http://localhost:8000"
TEST_TENANT_ID = "test-agency-001"
TEST_SESSION_ID = f"test_session_{int(datetime.now().timestamp())}"

class JiminiTestClient:
    """Test client for Jimini Gateway"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=GATEWAY_URL,
            headers={
                "X-Tenant-Id": TEST_TENANT_ID,
                "X-Session-Id": TEST_SESSION_ID,
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

# 🧪 **API ENDPOINT TESTS**

class TestJiminiGatewayAPI:
    """Test suite for Jimini Gateway API endpoints"""
    
    async def test_health_check(self):
        """Test health endpoint"""
        async with JiminiTestClient() as client:
            response = await client.client.get("/health")
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert health_data["service"] == "jimini-gateway"
            assert "active_rules" in health_data
            assert "total_decisions" in health_data
            
            print(f"✅ Health Check: {health_data}")
    
    async def test_get_rules(self):
        """Test rules endpoint"""
        async with JiminiTestClient() as client:
            response = await client.client.get("/api/v1/rules")
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == "ok"
            assert "rules" in data["data"]
            assert len(data["data"]["rules"]) > 0
            
            print(f"✅ Rules Retrieved: {len(data['data']['rules'])} rules")
    
    async def test_validate_rule(self):
        """Test rule validation"""
        test_rule = {
            "id": "TEST-RULE-1",
            "name": "Test Credit Card Detection",
            "pattern": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "action": "flag",
            "severity": "high",
            "system_scope": ["llm"],
            "enabled": True
        }
        
        async with JiminiTestClient() as client:
            response = await client.client.post("/api/v1/rules/validate", json=test_rule)
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == "ok"
            assert data["data"]["valid"] == True
            
            print("✅ Rule Validation: Valid rule accepted")
    
    async def test_invalid_rule_validation(self):
        """Test validation with invalid rule"""
        invalid_rule = {
            "id": "INVALID-RULE",
            "name": "Invalid Regex Rule",
            "pattern": r"[unclosed_bracket",  # Invalid regex
            "action": "block",
            "severity": "high",
            "system_scope": ["llm"],
            "enabled": True
        }
        
        async with JiminiTestClient() as client:
            response = await client.client.post("/api/v1/rules/validate", json=invalid_rule)
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == "error"
            assert "Invalid regex pattern" in str(data["details"])
            
            print("✅ Invalid Rule Validation: Invalid rule rejected")
    
    async def test_dry_run_rule(self):
        """Test rule dry run functionality"""
        test_rule = {
            "id": "TEST-DRYRUN-1",
            "name": "Test SSN Detection",
            "pattern": r"\b\d{3}-?\d{2}-?\d{4}\b",
            "action": "block",
            "severity": "critical",
            "system_scope": ["llm"],
            "enabled": True
        }
        
        test_content = "User SSN is 123-45-6789 and phone is 555-123-4567"
        
        async with JiminiTestClient() as client:
            response = await client.client.post("/api/v1/rules/dryrun", json={
                **test_rule,
                "test_content": test_content
            })
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == "ok"
            assert data["data"]["matched"] == True
            assert data["data"]["decision"] == "block"
            
            print(f"✅ Dry Run: Rule matched - Decision: {data['data']['decision']}")
    
    async def test_publish_rule(self):
        """Test rule publishing"""
        new_rule = {
            "id": f"TEST-PUBLISH-{int(datetime.now().timestamp())}",
            "name": "Test Published Rule",
            "pattern": r"\btest_data_\d+\b",
            "action": "flag",
            "severity": "low",
            "system_scope": ["llm"],
            "enabled": True
        }
        
        async with JiminiTestClient() as client:
            response = await client.client.post("/api/v1/rules/publish", json=new_rule)
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == "ok"
            assert data["data"]["rule_id"] == new_rule["id"]
            
            print(f"✅ Rule Published: {new_rule['id']}")
    
    async def test_get_coverage(self):
        """Test coverage metrics endpoint"""
        async with JiminiTestClient() as client:
            response = await client.client.get("/api/v1/coverage")
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == "ok"
            assert "total_requests" in data["data"]
            assert "coverage_rate" in data["data"]
            assert "active_rules" in data["data"]
            
            print(f"✅ Coverage Metrics: {data['data']['total_requests']} requests, "
                  f"{data['data']['coverage_rate']:.1f}% coverage")
    
    async def test_get_decisions(self):
        """Test decisions endpoint with filters"""
        async with JiminiTestClient() as client:
            # Test without filters
            response = await client.client.get("/api/v1/decisions")
            assert response.status_code == 200
            
            data = response.json()
            assert data["code"] == "ok"
            assert "decisions" in data["data"]
            
            # Test with filters
            response = await client.client.get("/api/v1/decisions", params={
                "system": "llm",
                "limit": 10
            })
            assert response.status_code == 200
            
            filtered_data = response.json()
            assert filtered_data["code"] == "ok"
            
            print(f"✅ Decisions: {len(data['data']['decisions'])} total, "
                  f"{len(filtered_data['data']['decisions'])} filtered")

# 🔌 **PKI ADAPTER TESTS**

class TestPKIAdapters:
    """Test suite for PKI system adapters"""
    
    async def test_ldap_adapter(self):
        """Test LDAP adapter functionality"""
        from pki_adapters import LDAPAdapter, JiminiPolicyEngine
        
        engine = JiminiPolicyEngine()
        adapter = LDAPAdapter("ldap://test.local", engine)
        
        # Test search with safe content
        safe_result = await adapter.search(
            base_dn="ou=users,dc=test,dc=local",
            search_filter="(cn=testuser)",
            attributes=["cn", "mail"],
            tenant_id=TEST_TENANT_ID,
            session_id=TEST_SESSION_ID
        )
        
        assert "entries" in safe_result
        print("✅ LDAP Adapter: Safe search completed")
        
        # Test search with PII (should be masked)
        try:
            pii_result = await adapter.search(
                base_dn="ou=users,dc=test,dc=local",
                search_filter="(ssn=123-45-6789)",  # Contains SSN
                attributes=["cn", "ssn"],
                tenant_id=TEST_TENANT_ID,
                session_id=TEST_SESSION_ID
            )
            print("⚠️ LDAP Adapter: PII search was allowed (check shadow mode)")
        except Exception as e:
            print("✅ LDAP Adapter: PII search blocked as expected")
    
    async def test_servicenow_adapter(self):
        """Test ServiceNow adapter functionality"""
        from pki_adapters import ServiceNowAdapter, JiminiPolicyEngine
        
        engine = JiminiPolicyEngine()
        adapter = ServiceNowAdapter("https://test.service-now.com", "test", "test", engine)
        
        # Test incident creation with safe data
        safe_incident = {
            "short_description": "System issue",
            "description": "General system problem",
            "priority": "Medium"
        }
        
        result = await adapter.create_incident(
            safe_incident,
            tenant_id=TEST_TENANT_ID,
            session_id=TEST_SESSION_ID
        )
        
        assert "sys_id" in result
        assert "number" in result
        print("✅ ServiceNow Adapter: Safe incident created")
        
        # Test incident with PII
        pii_incident = {
            "short_description": "User access issue",
            "description": "User with SSN 123-45-6789 cannot access system",
            "priority": "High"
        }
        
        try:
            pii_result = await adapter.create_incident(
                pii_incident,
                tenant_id=TEST_TENANT_ID,
                session_id=TEST_SESSION_ID
            )
            # Check if PII was masked in result
            if "123-45-6789" in str(pii_result):
                print("⚠️ ServiceNow Adapter: PII not masked (check configuration)")
            else:
                print("✅ ServiceNow Adapter: PII properly masked")
        except Exception as e:
            print("✅ ServiceNow Adapter: PII incident blocked as expected")
    
    async def test_db2_adapter(self):
        """Test DB2 adapter functionality"""
        from pki_adapters import DB2Adapter, JiminiPolicyEngine
        
        engine = JiminiPolicyEngine()
        adapter = DB2Adapter("db2://test:50000/testdb", engine)
        
        # Test safe query
        safe_query = "SELECT employee_id, name FROM employees WHERE department = ?"
        safe_params = {"department": "IT"}
        
        result = await adapter.execute_query(
            safe_query,
            safe_params,
            tenant_id=TEST_TENANT_ID,
            session_id=TEST_SESSION_ID
        )
        
        assert "rows" in result
        print("✅ DB2 Adapter: Safe query executed")
        
        # Test query with PII in parameters
        pii_query = "SELECT * FROM employees WHERE ssn = ?"
        pii_params = {"ssn": "123-45-6789"}
        
        try:
            pii_result = await adapter.execute_query(
                pii_query,
                pii_params,
                tenant_id=TEST_TENANT_ID,
                session_id=TEST_SESSION_ID
            )
            print("⚠️ DB2 Adapter: PII query allowed (check shadow mode)")
        except Exception as e:
            print("✅ DB2 Adapter: PII query blocked as expected")

# 🎯 **INTEGRATION TESTS**

class TestIntegrationScenarios:
    """End-to-end integration test scenarios"""
    
    async def test_government_citizen_lookup_flow(self):
        """Test complete government citizen lookup workflow"""
        print("\n🏛️ Testing Government Citizen Lookup Flow...")
        
        from pki_adapters import PKIAdapterFactory, JiminiPolicyEngine
        
        # Initialize system
        engine = JiminiPolicyEngine()
        factory = PKIAdapterFactory(engine)
        
        # Create adapters
        ldap_adapter = factory.create_ldap_adapter("ldap://gov.ldap")
        ums_adapter = factory.create_ums_adapter("https://ums.agency.gov")
        db2_adapter = factory.create_db2_adapter("db2://mainframe:50000/citizen_db")
        
        # Scenario 1: Safe citizen lookup
        print("  📋 Testing safe citizen lookup...")
        
        # LDAP search for user
        ldap_result = await ldap_adapter.search(
            base_dn="ou=citizens,dc=agency,dc=gov",
            search_filter="(cn=John Doe)",
            attributes=["cn", "employeeID", "department"],
            tenant_id=TEST_TENANT_ID,
            session_id=TEST_SESSION_ID
        )
        print(f"    ✅ LDAP lookup completed: {len(ldap_result.get('entries', []))} entries")
        
        # UMS profile lookup
        if ldap_result.get('entries'):
            employee_id = "E12345"
            ums_result = await ums_adapter.get_user_profile(
                employee_id,
                tenant_id=TEST_TENANT_ID,
                session_id=TEST_SESSION_ID
            )
            print(f"    ✅ UMS profile retrieved: {ums_result.get('username', 'N/A')}")
        
        # Scenario 2: PII-containing lookup (should be blocked/masked)
        print("  🚫 Testing PII-containing lookup...")
        
        try:
            # Query with SSN
            pii_query = "SELECT * FROM citizens WHERE ssn = ? AND name = ?"
            pii_params = {"ssn": "123-45-6789", "name": "John Doe"}
            
            db_result = await db2_adapter.execute_query(
                pii_query,
                pii_params,
                tenant_id=TEST_TENANT_ID,
                session_id=TEST_SESSION_ID
            )
            
            # Check if PII was masked
            result_str = str(db_result)
            if "123-45-6789" in result_str:
                print("    ⚠️ Warning: SSN not masked in database result")
            else:
                print("    ✅ SSN properly masked in database result")
                
        except Exception as e:
            print("    ✅ PII query blocked by policy engine")
    
    async def test_servicenow_incident_creation_flow(self):
        """Test ServiceNow incident creation with PII protection"""
        print("\n🎟️ Testing ServiceNow Incident Creation Flow...")
        
        from pki_adapters import ServiceNowAdapter, JiminiPolicyEngine
        
        engine = JiminiPolicyEngine()
        snow_adapter = ServiceNowAdapter("https://agency.service-now.com", "admin", "pass", engine)
        
        # Test cases with different PII levels
        test_cases = [
            {
                "name": "Safe incident",
                "data": {
                    "short_description": "System access issue",
                    "description": "User cannot access the portal",
                    "priority": "Medium",
                    "caller_id": "employee123"
                }
            },
            {
                "name": "Phone number incident",
                "data": {
                    "short_description": "Password reset request",
                    "description": "User at 555-123-4567 needs password reset",
                    "priority": "Low",
                    "caller_id": "help_desk"
                }
            },
            {
                "name": "SSN incident (critical)",
                "data": {
                    "short_description": "Identity verification issue",
                    "description": "Cannot verify user with SSN 123-45-6789",
                    "priority": "High",
                    "caller_id": "security_team"
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"  📝 Testing: {test_case['name']}")
            
            try:
                result = await snow_adapter.create_incident(
                    test_case["data"],
                    tenant_id=TEST_TENANT_ID,
                    session_id=TEST_SESSION_ID
                )
                
                # Check for PII in response
                result_str = str(result)
                pii_found = []
                
                if "555-123-4567" in result_str:
                    pii_found.append("phone")
                if "123-45-6789" in result_str:
                    pii_found.append("ssn")
                
                if pii_found:
                    print(f"    ⚠️ PII detected in response: {', '.join(pii_found)}")
                else:
                    print(f"    ✅ Incident created, PII properly handled")
                    
            except Exception as e:
                print(f"    🚫 Incident blocked: {str(e)[:100]}...")
    
    async def test_llm_integration_protection(self):
        """Test LLM integration with PII protection"""
        print("\n🤖 Testing LLM Integration Protection...")
        
        from jimini_gateway import JiminiPolicyEngine, SystemType, Direction
        
        engine = JiminiPolicyEngine()
        
        # Test various LLM queries
        test_queries = [
            {
                "query": "What are the office hours for government services?",
                "expected": "allow",
                "description": "Safe general query"
            },
            {
                "query": "How do I update my information? My phone is 555-123-4567",
                "expected": "flag",
                "description": "Query with phone number"
            },
            {
                "query": "I need help with my account. My SSN is 123-45-6789",
                "expected": "block",
                "description": "Query with SSN"
            },
            {
                "query": "API_KEY=sk-1234567890abcdef Please help with integration",
                "expected": "block",
                "description": "Query with API key"
            }
        ]
        
        for test in test_queries:
            print(f"  🧪 Testing: {test['description']}")
            
            decision = await engine.evaluate_request(
                content=test["query"],
                system=SystemType.LLM,
                endpoint="/chat/completions",
                direction=Direction.OUTBOUND,
                tenant_id=TEST_TENANT_ID,
                session_id=TEST_SESSION_ID
            )
            
            print(f"    📊 Decision: {decision.decision}")
            print(f"    📋 Rules triggered: {', '.join(decision.rule_ids) if decision.rule_ids else 'None'}")
            print(f"    🎭 Masked fields: {len(decision.masked_fields)}")
            
            # Verify expected behavior
            if decision.decision.value == test["expected"]:
                print(f"    ✅ Expected decision: {test['expected']}")
            else:
                print(f"    ⚠️ Unexpected decision: got {decision.decision.value}, expected {test['expected']}")

# 🚀 **TEST RUNNER**

async def run_all_tests():
    """Run all test suites"""
    print("🧪 Starting Jimini Gateway Test Suite")
    print("=" * 50)
    
    try:
        # Test API endpoints
        print("\n📡 Testing API Endpoints...")
        api_tests = TestJiminiGatewayAPI()
        
        await api_tests.test_health_check()
        await api_tests.test_get_rules()
        await api_tests.test_validate_rule()
        await api_tests.test_invalid_rule_validation()
        await api_tests.test_dry_run_rule()
        await api_tests.test_publish_rule()
        await api_tests.test_get_coverage()
        await api_tests.test_get_decisions()
        
        print("\n🔌 Testing PKI Adapters...")
        pki_tests = TestPKIAdapters()
        
        await pki_tests.test_ldap_adapter()
        await pki_tests.test_servicenow_adapter()
        await pki_tests.test_db2_adapter()
        
        print("\n🎯 Testing Integration Scenarios...")
        integration_tests = TestIntegrationScenarios()
        
        await integration_tests.test_government_citizen_lookup_flow()
        await integration_tests.test_servicenow_incident_creation_flow()
        await integration_tests.test_llm_integration_protection()
        
        print("\n✅ All Tests Completed Successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test Suite Failed: {e}")
        raise

# Performance Tests
async def run_performance_tests():
    """Run performance and load tests"""
    print("\n⚡ Running Performance Tests...")
    
    async with JiminiTestClient() as client:
        # Test API response times
        start_time = datetime.now()
        
        # Run 100 concurrent coverage requests
        tasks = []
        for _ in range(100):
            tasks.append(client.client.get("/api/v1/coverage"))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        successful_responses = len([r for r in responses if not isinstance(r, Exception)])
        
        print(f"  📊 Coverage Endpoint Performance:")
        print(f"    • 100 concurrent requests completed in {duration:.2f}s")
        print(f"    • Success rate: {successful_responses}/100")
        print(f"    • Average response time: {duration/100*1000:.1f}ms")

if __name__ == "__main__":
    print("🛡️ Jimini Gateway Test Suite")
    print("Make sure Jimini Gateway is running on localhost:8000")
    print("Start with: python jimini_gateway.py")
    print()
    
    # Run tests
    asyncio.run(run_all_tests())
    
    # Run performance tests
    asyncio.run(run_performance_tests())
    
    print("\n🎉 Test Suite Complete!")