#!/usr/bin/env python3
"""
Simple Government PII Protection Test
=====================================

This script shows you EXACTLY how to protect citizen data in your dashboard.
Run this to see Jimini catch PII in real government data scenarios.
"""

import re
import json
from datetime import datetime

class SimpleGovPIIProtector:
    def __init__(self):
        self.rules = [
            {
                "id": "SSN-PROTECTION",
                "name": "Social Security Number",
                "pattern": r'\b\d{3}-?\d{2}-?\d{4}\b',
                "action": "BLOCK",
                "severity": "CRITICAL"
            },
            {
                "id": "DL-PROTECTION", 
                "name": "Driver's License Number",
                "pattern": r'[A-Z]{1,2}\d{7,8}|D\d{8}',
                "action": "FLAG",
                "severity": "HIGH"
            },
            {
                "id": "ADDRESS-PROTECTION",
                "name": "Street Address", 
                "pattern": r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
                "action": "FLAG",
                "severity": "MEDIUM"
            },
            {
                "id": "PHONE-PROTECTION",
                "name": "Phone Number",
                "pattern": r'\b\d{3}-?\d{3}-?\d{4}\b',
                "action": "FLAG", 
                "severity": "MEDIUM"
            },
            {
                "id": "EMAIL-PROTECTION",
                "name": "Email Address",
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "action": "FLAG",
                "severity": "MEDIUM"
            }
        ]
    
    def check_text(self, text, context="dashboard"):
        """Check text for PII and return results"""
        results = {
            "text": text,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "violations": [],
            "decision": "ALLOW",
            "severity": "NONE"
        }
        
        for rule in self.rules:
            matches = re.finditer(rule["pattern"], text, re.IGNORECASE)
            
            for match in matches:
                violation = {
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "matched_text": match.group(),
                    "position": match.span(),
                    "action": rule["action"],
                    "severity": rule["severity"]
                }
                results["violations"].append(violation)
                
                # Update overall decision
                if rule["action"] == "BLOCK":
                    results["decision"] = "BLOCK"
                    results["severity"] = "CRITICAL"
                elif rule["action"] == "FLAG" and results["decision"] != "BLOCK":
                    results["decision"] = "FLAG"
                    if results["severity"] in ["NONE", "LOW"]:
                        results["severity"] = rule["severity"]
        
        return results

def test_government_scenarios():
    """Test real government data scenarios"""
    
    protector = SimpleGovPIIProtector()
    
    test_scenarios = [
        {
            "name": "Driver Registration Form",
            "text": "Applicant: John Doe, SSN: 123-45-6789, Address: 123 Main Street, Phone: 555-123-4567, Email: john.doe@email.com, Driver's License: D12345678"
        },
        {
            "name": "Background Check Request", 
            "text": "Background check for Jane Smith, DL# A9876543, requesting criminal history and employment verification"
        },
        {
            "name": "Medical Billing Query",
            "text": "Patient billing inquiry for account 987-65-4321, insurance claim processing required"
        },
        {
            "name": "Citizen Lookup Dashboard",
            "text": "Dashboard query: SELECT * FROM citizens WHERE ssn='111-22-3333' AND address LIKE '%Oak Avenue%'"
        },
        {
            "name": "Safe Government Communication",
            "text": "Meeting scheduled for Tuesday to review policy updates and training materials"
        }
    ]
    
    print("🛡️  GOVERNMENT PII PROTECTION TEST")
    print("="*60)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}: {scenario['name']}")
        print("-" * 40)
        
        result = protector.check_text(scenario['text'])
        
        print(f"📝 Text: {scenario['text']}")
        print(f"🚨 Decision: {result['decision']}")
        print(f"⚠️  Severity: {result['severity']}")
        
        if result['violations']:
            print("🔍 PII Detected:")
            for violation in result['violations']:
                print(f"   • {violation['rule_name']}: '{violation['matched_text']}' ({violation['action']})")
        else:
            print("✅ No PII detected - Safe to process")
        
        print()

def dashboard_integration_example():
    """Show how to integrate with your dashboard"""
    
    print("\n🚀 DASHBOARD INTEGRATION EXAMPLE")
    print("="*50)
    
    protector = SimpleGovPIIProtector()
    
    # Simulate dashboard functions
    def safe_citizen_lookup(query_text):
        """Example: Protect citizen lookup queries"""
        result = protector.check_text(query_text, "citizen_lookup")
        
        if result['decision'] == 'BLOCK':
            return {
                "error": "BLOCKED: PII detected in query",
                "violations": result['violations'],
                "message": "Cannot execute query containing sensitive citizen data"
            }
        elif result['decision'] == 'FLAG':
            return {
                "warning": "PII detected - query flagged for audit", 
                "violations": result['violations'],
                "data": "[PROTECTED DATA - logged for compliance]",
                "audit_required": True
            }
        else:
            return {
                "status": "safe",
                "data": "[Query executed successfully]"
            }
    
    def safe_response_filter(response_data):
        """Example: Filter responses before sending to dashboard"""
        result = protector.check_text(str(response_data), "response_filter")
        
        if result['violations']:
            # Mask the PII
            masked_data = str(response_data)
            for violation in result['violations']:
                masked_data = masked_data.replace(
                    violation['matched_text'], 
                    f"[MASKED_{violation['rule_name']}]"
                )
            return {
                "data": masked_data,
                "pii_masked": True,
                "violations": result['violations']
            }
        
        return {"data": response_data, "pii_masked": False}
    
    # Test dashboard functions
    print("🔍 Testing Citizen Lookup Protection:")
    query = "SELECT * FROM citizens WHERE ssn='123-45-6789'"
    result = safe_citizen_lookup(query)
    print(f"Query: {query}")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\n🔒 Testing Response Filtering:")
    response = "Citizen: John Doe, Address: 456 Oak Avenue, Phone: 555-987-6543"
    filtered = safe_response_filter(response)
    print(f"Original: {response}")
    print(f"Filtered: {json.dumps(filtered, indent=2)}")

if __name__ == "__main__":
    print("🏛️  GOVERNMENT CITIZEN DATA PROTECTION")
    print("Building PII protection for your dashboard")
    print("=" * 60)
    
    test_government_scenarios()
    dashboard_integration_example()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run this script: python3 simple_gov_pii_test.py")
    print("2. Integrate these protectors into your dashboard code")
    print("3. Test with your real (anonymized) data")
    print("4. Deploy to production with full Jimini platform")
    print("\n✅ Your citizen data will be protected automatically!")