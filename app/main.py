# app/main.py
from __future__ import annotations

from collections import defaultdict
from datetime import date
from fastapi import FastAPI, HTTPException
from re import Pattern
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

from app.config import API_KEY, RULES_PATH
from app.rules_loader import RulesHandler
from app.enforcement import evaluate
from app.models import EvaluateRequest, EvaluateResponse, Rule
from app.audit import verify_chain, iter_audits

import os

app = FastAPI()

# ---- rule store (rule_id -> (Rule, compiled_regex_or_None)) ----
rules_store: Dict[str, Tuple[Rule, Optional[Pattern[str]]]] = {}
RulesHandler(RULES_PATH, rules_store)

# ---- shadow mode ----
SHADOW: bool = (os.getenv("JIMINI_SHADOW") == "1")  # type: ignore[name-defined]

# ---- in-memory metrics ----
METRICS_TOTALS: DefaultDict[str, int] = defaultdict(int)   # allow/flag/block counts
METRICS_RULES: DefaultDict[str, int] = defaultdict(int)    # rule_id -> hits
METRICS_SHADOW: DefaultDict[str, int] = defaultdict(int)   # shadow overrides

@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate_endpoint(req: EvaluateRequest) -> EvaluateResponse:
    if req.api_key != API_KEY:
        raise HTTPException(401, "Unauthorized")

    decision, rule_ids, enforce_even_in_shadow = evaluate(
        text=req.text,
        agent_id=req.agent_id,
        rules_store=rules_store,
        direction=getattr(req, "direction", None),
        endpoint=getattr(req, "endpoint", None),
    )

    # metrics
    METRICS_TOTALS[decision] += 1
    for rid in rule_ids:
        METRICS_RULES[rid] += 1

    # shadow handling
    if SHADOW and decision in ("block", "flag") and not enforce_even_in_shadow:
        METRICS_SHADOW[decision] += 1
        return EvaluateResponse(decision="allow", rule_ids=rule_ids)

    return EvaluateResponse(decision=decision, rule_ids=rule_ids)

@app.get("/v1/metrics")
async def metrics() -> Dict[str, Any]:
    """Lightweight JSON for dashboards/polling."""
    return {
        "shadow_mode": SHADOW,
        "totals": dict(METRICS_TOTALS),           # Dict[str, int]
        "rules": dict(METRICS_RULES),             # Dict[str, int]
        "shadow_overrides": dict(METRICS_SHADOW), # Dict[str, int]
        "loaded_rules": int(len(rules_store)),
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
