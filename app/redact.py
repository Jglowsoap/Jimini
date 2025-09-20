# app/redact.py
from __future__ import annotations
import re
from typing import List, Tuple, Dict, Pattern, Any

# Provide the rule IDs that should be redacted (not just blocked)
REDACT_RULES = {
    "OPENAI-KEY-1.0",
    "GITHUB-TOKEN-1.0",
    "JWT-1.0",
    "SSH-PRIVATE-1.0",
    "PGP-PRIVATE-1.0",
    "AWS-KEY-1.0",
}

def build_redactors(
    rules_store: Dict[str, Tuple[Any, Pattern[str] | None]]  # Typically Dict[str, Tuple[Rule, Pattern[str] | None]]
) -> List[Tuple[str, Pattern[str]]]:
    redactors: List[Tuple[str, Pattern[str]]] = []
    for rid, (rule, compiled) in rules_store.items():
        if rid in REDACT_RULES and compiled is not None:
            redactors.append((rid, compiled))
    return redactors

def redact(text: str, redactors: List[Tuple[str, "re.Pattern[str]"]]) -> str:
    redacted = text
    for _, cregex in redactors:
        try:
            redacted = cregex.sub("[REDACTED]", redacted)
        except Exception:
            pass
    return redacted
