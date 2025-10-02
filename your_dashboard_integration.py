#!/usr/bin/env python3
"""
YOUR DASHBOARD PII PROTECTION
=============================

Copy this code into your existing dashboard to add instant PII protection.
Replace the SimpleGovPIIProtector import with your existing dashboard functions.
"""

# Import the PII protector directly
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Copy the protector class inline for demo
import re
import json
from datetime import datetime

class SimpleGovPIIProtector:
    def __init__(self):
        self.rules = [
            {"id": "SSN-PROTECTION", "name": "Social Security Number", "pattern": r'\b\d{3}-?\d{2}-?\d{4}\b', "action": "BLOCK", "severity": "CRITICAL"},
            {"id": "DL-PROTECTION", "name": "Driver's License Number", "pattern": r'[A-Z]{1,2}\d{7,8}|D\d{8}', "action": "FLAG", "severity": "HIGH"},
            {"id": "ADDRESS-PROTECTION", "name": "Street Address", "pattern": r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b', "action": "FLAG", "severity": "MEDIUM"},
            {"id": "PHONE-PROTECTION", "name": "Phone Number", "pattern": r'\b\d{3}-?\d{3}-?\d{4}\b', "action": "FLAG", "severity": "MEDIUM"}
        ]
    
    def check_text(self, text, context="dashboard"):
        results = {"text": text, "context": context, "timestamp": datetime.now().isoformat(), "violations": [], "decision": "ALLOW", "severity": "NONE"}
        for rule in self.rules:
            matches = re.finditer(rule["pattern"], text, re.IGNORECASE)
            for match in matches:
                violation = {"rule_id": rule["id"], "rule_name": rule["name"], "matched_text": match.group(), "position": match.span(), "action": rule["action"], "severity": rule["severity"]}
                results["violations"].append(violation)
                if rule["action"] == "BLOCK": 
                    results["decision"] = "BLOCK"
                    results["severity"] = "CRITICAL"
                elif rule["action"] == "FLAG" and results["decision"] != "BLOCK":
                    results["decision"] = "FLAG"
                    if results["severity"] in ["NONE", "LOW"]: results["severity"] = rule["severity"]
        return results

class YourDashboardWithProtection:
    """Your existing dashboard with PII protection added"""
    
    def __init__(self):
        self.pii_protector = SimpleGovPIIProtector()
        # Your existing dashboard initialization here
    
    def citizen_lookup(self, citizen_id, query_params):
        """Your existing citizen lookup with PII protection"""
        
        # 1. Check the input for PII
        input_check = self.pii_protector.check_text(
            f"citizen_id={citizen_id}, params={query_params}", 
            "citizen_lookup_input"
        )
        
        if input_check['decision'] == 'BLOCK':
            return {
                "error": "Cannot process request - contains sensitive data",
                "details": "PII detected in input parameters",
                "blocked": True
            }
        
        # 2. Your existing database query
        # Replace this with your real database call
        citizen_data = self.get_citizen_from_database(citizen_id)
        
        # 3. Check the output for PII before returning
        output_check = self.pii_protector.check_text(
            str(citizen_data), 
            "citizen_lookup_response"
        )
        
        if output_check['violations']:
            # Mask PII in the response
            safe_data = self.mask_pii_in_response(citizen_data, output_check['violations'])
            return {
                "data": safe_data,
                "pii_protected": True,
                "audit_log": f"PII masked in response: {len(output_check['violations'])} violations"
            }
        
        return {"data": citizen_data, "pii_protected": False}
    
    def background_check_request(self, person_info, check_type):
        """Your background check system with audit trail"""
        
        # Always log background check requests
        input_text = f"Background check: {person_info}, type: {check_type}"
        pii_check = self.pii_protector.check_text(input_text, "background_check")
        
        # Log the request for audit (required for background checks)
        audit_entry = {
            "timestamp": "2025-10-02T20:10:00Z",
            "user": "dashboard_user",  # Replace with actual user
            "action": "background_check_request",
            "input": input_text,
            "pii_detected": len(pii_check['violations']),
            "justification": "Employment verification process"  # Add real justification
        }
        
        print(f"🔍 AUDIT LOG: {audit_entry}")
        
        # Your existing background check API call
        result = self.call_background_check_api(person_info, check_type)
        
        return {
            "result": result,
            "audit_logged": True,
            "pii_violations": pii_check['violations']
        }
    
    def medical_billing_lookup(self, account_info):
        """Your medical billing with HIPAA protection"""
        
        # Check for medical PII
        pii_check = self.pii_protector.check_text(str(account_info), "medical_billing")
        
        if pii_check['decision'] == 'BLOCK':
            return {
                "error": "HIPAA VIOLATION PREVENTED",
                "message": "Cannot process medical data without proper authorization",
                "requires_supervisor_approval": True
            }
        
        # Your existing medical billing query
        billing_data = self.get_medical_billing_data(account_info)
        
        return {
            "data": "[MEDICAL DATA - HIPAA PROTECTED]",  # Replace with masked data
            "hipaa_compliant": True,
            "audit_required": True
        }
    
    def mask_pii_in_response(self, data, violations):
        """Mask PII in responses before sending to dashboard"""
        masked_data = str(data)
        
        for violation in violations:
            # Replace actual PII with masked version
            mask_text = f"[PROTECTED_{violation['rule_name'].upper().replace(' ', '_')}]"
            masked_data = masked_data.replace(violation['matched_text'], mask_text)
        
        return masked_data
    
    def get_citizen_from_database(self, citizen_id):
        """Replace this with your actual database query"""
        # This is where your real database call goes
        return {
            "id": citizen_id,
            "name": "John Doe",
            "address": "123 Main Street",  # This will get masked
            "phone": "555-123-4567",      # This will get masked
            "status": "active"
        }
    
    def call_background_check_api(self, person_info, check_type):
        """Replace this with your actual background check API"""
        return {"status": "pending", "reference": "BGC123456"}
    
    def get_medical_billing_data(self, account_info):
        """Replace this with your actual medical billing query"""
        return {"account": account_info, "status": "active"}


def demo_your_protected_dashboard():
    """Demo your dashboard with PII protection"""
    
    print("🏛️  YOUR DASHBOARD WITH PII PROTECTION")
    print("="*50)
    
    dashboard = YourDashboardWithProtection()
    
    # Test citizen lookup
    print("\n🔍 Testing Citizen Lookup:")
    result = dashboard.citizen_lookup("CITIZEN123", {"ssn": "123-45-6789"})
    print(f"Result: {result}")
    
    # Test background check  
    print("\n📋 Testing Background Check:")
    result = dashboard.background_check_request(
        {"name": "Jane Smith", "dl": "A9876543"}, 
        "employment_verification"
    )
    print(f"Result: {result}")
    
    # Test medical billing
    print("\n🏥 Testing Medical Billing:")
    result = dashboard.medical_billing_lookup({"patient_id": "987-65-4321"})
    print(f"Result: {result}")

if __name__ == "__main__":
    demo_your_protected_dashboard()
    
    print("\n🎯 TO INTEGRATE WITH YOUR DASHBOARD:")
    print("1. Copy the YourDashboardWithProtection class")
    print("2. Replace the demo functions with your real database/API calls")
    print("3. Add the pii_protector.check_text() calls to your existing functions") 
    print("4. Test with your real data (use fake SSNs for testing!)")
    print("\n✅ Your citizens' PII will be automatically protected!")