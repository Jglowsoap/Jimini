# app/main.py
import os
from collections import defaultdict, deque
from typing import Any, Dict, Deque

from fastapi import FastAPI, HTTPException

from app.models import EvaluateRequest, EvaluateResponse
from app.rules_loader import load_rules, rules_store
from app.enforcement import evaluate
from app import audit  # Added missing import for audit module
from app.telemetry import emit_decision_span, post_webhook_alert

app = FastAPI(title="Jimini", description="AI Policy Enforcement Gateway")

# Environment variables
API_KEY = os.environ.get("JIMINI_API_KEY", "changeme")
SHADOW_MODE = os.environ.get("JIMINI_SHADOW", "0") == "1"

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


@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate_endpoint(req: EvaluateRequest):
    # Validate API key
    if req.api_key != API_KEY:
        raise HTTPException(401, "Unauthorized")

    decision, rule_ids, enforce_even_in_shadow = evaluate(
        req.text,
        req.agent_id,
        rules_store,
        direction=getattr(req, "direction", None),
        endpoint=getattr(req, "endpoint", None),
    )

    # OTEL span (safe if not configured)
    emit_decision_span(
        agent_id=req.agent_id,
        endpoint=getattr(req, "endpoint", None),
        direction=getattr(req, "direction", None),
        decision=decision,
        rule_ids=rule_ids,
    )

    # Metrics counters
    METRICS_TOTALS[decision] += 1
    for rid in rule_ids:
        METRICS_RULES[rid] += 1
    ep = getattr(req, "endpoint", None)
    if ep is not None:
        METRICS_ENDPOINTS[ep] += 1
    dr = getattr(req, "direction", None)
    if dr is not None:
        METRICS_DIRECTIONS[dr] += 1
    RECENT_DECISIONS.append(
        {
            "agent_id": req.agent_id,
            "decision": decision,
            "rule_ids": rule_ids,
            "excerpt": req.text[:120],
        }
    )

    # Webhook alert for blocks and severe flags (customize as needed)
    if decision == "block" or ("HALLUC-1.0" in rule_ids and decision == "flag"):
        post_webhook_alert(
            agent_id=req.agent_id,
            endpoint=getattr(req, "endpoint", None),
            direction=getattr(req, "direction", None),
            decision=decision,
            rule_ids=rule_ids,
            excerpt=req.text[:200],
        )

    if SHADOW_MODE and decision in ("block", "flag") and not enforce_even_in_shadow:
        METRICS_SHADOW[decision] += 1
        return EvaluateResponse(decision="allow", rule_ids=rule_ids)

    return EvaluateResponse(decision=decision, rule_ids=rule_ids)


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
