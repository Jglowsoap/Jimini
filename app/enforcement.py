# app/enforcement.py
from datetime import datetime, timezone
from typing import Dict, Tuple, List, Optional, Any
import fnmatch

from app.models import AuditRecord, Rule
from app.audit import append_audit

# --- LLM policy check using OpenAI v1 SDK (lazy init to avoid noise) ---
_openai_client: Optional[Any] = None

def _ensure_openai():
    """Lazy-initialize the OpenAI client; mark as unavailable on failure."""
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI  # pip install openai
            _openai_client = OpenAI()  # reads OPENAI_API_KEY
        except Exception:
            _openai_client = False  # mark unavailable (no warning spam)

def llm_policy_check(text: str, prompt: str, model: str = "gpt-4o-mini") -> bool:
    """
    Returns True when the LLM indicates the text violates the policy (e.g., answers 'Yes').
    Fail-safe: returns False if the client isn't available or the call errors.
    """
    _ensure_openai()
    if _openai_client is False:
        return False
    try:
        # Defensive: check if _openai_client has expected attributes
        chat = getattr(_openai_client, "chat", None)
        if chat is None or not hasattr(chat, "completions"):
            return False
        completions = getattr(chat, "completions", None)
        if completions is None or not hasattr(completions, "create"):
            return False
        resp = completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=50,
            temperature=0,
        )  # type: ignore
        # Defensive: choices/message/content
        choices = getattr(resp, "choices", None)
        if not choices or not hasattr(choices[0], "message"):
            return False
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", "")
        answer = (content or "").strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False

import re
def _regex_hit(compiled_regex: Optional[re.Pattern[str]], text: str, min_count: Optional[int]) -> bool:
    """
    Prefer search() for a quick yes/no. Only count with findall() when a min_count
    threshold is explicitly requested.
    """
    if compiled_regex is None:
        return False
    try:
        # If a threshold is requested (>1), count matches.
        if min_count and int(min_count) > 1:
            return len(compiled_regex.findall(text)) >= int(min_count)
        # Otherwise, a single hit is enough.
        return compiled_regex.search(text) is not None
    except Exception as re_err:
        print(f"[Jimini] Regex error: {re_err}")
        return False

def _endpoint_matches(rule_endpoints: Optional[List[str]], endpoint: Optional[str]) -> bool:
    """
    True if rule_endpoints is None (no restriction), or endpoint matches:
    - exact string
    - prefix match (rule endswith '/*' and endpoint startswith prefix)
    - glob pattern via fnmatch (supports '*' and '?')
    """
    if not rule_endpoints:  # None or empty => no restriction
        return True
    if not endpoint:
        return False
    for pat in rule_endpoints:
        # explicit prefix support
        if pat.endswith("/*") and endpoint.startswith(pat[:-2]):
            return True
        # glob support (e.g., "/api/cjis/*", "/api/*/export")
        if fnmatch.fnmatch(endpoint, pat):
            return True
        # exact
        if endpoint == pat:
            return True
    return False

def evaluate(
    text: str,
    agent_id: str,
    rules_store: Dict[str, Any],
    direction: Optional[str] = None,
    endpoint: Optional[str] = None,
):
    """
    Evaluate text against rules. Each store entry is typically (Rule, compiled_regex),
    but we tolerate (Rule,), (Rule, regex, ...extras), or just Rule.

    Supports: regex, min_count, max_chars, llm_prompt, and scoping by direction/endpoint.

    Returns: (decision, rule_ids, enforce_even_in_shadow)
    """
    matched: List[Tuple[Rule, str]] = []

    # normalize direction to avoid case mismatches
    if direction:
        direction = direction.lower().strip()

    # 1) Collect matches (robust unpacking)
    for rid, entry in rules_store.items():
        # tolerate shapes: (Rule,), (Rule, regex), (Rule, regex, extras), or just Rule
        if isinstance(entry, tuple):
            rule = entry[0]  # type: ignore
            compiled_regex = entry[1] if len(entry) >= 2 else None  # type: ignore
        else:
            rule = entry
            compiled_regex = None

        # Accept any object with an 'action' attribute (for testing flexibility)
        if not hasattr(rule, "action"):
            continue

        # Scope by direction and endpoint
        if direction and rule.applies_to and direction not in rule.applies_to:
            continue
        if not _endpoint_matches(rule.endpoints, endpoint):
            continue

        hit = False

        # Regex (with optional min_count)
        import re
        regex_arg: Optional[re.Pattern[str]] = compiled_regex if isinstance(compiled_regex, re.Pattern) else None
        if _regex_hit(regex_arg, text, rule.min_count):
            hit = True

        # Length threshold
        max_chars = rule.max_chars
        if not hit and max_chars is not None:
            try:
                max_chars_int = int(max_chars)
            except (TypeError, ValueError):
                max_chars_int = None
            if max_chars_int is not None and len(text) > max_chars_int:
                hit = True

        # LLM policy check (only if still no hit and rule has llm_prompt)
        if not hit and rule.llm_prompt:
            if llm_policy_check(text, rule.llm_prompt):
                hit = True

        if hit:
            matched.append((rule, rid))

    # 2) Suppress generic API-1.0 if a specific secret matched
    SPECIFIC_SECRET_IDS = {
        "GITHUB-TOKEN-1.0",
        "AWS-ACCESS-KEY-1.0",
        "AWS-SECRET-KEY-1.0",
        "OPENAI-KEY-1.0",
        "SLACK-BOT-1.0",
        "GOOGLE-API-KEY-1.0",
        "STRIPE-KEY-1.0",
        "JWT-1.0",
    }
    matched_ids = {rid for _, rid in matched}
    if "API-1.0" in matched_ids and (matched_ids & SPECIFIC_SECRET_IDS):
        matched = [(r, r_id) for (r, r_id) in matched if r_id != "API-1.0"]

    # 3) Decision precedence (block > flag > allow)
    if any(r.action == "block" for r, _ in matched):
        decision = "block"
    elif any(r.action == "flag" for r, _ in matched):
        decision = "flag"
    else:
        decision = "allow"

    rule_ids = [r_id for _, r_id in matched]

    # 4) Per-rule shadow override: enforce even when global shadow mode is on
    enforce_even_in_shadow = any(
        getattr(r, "shadow_override", None) == "enforce" for r, _ in matched
    )

    # 5) Audit
    record = AuditRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),        agent_id=agent_id,
        decision=decision,
        rule_ids=rule_ids,
        excerpt=text[:200],
    )
    append_audit(record)

    return decision, rule_ids, enforce_even_in_shadow
