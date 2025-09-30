import datetime
import uuid
import re
from typing import Dict, Any


def now_iso() -> str:
    """Return current UTC time in ISO 8601 format with milliseconds"""
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="milliseconds") + "Z"


def gen_request_id() -> str:
    """Generate a unique request ID"""
    return f"req_{uuid.uuid4().hex[:12]}"


def redact(text: str) -> str:
    """Redact sensitive information from text"""
    # Redact API keys, tokens, passwords, etc.
    patterns = [
        (r"(api[-_]?key|token|password)=([^&\s]+)", r"\1=REDACTED"),
        (
            r'(api[-_]?key|token|password):\s*["\'`]([^"\'`\s]+)["\'`]',
            r'\1: "REDACTED"',
        ),
        (r"(Authorization|auth):\s*([^\s]+)", r"\1: REDACTED"),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


def safe_serialize(obj: Any) -> Any:
    """Convert types that are not JSON serializable to strings"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "__str__"):
        return str(obj)
    return obj


def dict_to_flat_keys(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Convert a nested dictionary to flat keys with dot notation"""
    result = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(dict_to_flat_keys(v, key))
        else:
            result[key] = v
    return result
