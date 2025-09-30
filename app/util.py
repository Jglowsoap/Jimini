# app/util.py
from __future__ import annotations
from datetime import datetime, timezone
import uuid
import re

def now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()

def gen_request_id() -> str:
    """Generate a unique request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"

def redact(text: str, patterns: list[str] | None = None) -> str:
    """
    Redact sensitive patterns from text.
    Basic implementation for Phase 3.
    """
    if not patterns:
        # Default patterns for common secrets
        patterns = [
            r'sk-[A-Za-z0-9_-]{20,}',  # OpenAI keys
            r'ghp_[A-Za-z0-9]{36}',  # GitHub tokens
            r'AKIA[0-9A-Z]{16}',  # AWS keys
        ]
    
    redacted = text
    for pattern in patterns:
        try:
            redacted = re.sub(pattern, '[REDACTED]', redacted)
        except Exception:
            pass
    
    return redacted
