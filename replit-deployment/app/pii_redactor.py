"""
Enhanced PII redaction system for comprehensive data protection.
Supports multiple PII types with configurable replacement patterns.
"""

import re
from typing import Dict, List, Pattern, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class PIIType(Enum):
    """Types of PII that can be detected and redacted"""
    SSN = "ssn"
    PHONE = "phone"
    EMAIL = "email"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    IDENTIFIER = "identifier"
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    SSH_KEY = "ssh_key"


@dataclass
class PIIPattern:
    """PII detection pattern configuration"""
    pii_type: PIIType
    pattern: str
    flags: int = re.IGNORECASE
    replacement: Optional[str] = None
    
    def __post_init__(self):
        if self.replacement is None:
            self.replacement = f"[PII:{self.pii_type.value.upper()}]"


class PIIRedactor:
    """Comprehensive PII redaction system"""
    
    def __init__(self):
        self.patterns = self._build_pii_patterns()
        self.compiled_patterns = self._compile_patterns()
    
    def _build_pii_patterns(self) -> List[PIIPattern]:
        """Build comprehensive PII detection patterns"""
        return [
            # Social Security Numbers
            PIIPattern(
                PIIType.SSN,
                r'\b(?:\d{3}[-.\s]?\d{2}[-.\s]?\d{4}|\d{9})\b'
            ),
            
            # Phone Numbers (US/International)
            PIIPattern(
                PIIType.PHONE,
                r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{10})\b'
            ),
            
            # Email Addresses
            PIIPattern(
                PIIType.EMAIL,
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            
            # Credit Card Numbers (Major types)
            PIIPattern(
                PIIType.CREDIT_CARD,
                r'\b(?:4\d{3}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}|'  # Visa
                r'5[1-5]\d{2}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}|'  # MasterCard
                r'3[47]\d{2}[-.\s]?\d{6}[-.\s]?\d{5}|'               # American Express
                r'3[0-9]\d{2}[-.\s]?\d{6}[-.\s]?\d{4}|'              # Diners Club
                r'6(?:011|5\d{2})[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4})\b'  # Discover
            ),
            
            # IP Addresses (IPv4)
            PIIPattern(
                PIIType.IP_ADDRESS,
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            
            # Generic identifiers (license numbers, employee IDs, etc.)
            PIIPattern(
                PIIType.IDENTIFIER,
                r'\b(?:ID|DL|EIN|TIN|SSN|EMP)#?\s*[A-Z0-9]{5,}\b'
            ),
            
            # API Keys (common patterns)
            PIIPattern(
                PIIType.API_KEY,
                r'\b(?:api_key|apikey|access_key|secret_key)[\s=:]+[A-Za-z0-9._-]{16,}\b'
            ),
            
            # JWT Tokens
            PIIPattern(
                PIIType.JWT_TOKEN,
                r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*\b'
            ),
            
            # SSH Private Key indicators
            PIIPattern(
                PIIType.SSH_KEY,
                r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----'
            ),
        ]
    
    def _compile_patterns(self) -> List[Tuple[PIIPattern, Pattern[str]]]:
        """Compile regex patterns for efficiency"""
        compiled = []
        for pattern in self.patterns:
            try:
                regex = re.compile(pattern.pattern, pattern.flags)
                compiled.append((pattern, regex))
            except re.error as e:
                print(f"Warning: Failed to compile PII pattern {pattern.pii_type}: {e}")
        return compiled
    
    def redact(self, text: str, preserve_structure: bool = True) -> str:
        """
        Redact PII from text
        
        Args:
            text: Input text to redact
            preserve_structure: If True, maintain text length/structure when possible
            
        Returns:
            Text with PII redacted
        """
        if not text:
            return text
        
        redacted = text
        
        for pattern_config, compiled_regex in self.compiled_patterns:
            try:
                if preserve_structure:
                    # Replace with same-length placeholder when possible
                    def replacement_func(match):
                        original = match.group(0)
                        replacement = pattern_config.replacement
                        # Try to match length for better structure preservation
                        if len(original) > len(replacement):
                            padding = '*' * (len(original) - len(replacement))
                            return replacement + padding
                        return replacement
                    
                    redacted = compiled_regex.sub(replacement_func, redacted)
                else:
                    redacted = compiled_regex.sub(pattern_config.replacement, redacted)
                    
            except Exception as e:
                print(f"Warning: PII redaction failed for {pattern_config.pii_type}: {e}")
                continue
        
        return redacted
    
    def detect_pii_types(self, text: str) -> Dict[PIIType, int]:
        """
        Detect and count PII types in text without redacting
        
        Returns:
            Dictionary mapping PII types to occurrence counts
        """
        detections = {}
        
        for pattern_config, compiled_regex in self.compiled_patterns:
            try:
                matches = compiled_regex.findall(text)
                if matches:
                    detections[pattern_config.pii_type] = len(matches)
            except Exception:
                continue
        
        return detections
    
    def add_custom_pattern(self, pii_type: PIIType, pattern: str, replacement: str = None):
        """Add a custom PII detection pattern"""
        custom_pattern = PIIPattern(pii_type, pattern, replacement=replacement)
        self.patterns.append(custom_pattern)
        
        # Recompile patterns
        try:
            regex = re.compile(custom_pattern.pattern, custom_pattern.flags)
            self.compiled_patterns.append((custom_pattern, regex))
        except re.error as e:
            print(f"Warning: Failed to compile custom pattern {pii_type}: {e}")
    
    def get_supported_types(self) -> List[PIIType]:
        """Get list of supported PII types"""
        return [pattern.pii_type for pattern in self.patterns]


# Maintain backward compatibility with existing redact.py interface
def build_redactors(rules_store: Dict) -> List[Tuple[str, Pattern[str]]]:
    """
    Legacy interface for rules-based redaction
    Maintains compatibility with existing code
    """
    redact_rules = {
        "OPENAI-KEY-1.0",
        "GITHUB-TOKEN-1.0", 
        "JWT-1.0",
        "SSH-PRIVATE-1.0",
        "PGP-PRIVATE-1.0",
        "AWS-KEY-1.0",
    }
    
    redactors = []
    for rule_id, (rule, compiled) in rules_store.items():
        if rule_id in redact_rules and compiled is not None:
            redactors.append((rule_id, compiled))
    return redactors


def redact(text: str, redactors: List[Tuple[str, Pattern[str]]]) -> str:
    """
    Legacy redaction function for backward compatibility
    """
    redacted = text
    for _, regex in redactors:
        try:
            redacted = regex.sub("[REDACTED]", redacted)
        except Exception:
            pass
    return redacted


# Global PII redactor instance
_global_redactor = None

def get_pii_redactor() -> PIIRedactor:
    """Get global PII redactor instance"""
    global _global_redactor
    if _global_redactor is None:
        _global_redactor = PIIRedactor()
    return _global_redactor


def redact_pii(text: str, preserve_structure: bool = True) -> str:
    """Convenience function for PII redaction"""
    return get_pii_redactor().redact(text, preserve_structure)


def detect_pii(text: str) -> Dict[PIIType, int]:
    """Convenience function for PII detection"""
    return get_pii_redactor().detect_pii_types(text)