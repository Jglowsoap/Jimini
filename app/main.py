# app/main.py
from __future__ import annotations
from app.telemetry import incr as tele_incr, snapshot as tele_snapshot, push_last
from collections import defaultdict
from datetime import date, datetime, timezone
from fastapi import FastAPI, HTTPException
from re import Pattern
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

from app.config import API_KEY, RULES_PATH, WEBHOOK_URL
from app.rules_loader import RulesHandler
from app.enforcement import evaluate
from app.models import EvaluateRequest, EvaluateResponse, Rule
from app.audit import verify_chain, iter_audits
from app.notifier import notify_block

import httpx
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

    # --- Alert webhook for high-severity blocks ---
    if WEBHOOK_URL and decision == "block":
        # Find triggered rules and check severity
        triggered_rules = []
        for rid in rule_ids:
            entry = rules_store.get(rid)
            if entry:
                rule = entry[0] if isinstance(entry, tuple) else entry
                triggered_rules.append(rule)
        error_rules = [r for r in triggered_rules if hasattr(r, "severity") and getattr(r, "severity", None) == "error"]
        if error_rules:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": req.agent_id,
                "endpoint": getattr(req, "endpoint", None),
                "rule_ids": rule_ids[:3],
                "shadow": SHADOW,
                "decision": decision,
                "audit_excerpt": req.text[:200],
                "audit_chain_hash": None,
            }
            # Try to get audit chain hash from latest audit record if available
            try:
                from app.audit import iter_audits
                audits = list(iter_audits())
                if audits:
                    payload["audit_chain_hash"] = getattr(audits[-1], "hash", None)
            except Exception:
                pass
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(WEBHOOK_URL, json=payload)
            except Exception as e:
                print(f"[Jimini] Webhook alert failed: {e}")

    # Was enforcement overridden by SHADOW?
    shadow_overridden = False
    effective_decision = decision
    if SHADOW and decision in ("block", "flag") and not enforce_even_in_shadow:
        shadow_overridden = True
        effective_decision = "allow"

    # Telemetry
    tele_incr(
        decision=decision,
        rule_ids=rule_ids,
        endpoint=getattr(req, "endpoint", None),
        direction=getattr(req, "direction", None),
        shadow_overridden=shadow_overridden,
    )
    push_last({
        "agent_id": req.agent_id,
        "endpoint": getattr(req, "endpoint", None),
        "direction": getattr(req, "direction", None),
        "decision": decision,
        "effective": effective_decision,
        "rule_ids": rule_ids,
    })

    # shadow handling
    if shadow_overridden:
        METRICS_SHADOW[decision] += 1
        result = EvaluateResponse(decision=effective_decision, rule_ids=rule_ids)
        notify_block(
            agent_id=req.agent_id,
            decision=decision,              # original decision from engine
            rule_ids=rule_ids,
            endpoint=getattr(req, "endpoint", None),
            excerpt=req.text,
        )
        return result

    result = EvaluateResponse(decision=decision, rule_ids=rule_ids)
    notify_block(
        agent_id=req.agent_id,
        decision=decision,              # original decision from engine
        rule_ids=rule_ids,
        endpoint=getattr(req, "endpoint", None),
        excerpt=req.text,
    )
    return result

@app.get("/v1/metrics")
async def metrics():
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
