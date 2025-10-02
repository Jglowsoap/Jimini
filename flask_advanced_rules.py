"""
Enhanced Flask PII Protection with Rule Management
=================================================

This version provides both embedded rules AND API rule management,
giving you the flexibility to update rules without redeploying code.
"""

import json
import os
import yaml
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime
from typing import Dict, Any, List

app = Flask(__name__)
CORS(app)

class AdvancedPIIProtector:
    """Enhanced PII Protection with configurable rules"""
    
    def __init__(self, rules_file: str = None):
        # Default embedded rules (always available)
        self.default_rules = {
            'SSN-PROTECTION': {
                'name': 'Social Security Number',
                'pattern': r'\b\d{3}-?\d{2}-?\d{4}\b',
                'action': 'BLOCK',
                'severity': 'CRITICAL',
                'enabled': True
            },
            'DL-PROTECTION': {
                'name': 'Driver\'s License Number',
                'pattern': r'\b[A-Z]{1,2}\d{7,8}\b|D\d{8}\b',
                'action': 'FLAG',
                'severity': 'HIGH',
                'enabled': True
            },
            'ADDRESS-PROTECTION': {
                'name': 'Street Address',
                'pattern': r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
                'action': 'FLAG',
                'severity': 'MEDIUM',
                'enabled': True
            },
            'PHONE-PROTECTION': {
                'name': 'Phone Number',
                'pattern': r'\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b',
                'action': 'FLAG',
                'severity': 'MEDIUM',
                'enabled': True
            },
            'EMAIL-PROTECTION': {
                'name': 'Email Address',
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'action': 'FLAG',
                'severity': 'LOW',
                'enabled': True
            }
        }
        
        self.rules = self.default_rules.copy()
        self.audit_log = []
        self.rules_file = rules_file
        
        # Load rules from file if provided
        if rules_file and os.path.exists(rules_file):
            self.load_rules_from_file(rules_file)
    
    def load_rules_from_file(self, rules_file: str):
        """Load rules from YAML or JSON file"""
        try:
            with open(rules_file, 'r') as f:
                if rules_file.endswith('.yaml') or rules_file.endswith('.yml'):
                    file_rules = yaml.safe_load(f)
                else:
                    file_rules = json.load(f)
            
            # Update rules with file content
            if isinstance(file_rules, dict) and 'rules' in file_rules:
                for rule in file_rules['rules']:
                    if 'id' in rule:
                        rule_id = rule['id']
                        self.rules[rule_id] = {
                            'name': rule.get('title', rule.get('name', rule_id)),
                            'pattern': rule.get('pattern', ''),
                            'action': rule.get('action', 'FLAG').upper(),
                            'severity': rule.get('severity', 'MEDIUM').upper(),
                            'enabled': rule.get('enabled', True)
                        }
            
            print(f"✅ Loaded {len(self.rules)} rules from {rules_file}")
            
        except Exception as e:
            print(f"❌ Error loading rules from {rules_file}: {e}")
            print("🛡️ Using default embedded rules")
    
    def get_active_rules(self) -> Dict[str, Dict]:
        """Get only enabled rules"""
        return {rule_id: rule for rule_id, rule in self.rules.items() if rule.get('enabled', True)}
    
    def protect_data(self, text: str, endpoint: str = "/api", user_id: str = "user") -> Dict[str, Any]:
        """Check text for PII using active rules"""
        violations = []
        decision = "ALLOW"
        highest_severity = "NONE"
        
        active_rules = self.get_active_rules()
        
        for rule_id, rule in active_rules.items():
            if not rule.get('pattern'):
                continue
                
            try:
                matches = re.finditer(rule['pattern'], text, re.IGNORECASE)
                for match in matches:
                    violation = {
                        'rule_id': rule_id,
                        'rule_name': rule['name'],
                        'matched_text': match.group(),
                        'position': [match.start(), match.end()],
                        'action': rule['action'],
                        'severity': rule['severity']
                    }
                    violations.append(violation)
                    
                    # Update overall decision
                    if rule['action'] == 'BLOCK':
                        decision = "BLOCK"
                        highest_severity = "CRITICAL"
                    elif rule['action'] == 'FLAG' and decision != 'BLOCK':
                        decision = "FLAG"
                        if highest_severity in ["NONE", "LOW", "MEDIUM"]:
                            highest_severity = rule['severity']
            except re.error as e:
                print(f"⚠️ Invalid regex in rule {rule_id}: {e}")
        
        # Log the decision
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'user_id': user_id,
            'decision': decision,
            'severity': highest_severity,
            'violations_count': len(violations),
            'text_length': len(text),
            'user_agent': request.headers.get('User-Agent', 'Unknown') if request else 'Unknown'
        }
        self.audit_log.append(audit_entry)
        
        return {
            'decision': decision,
            'severity': highest_severity,
            'violations': violations,
            'rule_ids': [v['rule_id'] for v in violations],
            'audit_id': len(self.audit_log) - 1
        }

# Initialize protector (can load from file)
RULES_FILE = os.getenv('JIMINI_RULES_FILE', 'government_rules.yaml')
protector = AdvancedPIIProtector(RULES_FILE if os.path.exists(RULES_FILE) else None)

# 🔧 **RULE MANAGEMENT API ENDPOINTS**

@app.route('/api/rules', methods=['GET'])
def get_rules():
    """Get all rules (enabled and disabled)"""
    return jsonify({
        'status': 'success',
        'rules': protector.rules,
        'active_count': len(protector.get_active_rules()),
        'total_count': len(protector.rules)
    })

@app.route('/api/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """Update a specific rule"""
    try:
        data = request.get_json()
        
        if rule_id not in protector.rules:
            return jsonify({'error': f'Rule {rule_id} not found'}), 404
        
        # Update rule fields
        rule = protector.rules[rule_id]
        if 'name' in data:
            rule['name'] = data['name']
        if 'pattern' in data:
            # Test regex validity
            try:
                re.compile(data['pattern'])
                rule['pattern'] = data['pattern']
            except re.error as e:
                return jsonify({'error': f'Invalid regex pattern: {e}'}), 400
        if 'action' in data:
            rule['action'] = data['action'].upper()
        if 'severity' in data:
            rule['severity'] = data['severity'].upper()
        if 'enabled' in data:
            rule['enabled'] = bool(data['enabled'])
        
        return jsonify({
            'status': 'success',
            'message': f'Rule {rule_id} updated',
            'rule': rule
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rules/<rule_id>/toggle', methods=['POST'])
def toggle_rule(rule_id):
    """Enable or disable a rule"""
    try:
        if rule_id not in protector.rules:
            return jsonify({'error': f'Rule {rule_id} not found'}), 404
        
        current_status = protector.rules[rule_id].get('enabled', True)
        protector.rules[rule_id]['enabled'] = not current_status
        
        return jsonify({
            'status': 'success',
            'rule_id': rule_id,
            'enabled': protector.rules[rule_id]['enabled'],
            'message': f'Rule {rule_id} {"enabled" if protector.rules[rule_id]["enabled"] else "disabled"}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rules', methods=['POST'])
def add_rule():
    """Add a new custom rule"""
    try:
        data = request.get_json()
        
        required_fields = ['id', 'name', 'pattern', 'action']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        rule_id = data['id']
        if rule_id in protector.rules:
            return jsonify({'error': f'Rule {rule_id} already exists'}), 400
        
        # Test regex validity
        try:
            re.compile(data['pattern'])
        except re.error as e:
            return jsonify({'error': f'Invalid regex pattern: {e}'}), 400
        
        # Add new rule
        protector.rules[rule_id] = {
            'name': data['name'],
            'pattern': data['pattern'],
            'action': data['action'].upper(),
            'severity': data.get('severity', 'MEDIUM').upper(),
            'enabled': data.get('enabled', True)
        }
        
        return jsonify({
            'status': 'success',
            'message': f'Rule {rule_id} added',
            'rule': protector.rules[rule_id]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rules/reload', methods=['POST'])
def reload_rules():
    """Reload rules from file"""
    try:
        if protector.rules_file and os.path.exists(protector.rules_file):
            # Reset to defaults and reload
            protector.rules = protector.default_rules.copy()
            protector.load_rules_from_file(protector.rules_file)
            
            return jsonify({
                'status': 'success',
                'message': f'Rules reloaded from {protector.rules_file}',
                'rule_count': len(protector.rules)
            })
        else:
            return jsonify({
                'status': 'info',
                'message': 'No rules file configured, using default embedded rules',
                'rule_count': len(protector.rules)
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 🛡️ **PII PROTECTION ENDPOINTS** (same as before but using enhanced protector)

@app.route('/api/pii/check', methods=['POST'])
def check_pii():
    """Check text for PII using current rules"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        endpoint = data.get('endpoint', '/api/unknown')
        user_id = data.get('user_id', 'anonymous')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        result = protector.protect_data(text, endpoint, user_id)
        
        return jsonify({
            'status': 'success',
            'protection_result': result,
            'rules_used': len(protector.get_active_rules())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ... (include all other endpoints from previous version)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check with rule information"""
    active_rules = protector.get_active_rules()
    return jsonify({
        'status': 'healthy',
        'service': 'jimini-pii-protection-advanced',
        'version': '2.0.0',
        'rules_total': len(protector.rules),
        'rules_active': len(active_rules),
        'rules_file': protector.rules_file,
        'audit_entries': len(protector.audit_log),
        'rules_summary': {
            rule_id: {'enabled': rule.get('enabled', True), 'action': rule.get('action')} 
            for rule_id, rule in protector.rules.items()
        }
    })

if __name__ == '__main__':
    print("🛡️ Starting Enhanced Jimini PII Protection Server")
    print(f"📋 Loaded {len(protector.rules)} rules ({len(protector.get_active_rules())} active)")
    if protector.rules_file:
        print(f"📄 Rules source: {protector.rules_file}")
    else:
        print("📄 Rules source: Embedded defaults")
    
    app.run(debug=True, host='0.0.0.0', port=5000)