# app/main.py
import os
import time
from collections import defaultdict, deque
from datetime import date
from typing import Any, Dict, List, Optional, Tuple, Deque

from fastapi import FastAPI, HTTPException
from app.config import API_KEY, RULES_PATH, get_config
from app.rules_loader import RulesHandler
from app.enforcement import evaluate
from app.models import EvaluateRequest, EvaluateResponse
from app.audit import verify_chain, iter_audits
from app.telemetry import emit_decision_span, post_webhook_alert, Telemetry, TelemetryEvent
from app.util import now_iso, gen_request_id

app = FastAPI()

from app.models import Rule
rules_store: Dict[str, Tuple[Rule, object]] = {}
RulesHandler(RULES_PATH, rules_store)

# Load config and initialize telemetry
cfg = get_config()
telemetry = Telemetry.instance()

# Legacy shadow mode from env (for backward compatibility)
SHADOW: bool = cfg.app.shadow_mode or (os.getenv("JIMINI_SHADOW") == "1")

# simple in-memory metrics
METRICS_TOTALS: Dict[str, int] = defaultdict(int)
METRICS_RULES: Dict[str, int] = defaultdict(int)
METRICS_SHADOW: Dict[str, int] = defaultdict(int)
METRICS_ENDPOINTS: Dict[str, int] = defaultdict(int)
METRICS_DIRECTIONS: Dict[str, int] = defaultdict(int)
RECENT_DECISIONS: Deque[Dict[str, Any]] = deque(maxlen=100)

@app.post('/v1/evaluate', response_model=EvaluateResponse)
async def evaluate_endpoint(req: EvaluateRequest):
    if req.api_key != API_KEY:
        raise HTTPException(401, 'Unauthorized')

    request_id = gen_request_id()
    t0 = time.perf_counter()
    
    # Inbound telemetry
    telemetry.record_event(TelemetryEvent(
        ts=now_iso(), 
        endpoint="/v1/evaluate", 
        direction="inbound",
        decision="SHADOW" if SHADOW else "ALLOW",
        shadow_mode=SHADOW, 
        rule_ids=[],
        request_id=request_id
    ))

    # Evaluate
    decision, rule_ids, enforce_even_in_shadow = evaluate(
        req.text, req.agent_id, rules_store,
        direction=getattr(req, "direction", None),
        endpoint=getattr(req, "endpoint", None)
    )

    latency = round((time.perf_counter() - t0) * 1000, 2)

    # Shadow override: enforce if any rule is in overrides
    shadow_overrides = cfg.app.shadow_overrides
    if SHADOW and any(r in shadow_overrides for r in rule_ids):
        decision_effective = decision  # enforce
    elif SHADOW:
        decision_effective = "ALLOW" if decision in ("BLOCK", "FLAG") else decision
    else:
        decision_effective = decision

    # Outbound telemetry
    telemetry.record_event(TelemetryEvent(
        ts=now_iso(), 
        endpoint="/v1/evaluate", 
        direction="outbound",
        decision=decision_effective if not SHADOW else (
            decision_effective if decision_effective in ("BLOCK", "FLAG") else "SHADOW"
        ),
        shadow_mode=SHADOW, 
        rule_ids=rule_ids,
        request_id=request_id, 
        latency_ms=latency,
        meta={"raw_decision": decision}
    ))

    # Legacy OTEL span (safe if not configured)
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
    RECENT_DECISIONS.append({
        "agent_id": req.agent_id,
        "decision": decision,
        "rule_ids": rule_ids,
        "excerpt": req.text[:120],
    })

    # Legacy webhook alert for blocks and severe flags
    if decision == "block" or ("HALLUC-1.0" in rule_ids and decision == "flag"):
        post_webhook_alert(
            agent_id=req.agent_id,
            endpoint=getattr(req, "endpoint", None),
            direction=getattr(req, "direction", None),
            decision=decision,
            rule_ids=rule_ids,
            excerpt=req.text[:200],
        )

    # Apply shadow mode logic (legacy)
    if SHADOW and decision in ("block", "flag"):
        # Check shadow overrides
        if any(r in shadow_overrides for r in rule_ids):
            # Enforce even in shadow
            pass
        elif not enforce_even_in_shadow:
            METRICS_SHADOW[decision] += 1
            return EvaluateResponse(decision="allow", rule_ids=rule_ids)

    return EvaluateResponse(decision=decision_effective, rule_ids=rule_ids)

@app.get("/v1/metrics")
async def metrics() -> Dict[str, Any]:
    return {
        "shadow_mode": SHADOW,
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
    return verify_chain()  # already returns a Dict[str, Any]

@app.get("/v1/audit/sarif")
async def audit_sarif(date_prefix: Optional[str] = None) -> Dict[str, Any]:
    """
    Minimal SARIF view of audit results.
    Filter by day with ?date_prefix=YYYY-MM-DD (defaults to today).
    """
    if not date_prefix:
        date_prefix = date.today().isoformat()

    results: List[Dict[str, Any]] = []
    for rec in iter_audits() or []:
        if not rec.timestamp.startswith(date_prefix):
            continue
        level = "error" if rec.decision == "block" else ("warning" if rec.decision == "flag" else "note")
        for rid in rec.rule_ids:
            results.append({
                "ruleId": rid,
                "level": level,
                "message": {"text": f"{rec.decision} by {rid} for {rec.agent_id}"},
            })

    return {
        "version": "2.1.0",
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "runs": [{"tool": {"driver": {"name": "Jimini"}}, "results": results}],
    }

@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "shadow": SHADOW, "loaded_rules": int(len(rules_store))}
