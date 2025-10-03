#!/usr/bin/env python3
"""
🎯 JIMINI GATEWAY DEMONSTRATION
==============================

Complete demonstration of Jimini Gateway capabilities for government PKI systems.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# Configuration
GATEWAY_URL = "http://localhost:8000"
TENANT_ID = "gov-agency-demo"
SESSION_ID = f"demo_session_{int(datetime.now().timestamp())}"

class JiminiDemo:
    """Jimini Gateway demonstration"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=GATEWAY_URL,
            headers={
                "X-Tenant-Id": TENANT_ID,
                "X-Session-Id": SESSION_ID,
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f"  🛡️ {title}")
        print(f"{'='*60}")
    
    def print_subsection(self, title):
        print(f"\n📋 {title}")
        print("-" * 40)
    
    async def demo_health_check(self):
        """Demonstrate health check"""
        self.print_section("HEALTH CHECK & SYSTEM STATUS")
        
        try:
            response = await self.client.get("/health")
            health = response.json()
            
            print(f"✅ Service Status: {health['status']}")
            print(f"📊 Active Rules: {health['active_rules']}")
            print(f"📈 Total Decisions: {health['total_decisions']}")
            print(f"🔧 Mode: {health['mode']}")
            print(f"⏰ Timestamp: {health['timestamp']}")
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    async def demo_rules_management(self):
        """Demonstrate rules management"""
        self.print_section("POLICY RULES MANAGEMENT")
        
        # Get existing rules
        self.print_subsection("Current Rules")
        try:
            response = await self.client.get("/api/v1/rules")
            rules_data = response.json()
            
            if rules_data["code"] == "ok":
                rules = rules_data["data"]["rules"]
                print(f"📜 Total Rules: {len(rules)}")
                
                for rule in rules:
                    print(f"  • {rule['id']}: {rule['name']} ({rule['action'].upper()})")
                    print(f"    Systems: {', '.join(rule['system_scope'])}")
                    print(f"    Severity: {rule['severity']}")
            
        except Exception as e:
            print(f"❌ Failed to get rules: {e}")
        
        # Create and test a new rule
        self.print_subsection("Creating New Rule")
        new_rule = {
            "id": f"DEMO-RULE-{int(datetime.now().timestamp())}",
            "name": "Demo Credit Card Detection",
            "pattern": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "action": "flag",
            "severity": "high",
            "system_scope": ["llm", "service_now"],
            "enabled": True
        }
        
        # Validate rule
        try:
            response = await self.client.post("/api/v1/rules/validate", json=new_rule)
            validation = response.json()
            
            if validation["code"] == "ok":
                print(f"✅ Rule validation passed")
            else:
                print(f"❌ Rule validation failed: {validation['message']}")
                return
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return
        
        # Dry run test
        try:
            test_content = "Please process payment with card 4532-1234-5678-9012"
            response = await self.client.post("/api/v1/rules/dryrun", json={
                **new_rule,
                "test_content": test_content
            })
            dryrun = response.json()
            
            if dryrun["code"] == "ok":
                result = dryrun["data"]
                print(f"🧪 Dry run result: {'MATCHED' if result['matched'] else 'NO MATCH'}")
                print(f"📊 Decision: {result['decision'].upper()}")
            
        except Exception as e:
            print(f"❌ Dry run error: {e}")
        
        # Publish rule
        try:
            response = await self.client.post("/api/v1/rules/publish", json=new_rule)
            publish = response.json()
            
            if publish["code"] == "ok":
                print(f"📜 Rule published: {new_rule['id']}")
            else:
                print(f"❌ Publish failed: {publish['message']}")
        
        except Exception as e:
            print(f"❌ Publish error: {e}")
    
    async def demo_pii_protection(self):
        """Demonstrate PII protection scenarios"""
        self.print_section("PII PROTECTION & MASKING")
        
        # Simulate PKI system requests with PII
        test_scenarios = [
            {
                "name": "LDAP User Search",
                "content": '{"search_filter": "(cn=John Doe)", "attributes": ["cn", "mail", "telephoneNumber"]}',
                "system": "ldap",
                "endpoint": "/search",
                "expected": "Safe search should be allowed"
            },
            {
                "name": "ServiceNow Incident with Phone",
                "content": '{"description": "User at 555-123-4567 needs password reset", "priority": "Medium"}',
                "system": "service_now", 
                "endpoint": "/incidents",
                "expected": "Phone number should be flagged"
            },
            {
                "name": "Database Query with SSN",
                "content": '{"query": "SELECT * FROM citizens WHERE ssn = ?", "params": {"ssn": "123-45-6789"}}',
                "system": "db2",
                "endpoint": "/query",
                "expected": "SSN should be blocked"
            },
            {
                "name": "LLM Request with API Key",
                "content": '{"prompt": "Help me integrate with API_KEY=sk-1234567890abcdef", "model": "gpt-4"}',
                "system": "llm",
                "endpoint": "/chat/completions",
                "expected": "API key should be blocked"
            }
        ]
        
        from jimini_gateway import JiminiPolicyEngine, SystemType, Direction
        
        # Create engine instance for simulation
        engine = JiminiPolicyEngine()
        
        for scenario in test_scenarios:
            self.print_subsection(f"Scenario: {scenario['name']}")
            print(f"📝 Description: {scenario['expected']}")
            print(f"🔍 Content: {scenario['content'][:100]}...")
            
            try:
                # Map system names to enum values
                system_map = {
                    "ldap": SystemType.LDAP,
                    "service_now": SystemType.SERVICENOW,
                    "db2": SystemType.DB2,
                    "llm": SystemType.LLM
                }
                
                decision = await engine.evaluate_request(
                    content=scenario["content"],
                    system=system_map[scenario["system"]],
                    endpoint=scenario["endpoint"],
                    direction=Direction.OUTBOUND,
                    tenant_id=TENANT_ID,
                    session_id=SESSION_ID
                )
                
                print(f"📊 Decision: {decision.decision.value.upper()}")
                print(f"⚡ Latency: {decision.latency_ms:.1f}ms")
                
                if decision.rule_ids:
                    print(f"📋 Rules triggered: {', '.join(decision.rule_ids)}")
                
                if decision.masked_fields:
                    print(f"🎭 Masked fields: {len(decision.masked_fields)} fields")
                    for field in decision.masked_fields:
                        print(f"    • {field}")
                
                if decision.citations:
                    print(f"📚 Policy citations: {len(decision.citations)} references")
                
            except Exception as e:
                print(f"❌ Evaluation error: {e}")
    
    async def demo_coverage_metrics(self):
        """Demonstrate coverage and metrics"""
        self.print_section("COVERAGE METRICS & ANALYTICS")
        
        try:
            response = await self.client.get("/api/v1/coverage")
            coverage_data = response.json()
            
            if coverage_data["code"] == "ok":
                data = coverage_data["data"]
                
                print(f"📊 Policy Enforcement Summary:")
                print(f"  • Total Requests: {data['total_requests']}")
                print(f"  • Blocked: {data['blocked']}")
                print(f"  • Flagged: {data['flagged']}")
                print(f"  • Allowed: {data['allowed']}")
                print(f"  • Coverage Rate: {data['coverage_rate']:.1f}%")
                print(f"  • Active Rules: {data['active_rules']}")
                
                if "systems" in data and data["systems"]:
                    print(f"\n🏢 System Breakdown:")
                    for system, stats in data["systems"].items():
                        print(f"  • {system.upper()}:")
                        print(f"    - Total: {stats['total']}")
                        print(f"    - Blocked: {stats['blocked']}")
                        print(f"    - Flagged: {stats['flagged']}")
                        print(f"    - Allowed: {stats['allowed']}")
        
        except Exception as e:
            print(f"❌ Coverage error: {e}")
    
    async def demo_decision_log(self):
        """Demonstrate decision logging"""
        self.print_section("DECISION AUDIT LOG")
        
        try:
            response = await self.client.get("/api/v1/decisions", params={"limit": 10})
            decisions_data = response.json()
            
            if decisions_data["code"] == "ok":
                decisions = decisions_data["data"]["decisions"]
                
                print(f"📋 Recent Decisions ({len(decisions)} shown):")
                
                for decision in decisions:
                    timestamp = decision["ts"][:19].replace("T", " ")
                    
                    decision_icon = {
                        "allow": "✅",
                        "flag": "⚠️", 
                        "block": "🚫"
                    }.get(decision["decision"], "❓")
                    
                    print(f"\n  {decision_icon} {decision['decision'].upper()} - {timestamp}")
                    print(f"    📡 System: {decision['system']}")
                    print(f"    🔗 Endpoint: {decision['endpoint']}")
                    print(f"    🆔 Request ID: {decision['request_id']}")
                    print(f"    ⚡ Latency: {decision['latency_ms']:.1f}ms")
                    
                    if decision['rule_ids']:
                        print(f"    📋 Rules: {', '.join(decision['rule_ids'])}")
                    
                    if decision['masked_fields']:
                        print(f"    🎭 Masked: {len(decision['masked_fields'])} fields")
        
        except Exception as e:
            print(f"❌ Decision log error: {e}")
    
    async def demo_break_glass_access(self):
        """Demonstrate break-glass reveal functionality"""
        self.print_section("BREAK-GLASS ACCESS CONTROL")
        
        print("🚨 Break-glass access allows temporary revelation of masked data")
        print("📋 All break-glass actions are logged for compliance auditing")
        
        # Simulate a break-glass request
        reveal_request = {
            "request_id": "demo_request_001",
            "field": "user.ssn",
            "reason": "Legal investigation requires access to citizen SSN for case #2024-001"
        }
        
        try:
            response = await self.client.post("/api/v1/reveal", json=reveal_request)
            reveal_data = response.json()
            
            if reveal_data["code"] == "ok":
                data = reveal_data["data"]
                print(f"🔓 Break-glass access granted:")
                print(f"  • Field: {data['field']}")
                print(f"  • Reason: {data['reason']}")
                print(f"  • TTL: {data['ttl']}")
                print(f"  • Audit Logged: {data['audit_logged']}")
                print(f"⚠️ Access will be automatically re-masked after TTL expiry")
            else:
                print(f"❌ Break-glass denied: {reveal_data['message']}")
        
        except Exception as e:
            print(f"❌ Break-glass error: {e}")

async def run_complete_demo():
    """Run the complete Jimini Gateway demonstration"""
    print("🛡️ JIMINI GATEWAY DEMONSTRATION")
    print("Enterprise PKI Security & Policy Engine")
    print(f"Tenant: {TENANT_ID}")
    print(f"Session: {SESSION_ID}")
    
    async with JiminiDemo() as demo:
        # Run all demonstration sections
        await demo.demo_health_check()
        await demo.demo_rules_management()
        await demo.demo_pii_protection()
        await demo.demo_coverage_metrics()
        await demo.demo_decision_log()
        await demo.demo_break_glass_access()
        
        print(f"\n{'='*60}")
        print("  ✅ DEMONSTRATION COMPLETE")
        print(f"{'='*60}")
        print("\n🎯 Key Capabilities Demonstrated:")
        print("  • Policy rule creation and validation")
        print("  • PII detection and masking")
        print("  • Multi-system integration (LDAP, ServiceNow, DB2, LLM)")
        print("  • Real-time decision logging")
        print("  • Coverage metrics and analytics")
        print("  • Break-glass access controls")
        print("\n🔗 Next Steps:")
        print("  • Integrate with your React dashboard")
        print("  • Configure PKI system connections")
        print("  • Deploy to production environment")
        print("  • Set up monitoring and alerting")
        
        print(f"\n📊 API Endpoints Available:")
        print(f"  • Gateway: {GATEWAY_URL}")
        print(f"  • Health: {GATEWAY_URL}/health")
        print(f"  • API Docs: {GATEWAY_URL}/docs")
        print(f"  • Rules: {GATEWAY_URL}/api/v1/rules")
        print(f"  • Coverage: {GATEWAY_URL}/api/v1/coverage")

if __name__ == "__main__":
    print("🚀 Starting Jimini Gateway Demonstration...")
    print("Make sure Jimini Gateway is running on localhost:8000")
    print()
    
    # Run the demonstration
    asyncio.run(run_complete_demo())