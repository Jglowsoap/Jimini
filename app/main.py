# app/main.py
import os
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from app.config import API_KEY, RULES_PATH
from app.rules_loader import RulesHandler
from app.enforcement import evaluate
from app.models import EvaluateRequest, EvaluateResponse
from app.audit import verify_chain, iter_audits
from app.telemetry import init_tracing, snapshot as tele_snapshot

app = FastAPI()

rules_store: Dict[str, Tuple[object, object]] = {}
RulesHandler(RULES_PATH, rules_store)

TRACER = init_tracing()  # None if OTEL not configured

SHADOW: bool = (os.getenv("JIMINI_SHADOW") == "1")

# simple in-memory metrics
METRICS_TOTALS: Dict[str, int] = defaultdict(int)
METRICS_RULES: Dict[str, int] = defaultdict(int)
METRICS_SHADOW: Dict[str, int] = defaultdict(int)

@app.post('/v1/evaluate', response_model=EvaluateResponse)
async def evaluate_endpoint(req: EvaluateRequest):
    if req.api_key != API_KEY:
        raise HTTPException(401, 'Unauthorized')

    # start span if tracer is active
    if TRACER:
        with TRACER.start_as_current_span("jimini.evaluate") as span:
            span.set_attribute("agent.id", req.agent_id)
            span.set_attribute("endpoint", getattr(req, "endpoint", None) or "")
            span.set_attribute("direction", getattr(req, "direction", None) or "")
            span.set_attribute("shadow.enabled", SHADOW)

            decision, rule_ids, enforce_even_in_shadow = evaluate(
                req.text, req.agent_id, rules_store,
                direction=getattr(req, "direction", None),
                endpoint=getattr(req, "endpoint", None)
            )

            # metrics
            METRICS_TOTALS[decision] += 1
            for rid in rule_ids:
                METRICS_RULES[rid] += 1

            # shadow handling
            effective_decision = decision
            if SHADOW and decision in ("block", "flag") and not enforce_even_in_shadow:
                METRICS_SHADOW[decision] += 1
                effective_decision = "allow"

            # annotate span with outcome
            span.set_attribute("decision.original", decision)
            span.set_attribute("decision.effective", effective_decision)
            span.set_attribute("decision.enforce_even_in_shadow", enforce_even_in_shadow)
            if rule_ids:
                # keep it small; join into a single string attribute
                span.set_attribute("rules.triggered", ",".join(rule_ids))

            return EvaluateResponse(decision=effective_decision, rule_ids=rule_ids)

    # === fallback path when TRACER is None ===
    decision, rule_ids, enforce_even_in_shadow = evaluate(
        req.text, req.agent_id, rules_store,
        direction=getattr(req, "direction", None),
        endpoint=getattr(req, "endpoint", None)
    )
    METRICS_TOTALS[decision] += 1
    for rid in rule_ids:
        METRICS_RULES[rid] += 1

    effective_decision = decision
    if SHADOW and decision in ("block", "flag") and not enforce_even_in_shadow:
        METRICS_SHADOW[decision] += 1
        effective_decision = "allow"

    return EvaluateResponse(decision=effective_decision, rule_ids=rule_ids)

@app.get("/v1/metrics")
async def metrics() -> Dict[str, Any]:
    snap = tele_snapshot(loaded_rules=len(rules_store))
    snap["shadow_mode"] = SHADOW
    return snap

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
