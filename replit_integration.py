"""
Jimini Replit Integration
========================

This module provides easy integration between your Replit dashboard 
and Jimini's PII protection service.
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class JiminiMonitor:
    """
    Jimini monitoring layer for Replit dashboards.
    
    This class provides all the functionality you need to protect
    citizen PII data in your government dashboard.
    """
    
    def __init__(self, 
                 api_url: str = "http://localhost:9000",
                 api_key: str = "changeme",
                 timeout: int = 5):
        """
        Initialize Jimini monitor.
        
        Args:
            api_url: Jimini service URL
            api_key: API key for authentication  
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
    def protect_data(self, 
                    data: str, 
                    endpoint: str = "/dashboard/data",
                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check data for PII and get protection decision.
        
        Args:
            data: The text/data to check for PII
            endpoint: The dashboard endpoint being accessed
            user_id: Optional user identifier
            
        Returns:
            Dictionary with decision, rule_ids, and any redacted text
        """
        try:
            payload = {
                "text": data,
                "agent_id": f"replit_dashboard_{user_id or 'anonymous'}",
                "direction": "outbound",
                "endpoint": endpoint,
                "api_key": self.api_key
            }
            
            response = requests.post(
                f"{self.api_url}/v1/evaluate",
                headers={
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"PII check: {result.get('decision', 'UNKNOWN')} for endpoint {endpoint}")
                return result
            else:
                error_msg = f"Jimini API error: {response.status_code}"
                self.logger.error(error_msg)
                return {
                    "decision": "ALLOW",  # Fail-safe: allow on API error
                    "error": error_msg,
                    "rule_ids": []
                }
                
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Jimini service"
            self.logger.error(error_msg)
            return {
                "decision": "ALLOW",  # Fail-safe: allow if service unavailable
                "error": error_msg,
                "rule_ids": []
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "decision": "ALLOW",  # Fail-safe
                "error": error_msg,
                "rule_ids": []
            }
    
    def check_citizen_data(self, citizen_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Specifically check citizen data for government PII.
        
        Args:
            citizen_data: Dictionary containing citizen information
            
        Returns:
            Protection result with redacted data if needed
        """
        # Convert citizen data to text for PII scanning
        text_to_scan = ""
        for key, value in citizen_data.items():
            text_to_scan += f"{key}: {value}, "
        
        result = self.protect_data(text_to_scan, "/citizen/lookup")
        
        # If blocked or flagged, redact the sensitive data
        if result.get('decision') in ['BLOCK', 'FLAG']:
            redacted_data = self._redact_pii(citizen_data, result.get('rule_ids', []))
            result['redacted_data'] = redacted_data
        else:
            result['redacted_data'] = citizen_data
            
        return result
    
    def _redact_pii(self, data: Dict[str, Any], rule_ids: list) -> Dict[str, Any]:
        """Redact PII based on triggered rules."""
        redacted = data.copy()
        
        for rule_id in rule_ids:
            if 'SSN' in rule_id:
                if 'ssn' in redacted:
                    redacted['ssn'] = "***-**-****"
                if 'social_security' in redacted:
                    redacted['social_security'] = "***-**-****"
                    
            elif 'DRIVER' in rule_id or 'LICENSE' in rule_id:
                if 'drivers_license' in redacted:
                    redacted['drivers_license'] = "D*******"
                if 'license_number' in redacted:
                    redacted['license_number'] = "D*******"
                    
            elif 'ADDRESS' in rule_id:
                if 'address' in redacted:
                    redacted['address'] = "[REDACTED ADDRESS]"
                if 'home_address' in redacted:
                    redacted['home_address'] = "[REDACTED ADDRESS]"
                    
            elif 'PHONE' in rule_id:
                if 'phone' in redacted:
                    redacted['phone'] = "***-***-****"
                if 'phone_number' in redacted:
                    redacted['phone_number'] = "***-***-****"
        
        return redacted
    
    def is_service_healthy(self) -> bool:
        """Check if Jimini service is running and healthy."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def get_protection_stats(self) -> Dict[str, Any]:
        """Get protection statistics from Jimini service."""
        try:
            response = requests.get(f"{self.api_url}/v1/metrics", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get stats: {response.status_code}"}
        except Exception as e:
            return {"error": f"Cannot get stats: {str(e)}"}

# Decorator for automatic PII protection
def protect_pii(endpoint: str = "/dashboard/default", monitor: Optional[JiminiMonitor] = None):
    """
    Decorator to automatically protect function outputs from PII exposure.
    
    Usage:
        @protect_pii("/citizen/lookup")
        def get_citizen_info(citizen_id):
            return {"name": "John Doe", "ssn": "123-45-6789"}
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if monitor is None:
                # Use default monitor
                default_monitor = JiminiMonitor()
            else:
                default_monitor = monitor
            
            # Convert result to string for PII checking
            if isinstance(result, dict):
                text_to_check = json.dumps(result)
            elif isinstance(result, str):
                text_to_check = result
            else:
                text_to_check = str(result)
            
            protection_result = default_monitor.protect_data(text_to_check, endpoint)
            
            # Log the protection decision
            decision = protection_result.get('decision', 'UNKNOWN')
            logging.info(f"PII Protection: {decision} for {func.__name__}() -> {endpoint}")
            
            # If blocked, return safe response
            if decision == 'BLOCK':
                return {
                    "error": "Data contains sensitive PII and has been blocked",
                    "decision": "BLOCK",
                    "timestamp": datetime.now().isoformat()
                }
            
            # If flagged, return with warning
            elif decision == 'FLAG':
                if isinstance(result, dict):
                    result['_pii_warning'] = "This data contains PII and has been logged"
                
            return result
        
        return wrapper
    return decorator

# Simple integration functions for common use cases
def quick_pii_check(text: str, api_key: str = "changeme") -> str:
    """
    Quick PII check function for simple integrations.
    
    Args:
        text: Text to check for PII
        api_key: Jimini API key
        
    Returns:
        "BLOCK", "FLAG", or "ALLOW"
    """
    monitor = JiminiMonitor(api_key=api_key)
    result = monitor.protect_data(text)
    return result.get('decision', 'ALLOW')

def protect_citizen_record(record: Dict[str, Any], api_key: str = "changeme") -> Dict[str, Any]:
    """
    Protect a citizen record from PII exposure.
    
    Args:
        record: Citizen data dictionary
        api_key: Jimini API key
        
    Returns:
        Protected/redacted record
    """
    monitor = JiminiMonitor(api_key=api_key)
    result = monitor.check_citizen_data(record)
    return result.get('redacted_data', record)

# Example usage for Replit dashboard
if __name__ == "__main__":
    # Initialize monitor
    jimini = JiminiMonitor()
    
    # Test citizen data protection
    test_citizen = {
        "name": "John Doe",
        "ssn": "123-45-6789", 
        "address": "123 Main Street, Anytown, ST 12345",
        "drivers_license": "D12345678",
        "phone": "555-123-4567"
    }
    
    print("🛡️ Testing Citizen Data Protection...")
    result = jimini.check_citizen_data(test_citizen)
    
    print(f"Decision: {result.get('decision')}")
    print(f"Rules Triggered: {result.get('rule_ids')}")
    print(f"Original Data: {test_citizen}")
    print(f"Protected Data: {result.get('redacted_data')}")
    
    # Test service health
    print(f"\n📡 Jimini Service Health: {'✅ Online' if jimini.is_service_healthy() else '❌ Offline'}")