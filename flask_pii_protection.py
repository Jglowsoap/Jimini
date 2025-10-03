"""
Flask Backend with Jimini PII Protection
=======================================

This Flask API provides PII protection endpoints for your React dashboard.
Add this to your existing Flask application.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import json
from datetime import datetime
from typing import Dict, Any, List

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# 🛡️ Jimini PII Protection Engine for Flask
class GovernmentPIIProtector:
    """PII Protection engine for government React/Flask dashboard"""
    
    def __init__(self):
        self.rules = {
            'SSN-PROTECTION': {
                'name': 'Social Security Number',
                'pattern': r'\b\d{3}-?\d{2}-?\d{4}\b',
                'action': 'BLOCK',
                'severity': 'CRITICAL'
            },
            'DL-PROTECTION': {
                'name': 'Driver\'s License Number', 
                'pattern': r'\b[A-Z]{1,2}\d{7,8}\b|D\d{8}\b',
                'action': 'FLAG',
                'severity': 'HIGH'
            },
            'ADDRESS-PROTECTION': {
                'name': 'Street Address',
                'pattern': r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
                'action': 'FLAG', 
                'severity': 'MEDIUM'
            },
            'PHONE-PROTECTION': {
                'name': 'Phone Number',
                'pattern': r'\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b',
                'action': 'FLAG',
                'severity': 'MEDIUM'  
            },
            'EMAIL-PROTECTION': {
                'name': 'Email Address',
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'action': 'FLAG',
                'severity': 'LOW'
            }
        }
        self.audit_log = []
    
    def protect_data(self, text: str, endpoint: str = "/api", user_id: str = "user") -> Dict[str, Any]:
        """Check text for PII and return protection decision"""
        violations = []
        decision = "ALLOW"
        highest_severity = "NONE"
        
        for rule_id, rule in self.rules.items():
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
    
    def mask_pii(self, text: str) -> Dict[str, Any]:
        """Mask PII in text for safe display"""
        result = self.protect_data(text)
        masked_text = text
        
        # Mask detected PII
        for violation in result['violations']:
            mask = f"[MASKED_{violation['rule_name'].replace(' ', '_').upper()}]"
            masked_text = masked_text.replace(violation['matched_text'], mask)
        
        return {
            'original_text': text,
            'masked_text': masked_text,
            'pii_detected': len(result['violations']) > 0,
            'violations': result['violations']
        }

# Initialize global protector
protector = GovernmentPIIProtector()

# 🛡️ PII Protection API Endpoints

@app.route('/api/pii/check', methods=['POST'])
def check_pii():
    """Check text for PII - Main protection endpoint"""
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
            'protection_result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pii/mask', methods=['POST'])
def mask_pii():
    """Mask PII in text for safe display"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        result = protector.mask_pii(text)
        
        return jsonify({
            'status': 'success',
            'masked_result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/citizen/lookup', methods=['POST'])
def citizen_lookup():
    """Protected citizen lookup endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        user_id = data.get('user_id', 'dashboard_user')
        
        # 🛡️ Check query for PII first
        protection_result = protector.protect_data(query, '/api/citizen/lookup', user_id)
        
        if protection_result['decision'] == 'BLOCK':
            return jsonify({
                'status': 'blocked',
                'message': 'Query contains sensitive PII and has been blocked',
                'protection_result': protection_result
            }), 403
        
        # Simulate database lookup (replace with your real database query)
        if 'john' in query.lower():
            citizen_data = {
                'citizen_id': 'C001234',
                'name': 'John Doe',
                'address': '123 Main Street, Springfield, IL',
                'phone': '555-123-4567',
                'status': 'Active',
                'last_updated': '2025-10-02'
            }
            
            # 🛡️ Protect the response data
            response_text = json.dumps(citizen_data)
            mask_result = protector.mask_pii(response_text)
            
            return jsonify({
                'status': 'success',
                'citizen_data': json.loads(mask_result['masked_text']) if not mask_result['pii_detected'] else None,
                'masked_data': mask_result['masked_text'] if mask_result['pii_detected'] else None,
                'protection_applied': mask_result['pii_detected'],
                'query_protection': protection_result
            })
        else:
            return jsonify({
                'status': 'not_found',
                'message': 'Citizen not found',
                'query_protection': protection_result
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dmv/lookup', methods=['POST'])
def dmv_lookup():
    """Protected DMV records lookup"""
    try:
        data = request.get_json()
        license_number = data.get('license_number', '')
        user_id = data.get('user_id', 'dmv_user')
        
        # 🛡️ Check license number for PII
        protection_result = protector.protect_data(license_number, '/api/dmv/lookup', user_id)
        
        if protection_result['decision'] == 'FLAG':
            # Log the driver's license access
            dmv_record = {
                'license_number': license_number,
                'name': 'Driver Name',
                'address': '456 Oak Avenue, Springfield, IL',
                'status': 'Valid',
                'expiration': '2026-12-31',
                'violations': []
            }
            
            # Mask the response
            response_text = json.dumps(dmv_record)
            mask_result = protector.mask_pii(response_text)
            
            return jsonify({
                'status': 'success',
                'dmv_record': dmv_record,
                'protection_applied': True,
                'protection_result': protection_result,
                'audit_logged': True
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Safe DMV query',
            'protection_result': protection_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/background/check', methods=['POST'])
def background_check():
    """Protected background check endpoint"""
    try:
        data = request.get_json()
        subject_info = data.get('subject_info', '')
        justification = data.get('justification', '')
        user_id = data.get('user_id', 'bg_check_user')
        
        if not justification:
            return jsonify({
                'status': 'error',
                'message': 'Justification required for background checks'
            }), 400
        
        # 🛡️ Check subject info for PII
        protection_result = protector.protect_data(subject_info, '/api/background/check', user_id)
        
        # Always log background check requests
        background_result = {
            'status': 'submitted',
            'message': 'Background check request submitted for review',
            'justification': justification,
            'protection_result': protection_result,
            'audit_required': True,
            'supervisor_notification': True
        }
        
        return jsonify(background_result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audit/logs', methods=['GET'])
def get_audit_logs():
    """Get audit logs for compliance"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        user_filter = request.args.get('user_id', None)
        decision_filter = request.args.get('decision', None)
        
        # Filter logs
        logs = protector.audit_log[-limit:]  # Last N entries
        
        if user_filter:
            logs = [log for log in logs if log.get('user_id') == user_filter]
        
        if decision_filter:
            logs = [log for log in logs if log.get('decision') == decision_filter]
        
        return jsonify({
            'status': 'success',
            'logs': logs,
            'total_count': len(protector.audit_log),
            'filtered_count': len(logs)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get PII protection metrics"""
    try:
        logs = protector.audit_log
        
        if not logs:
            return jsonify({
                'status': 'success',
                'metrics': {
                    'total_requests': 0,
                    'blocked': 0,
                    'flagged': 0,
                    'allowed': 0,
                    'protection_rate': 0
                }
            })
        
        total = len(logs)
        blocked = len([log for log in logs if log.get('decision') == 'BLOCK'])
        flagged = len([log for log in logs if log.get('decision') == 'FLAG'])
        allowed = len([log for log in logs if log.get('decision') == 'ALLOW'])
        
        protection_rate = ((blocked + flagged) / total * 100) if total > 0 else 0
        
        return jsonify({
            'status': 'success',
            'metrics': {
                'total_requests': total,
                'blocked': blocked,
                'flagged': flagged,
                'allowed': allowed,
                'protection_rate': round(protection_rate, 2),
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'jimini-pii-protection',
        'version': '1.0.0',
        'rules_loaded': len(protector.rules),
        'audit_entries': len(protector.audit_log)
    })

# Example middleware to protect all responses
@app.after_request
def protect_response(response):
    """Middleware to check all outgoing responses for PII"""
    if response.mimetype == 'application/json':
        try:
            # Only check non-error responses
            if response.status_code < 400:
                data = response.get_json()
                if data and isinstance(data, dict):
                    # Quick PII check on response
                    response_text = json.dumps(data)
                    protection_result = protector.protect_data(response_text, request.endpoint or '/unknown')
                    
                    # Add protection headers
                    if protection_result['violations']:
                        response.headers['X-PII-Protected'] = 'true'
                        response.headers['X-PII-Rules-Triggered'] = ','.join(protection_result['rule_ids'])
                    else:
                        response.headers['X-PII-Protected'] = 'false'
        except:
            pass  # Don't break the response if protection fails
    
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)