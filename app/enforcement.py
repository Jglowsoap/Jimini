# app/enforcement.py
from datetime import datetime, timezone
from typing import Dict, Tuple, List, Optional, Any
import fnmatch

from app.models import AuditRecord, Rule
from app.audit import append_audit

# --- LLM policy check using OpenAI v1 SDK (lazy init to avoid noise) ---
_openai_client = None

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
    if not _openai_client:
        return False
    try:
        resp = _openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=50,
            temperature=0,
        )
        answer = (resp.choices[0].message.content or "").strip().lower()
        return answer.startswith("yes")
    except Exception:
        return False

def _regex_hit(compiled_regex: Optional[Any], text: str, min_count: Optional[int]) -> bool:
    """
    Support both search() and findall() with optional min_count threshold.
    """
    if compiled_regex is None:
        return False
    # Try findall first for countable matches; fallback to search.
    try:
        found = compiled_regex.findall(text) if hasattr(compiled_regex, 'findall') else []
        if isinstance(found, list):
            return len(found) >= (min_count or 1)
    except Exception:
        pass
    # Fallback to simple search (min_count treated as 1)
    try:
        return bool(compiled_regex.search(text)) if hasattr(compiled_regex, 'search') else False
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
            rule = entry[0]
            compiled_regex = entry[1] if len(entry) >= 2 else None
        else:
            rule = entry
            compiled_regex = None

        # Only operate if rule is a Rule instance
        if not isinstance(rule, Rule):
            continue

        # Scope by direction and endpoint
        if direction and rule.applies_to and direction not in rule.applies_to:
            continue
        if not _endpoint_matches(rule.endpoints, endpoint):
            continue

        hit = False

        # Regex (with optional min_count)
        if _regex_hit(compiled_regex, text, rule.min_count):
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
