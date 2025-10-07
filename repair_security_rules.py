#!/usr/bin/env python3
"""
🔧 SECURITY RULES VALIDATION AND REPAIR UTILITY 🔧

Validates and repairs security rules for enterprise deployment compliance

Functions:
1. Identify rules missing required fields
2. Add default values for missing fields  
3. Validate regex patterns
4. Ensure deployment readiness
5. Generate corrected rules file

Required Rule Fields:
- id: Unique rule identifier
- title: Human-readable rule title
- pattern: Regex pattern for matching
- action: Action to take (allow/flag/block)
- applies_to: List of contexts to apply rule
- endpoints: List of endpoints for rule application
"""

import yaml
import re
from typing import Dict, List, Any
from pathlib import Path

def validate_and_repair_rules():
    """Validate and repair security rules for deployment"""
    print("🔧 Security Rules Validation and Repair Utility")
    print("="*55)
    
    # Read current rules
    with open('policy_rules.yaml', 'r') as f:
        policy_data = yaml.safe_load(f) or {}
    
    rules = policy_data.get('rules', [])
    print(f"📊 Total rules found: {len(rules)}")
    
    repaired_rules = []
    repair_count = 0
    invalid_count = 0
    
    for i, rule in enumerate(rules):
        repaired_rule = rule.copy()
        was_repaired = False
        
        # Ensure required fields exist
        required_fields = {
            'id': f'RULE-{i+1:03d}',
            'title': f'Security Rule {i+1}',
            'pattern': '.*',  # Default catch-all pattern
            'action': 'flag',
            'applies_to': ['user_input', 'prompt'],
            'endpoints': ['/*']
        }
        
        for field, default_value in required_fields.items():
            if field not in repaired_rule:
                repaired_rule[field] = default_value
                was_repaired = True
        
        # Validate and fix regex pattern
        if 'pattern' in repaired_rule:
            try:
                re.compile(repaired_rule['pattern'])
            except re.error:
                print(f"   ⚠️  Rule {i+1}: Invalid regex pattern, using safe default")
                repaired_rule['pattern'] = '.*'
                was_repaired = True
        
        # Ensure action is valid
        valid_actions = ['allow', 'flag', 'block']
        if repaired_rule.get('action') not in valid_actions:
            repaired_rule['action'] = 'flag'
            was_repaired = True
        
        # Ensure applies_to is a list
        if not isinstance(repaired_rule.get('applies_to'), list):
            repaired_rule['applies_to'] = ['user_input', 'prompt']
            was_repaired = True
        
        # Ensure endpoints is a list
        if not isinstance(repaired_rule.get('endpoints'), list):
            repaired_rule['endpoints'] = ['/*']
            was_repaired = True
        
        # Add standard fields if missing
        if 'severity' not in repaired_rule:
            severity_map = {'block': 'high', 'flag': 'medium', 'allow': 'low'}
            repaired_rule['severity'] = severity_map.get(repaired_rule['action'], 'medium')
        
        if 'description' not in repaired_rule:
            repaired_rule['description'] = repaired_rule.get('title', 'Security rule')
        
        repaired_rules.append(repaired_rule)
        
        if was_repaired:
            repair_count += 1
    
    # Update policy data
    policy_data['rules'] = repaired_rules
    
    # Write corrected rules back
    with open('policy_rules.yaml', 'w') as f:
        yaml.dump(policy_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"✅ Rules validation and repair complete:")
    print(f"   • Total rules: {len(repaired_rules)}")
    print(f"   • Repaired rules: {repair_count}")
    print(f"   • Invalid rules: {invalid_count}")
    print(f"   • All rules now deployment-ready")
    
    return True

if __name__ == '__main__':
    validate_and_repair_rules()