# app/main.py
from collections import defaultdict, deque
import time
import os
from typing import Any, Dict, Deque

from fastapi import FastAPI, HTTPException
import urllib.request
import json

from app.models import EvaluateRequest, EvaluateResponse
from app.rules_loader import load_rules, rules_store
from app.enforcement import evaluate
from app import audit
from app.config import get_config
from app.telemetry import Telemetry, TelemetryEvent
from app.util import now_iso, gen_request_id

# Initialize FastAPI and global variables
app = FastAPI(title="Jimini", description="AI Policy Enforcement Gateway")
telemetry = Telemetry.instance()
cfg = get_config()

# Constants for shadow mode behavior
SHADOW_MODE = os.environ.get("JIMINI_SHADOW", "0") == "1"
METRICS_SHADOW = defaultdict(int)  # Track shadow decisions

# Environment variables
API_KEY = os.environ.get("JIMINI_API_KEY", "changeme")

# simple in-memory metrics
METRICS_TOTALS: Dict[str, int] = defaultdict(int)
METRICS_RULES: Dict[str, int] = defaultdict(int)
METRICS_SHADOW: Dict[str, int] = defaultdict(int)
METRICS_ENDPOINTS: Dict[str, int] = defaultdict(int)
METRICS_DIRECTIONS: Dict[str, int] = defaultdict(int)
RECENT_DECISIONS: Deque[Dict[str, Any]] = deque(maxlen=100)


# Load rules on startup
@app.on_event("startup")
async def startup_event():
    rules_path = os.environ.get("JIMINI_RULES_PATH", "policy_rules.yaml")
    load_rules(rules_path)
    print(f"Loaded {len(rules_store)} rules.")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "shadow": SHADOW_MODE, "loaded_rules": int(len(rules_store))}


def determine_shadow_enforcement(rule_ids):
    """Determine if a rule should be enforced even in shadow mode."""
    # Look for rules with shadow_override: enforce
    for rule_id in rule_ids:
        rule = next((r for r in rules_store if r.id == rule_id), None)
        if rule and rule.shadow_override == "enforce":
            return True
    return False


def apply_shadow_logic(decision: str, rule_ids: list) -> tuple:
    """Apply shadow mode logic to decision

    Args:
        decision: The original decision (BLOCK, FLAG, ALLOW)
        rule_ids: List of rule IDs that triggered

    Returns:
        tuple: (original_decision, effective_decision)
    """
    # Check if any rule is in shadow_overrides
    enforce_even_in_shadow = any(r in cfg.app.shadow_overrides for r in rule_ids)

    # Shadow override logic
    if cfg.app.shadow_mode and decision.upper() in ("BLOCK", "FLAG") and not enforce_even_in_shadow:
        return decision, "ALLOW"
    else:
        return decision, decision


def post_webhook_alert(
    agent_id=None, endpoint=None, action=None, rule_ids=None, text_excerpt=None
):
    """Send webhook alert for blocked content or severe flags."""
    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        return

    payload = {
        "text": f"*Jimini Alert* - {action}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Policy violation detected*\nAction: `{action}`\nEndpoint: `{endpoint}`\nAgent: `{agent_id or 'n/a'}`\nRules: {', '.join(rule_ids or [])}",
                },
            }
        ],
    }

    if text_excerpt:
        payload["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Excerpt*:\n```{text_excerpt[:200]}```",
                },
            }
        )

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as _:
            pass
    except Exception:
        # Don't let webhook failures impact the API response
        pass


@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate_text(request: EvaluateRequest):
    """Evaluate text against policy rules and return decision."""
    request_id = request.request_id or gen_request_id()
    t0 = time.perf_counter()

    # Check API key
    api_key = request.api_key
    if api_key != os.environ.get("JIMINI_API_KEY", "changeme"):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Inbound telemetry
    telemetry.record_event(
        TelemetryEvent(
            ts=now_iso(),
            endpoint="/v1/evaluate",
            direction="inbound",
            decision="SHADOW" if cfg.app.shadow_mode else "ALLOW",
            shadow_mode=cfg.app.shadow_mode,
            rule_ids=[],
            request_id=request_id,
        )
    )

    # Call existing evaluate function
    result = evaluate(rules_store, request, request_id)

    latency = round((time.perf_counter() - t0) * 1000, 2)
    decision = result.action.upper()  # Convert to uppercase
    rule_ids = result.rule_ids

    # Apply shadow logic
    raw_decision, effective_decision = apply_shadow_logic(decision, rule_ids)

    # Record outbound telemetry
    telemetry_decision = effective_decision
    if (
        cfg.app.shadow_mode
        and effective_decision == "ALLOW"
        and raw_decision != "ALLOW"
    ):
        telemetry_decision = "SHADOW"  # Mark as shadow decision for telemetry

    telemetry.record_event(
        TelemetryEvent(
            ts=now_iso(),
            endpoint="/v1/evaluate",
            direction="outbound",
            decision=telemetry_decision,
            shadow_mode=cfg.app.shadow_mode,
            rule_ids=rule_ids,
            request_id=request_id,
            latency_ms=latency,
            meta={"raw_decision": raw_decision},
        )
    )

    # Webhook alert for blocks and severe flags (customize as needed)
    if decision == "block" or ("HALLUC-1.0" in rule_ids and decision == "flag"):
        post_webhook_alert(
            agent_id=request.agent_id,
            endpoint=getattr(request, "endpoint", None),
            action=decision,
            rule_ids=rule_ids,
            text_excerpt=request.text[:500] if hasattr(request, "text") else None,
        )

    # Make sure we call flush to ensure events are written
    telemetry.flush()

    # Construct response with shadow mode info
    return {
        "action": effective_decision.lower(),  # Convert back to lowercase for API consistency
        "rule_ids": rule_ids,
        "message": result.message,
        "request_id": request_id,
        "latency_ms": latency,
        "shadow_mode": cfg.app.shadow_mode,
        "raw_action": result.action,
    }


@app.get("/v1/metrics")
async def metrics() -> Dict[str, Any]:
    return {
        "shadow_mode": SHADOW_MODE,
        "totals": dict(METRICS_TOTALS),
        "rules": dict(METRICS_RULES),
        "shadow_overrides": dict(METRICS_SHADOW),
        "endpoints": dict(METRICS_ENDPOINTS),
        "directions": dict(METRICS_DIRECTIONS),
        "recent": list(RECENT_DECISIONS),
        "loaded_rules": len(rules_store),
    }


@app.get("/v1/audit/verify")
async def audit_verify() -> Dict[str, Any]:
    return audit.verify_chain()  # Use audit module to access verify_chain function


@app.get("/v1/audit/sarif")
async def audit_sarif(date_prefix: str = None):
    """Return audit logs in SARIF format."""
    records = audit.get_records_by_date_prefix(date_prefix)

    # Convert audit records to SARIF results
    results = []
    for record in records:
        if record.action in ["block", "flag"]:
            results.append(
                {
                    "ruleId": "+".join(record.rule_ids)
                    if record.rule_ids
                    else "unknown",
                    "level": "error" if record.action == "block" else "warning",
                    "message": {
                        "text": f"Content {'blocked' if record.action == 'block' else 'flagged'} due to policy violation."
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": record.endpoint},
                                "region": {"snippet": {"text": record.text_excerpt}},
                            }
                        }
                    ],
                }
            )

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "Jimini"}}, "results": results}],
    }


# Add telemetry endpoints
@app.get("/v1/telemetry/counters")
async def telemetry_counters():
    """Return current telemetry counters."""
    return telemetry.snapshot_counters()


@app.get("/v1/telemetry/flush")
async def telemetry_flush():
    """Force flush of telemetry events."""
    telemetry.flush()
    return {"status": "ok", "message": "Telemetry events flushed"}
    return telemetry.snapshot_counters()


@app.get("/v1/telemetry/flush")
async def telemetry_flush():
    """Force flush of telemetry events."""
    telemetry.flush()
    return {"status": "ok", "message": "Telemetry events flushed"}
