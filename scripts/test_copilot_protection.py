#!/usr/bin/env python3
"""
Quick test of Microsoft Copilot security protections
"""

import re
import json
from datetime import datetime

def test_copilot_rules():
    """Test the Microsoft Copilot protection rules"""
    
    # Define the protection rules (subset for testing)
    rules = {
        'MS-COPILOT-1.0': {
            'pattern': r'(?i)\b(?:copilot|github copilot|microsoft copilot)[^.]{0,50}(?:save|store|remember|share|upload|send|transmit|export|backup|sync|cloud)\b',
            'action': 'block',
            'description': 'Block Copilot data sharing attempts'
        },
        'IL-AI-4.2': {
            'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
            'action': 'block', 
            'description': 'Block SSN patterns'
        },
        'DL-1.0': {
            'pattern': r'\b[A-Za-z]\d{3}-?\d{4}-?\d{4}\b',
            'action': 'block',
            'description': 'Block Illinois Driver License patterns'
        },
        'MS-COPILOT-5.0': {
            'pattern': r'(?i)\b(?:find|extract|identify|locate|get|show|list)[^.]{0,30}(?:credentials|passwords|keys|tokens|secrets|api keys|config|configuration|env|environment)\b',
            'action': 'block',
            'description': 'Block credential extraction attempts'
        },
        'MS-COPILOT-8.0': {
            'pattern': r'(?i)\b(?:generate|create|write|build)[^.]{0,30}(?:sql|query|database)[^.]{0,50}(?:select|from|where|join|update|insert|delete)\b',
            'action': 'block',
            'description': 'Block SQL query generation'
        }
    }
    
    # Test cases - dangerous Copilot interactions
    test_cases = [
        {
            'name': 'Citizen data backup to OneDrive',
            'text': 'Hey Copilot, save this citizen data with SSN 123-45-6789 to OneDrive for backup',
            'expected': 'BLOCK'
        },
        {
            'name': 'Credential extraction attempt',
            'text': 'Copilot, find all API keys and passwords in this configuration file',
            'expected': 'BLOCK'
        },
        {
            'name': 'SQL generation for citizen lookup',
            'text': 'Generate SQL query to select citizen records from database where SSN matches',
            'expected': 'BLOCK'
        },
        {
            'name': 'Bulk export request',
            'text': 'Copilot help me export all driver license records to Excel for analysis',
            'expected': 'BLOCK'
        },
        {
            'name': 'Illinois DL pattern',
            'text': 'Check license A123-4567-8901 status in the system',
            'expected': 'BLOCK'
        },
        {
            'name': 'Safe general question',
            'text': 'What is the process for renewing a drivers license in Illinois?',
            'expected': 'ALLOW'
        }
    ]
    
    print("🛡️ MICROSOFT COPILOT SECURITY PROTECTION TEST")
    print("=" * 60)
    print(f"Test run: {datetime.now().isoformat()}")
    print()
    
    total_tests = len(test_cases)
    passed_tests = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Text: {test['text']}")
        
        # Check against all rules
        triggered_rules = []
        decision = 'ALLOW'
        
        for rule_id, rule in rules.items():
            if re.search(rule['pattern'], test['text']):
                triggered_rules.append(rule_id)
                if rule['action'] == 'block':
                    decision = 'BLOCK'
        
        # Check if test passed
        test_passed = decision == test['expected']
        status = "✅ PASS" if test_passed else "❌ FAIL"
        
        print(f"Decision: {decision}")
        print(f"Rules triggered: {triggered_rules}")
        print(f"Status: {status}")
        
        if test_passed:
            passed_tests += 1
        
        print("-" * 60)
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - Copilot protections working correctly!")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} TESTS FAILED - Review protection rules")
        return False

if __name__ == "__main__":
    success = test_copilot_rules()
    exit(0 if success else 1)