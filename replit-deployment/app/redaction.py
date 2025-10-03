# app/redaction.py
"""
PII redaction and data sanitization for compliance.
Ensures sensitive data doesn't leave the process when USE_PII=false.
"""

import re
import hashlib
from typing import Dict, Any, List, Pattern
from dataclasses import dataclass


@dataclass
class RedactionRule:
    """Redaction rule configuration"""
    name: str
    pattern: Pattern[str]
    replacement: str
    keep_hash: bool = False


class PIIRedactor:
    """
    PII redaction system with configurable rules.
    Supports email, token, UID redaction with optional hashing.
    """
    
    def __init__(self, use_pii: bool = False):
        self.use_pii = use_pii
        self.rules = self._build_redaction_rules()
    
    def _build_redaction_rules(self) -> List[RedactionRule]:
        """Build standard PII redaction rules"""
        return [
            # Email addresses
            RedactionRule(
                name="email",
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement="[EMAIL_REDACTED]",
                keep_hash=True
            ),
            
            # API Keys and tokens (common patterns)
            RedactionRule(
                name="api_key",
                pattern=re.compile(r'\bsk_[A-Za-z0-9]{30,}\b|[A-Za-z0-9]{40,}\b'),
                replacement="[TOKEN_REDACTED]",
                keep_hash=True
            ),
            
            # UUIDs
            RedactionRule(
                name="uuid",
                pattern=re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'),
                replacement="[UUID_REDACTED]",
                keep_hash=True
            ),
            
            # Credit card numbers (basic pattern)
            RedactionRule(
                name="credit_card",
                pattern=re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
                replacement="[CC_REDACTED]",
                keep_hash=False
            ),
            
            # Social Security Numbers (US format)
            RedactionRule(
                name="ssn",
                pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                replacement="[SSN_REDACTED]",
                keep_hash=False
            ),
            
            # Phone numbers (US format)
            RedactionRule(
                name="phone",
                pattern=re.compile(r'\b\d{3}-\d{3}-\d{4}\b|\(\d{3}\)\s?\d{3}-\d{4}\b'),
                replacement="[PHONE_REDACTED]",
                keep_hash=True
            ),
            
            # IP Addresses
            RedactionRule(
                name="ip_address",
                pattern=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
                replacement="[IP_REDACTED]",
                keep_hash=True
            )
        ]
    
    def _generate_hash(self, text: str) -> str:
        """Generate consistent hash for redacted content"""
        return hashlib.sha256(text.encode()).hexdigest()[:8]
    
    def redact_text(self, text: str) -> str:
        """
        Redact PII from text according to USE_PII setting.
        Returns original text if USE_PII=true, redacted if false.
        """
        if self.use_pii:
            return text
        
        if not text or not isinstance(text, str):
            return text
        
        redacted = text
        for rule in self.rules:
            matches = rule.pattern.findall(redacted)
            for match in matches:
                if rule.keep_hash:
                    hash_val = self._generate_hash(match)
                    replacement = f"{rule.replacement}_{hash_val}"
                else:
                    replacement = rule.replacement
                
                redacted = redacted.replace(match, replacement)
        
        return redacted
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively redact PII from dictionary structures.
        Used for event payloads and notifications.
        """
        if self.use_pii:
            return data
        
        if not isinstance(data, dict):
            return data
        
        redacted = {}
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key] = self.redact_text(value)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self.redact_text(item) if isinstance(item, str)
                    else self.redact_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                redacted[key] = value
        
        return redacted
    
    def should_redact(self) -> bool:
        """Check if redaction is enabled (USE_PII=false)"""
        return not self.use_pii
    
    def get_redaction_summary(self) -> Dict[str, Any]:
        """Get summary of redaction configuration"""
        return {
            "pii_processing_enabled": self.use_pii,
            "redaction_rules": [
                {
                    "name": rule.name,
                    "keeps_hash": rule.keep_hash,
                    "replacement": rule.replacement
                }
                for rule in self.rules
            ],
            "total_rules": len(self.rules)
        }


# Global redactor instance (will be initialized with config)
_redactor_instance = None


def get_redactor() -> PIIRedactor:
    """Get global redactor instance"""
    global _redactor_instance
    if _redactor_instance is None:
        from config.loader import get_current_config
        config = get_current_config()
        _redactor_instance = PIIRedactor(use_pii=config.app.use_pii)
    return _redactor_instance


def reset_redactor():
    """Reset redactor instance (for testing)"""
    global _redactor_instance
    _redactor_instance = None