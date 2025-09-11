# app/main.py
from fastapi import FastAPI, HTTPException
from app.config import API_KEY, RULES_PATH
from app.rules_loader import RulesHandler
from app.enforcement import evaluate
from app.models import EvaluateRequest, EvaluateResponse
from app.audit import verify_chain
import os

app = FastAPI()
rules_store: dict = {}
RulesHandler(RULES_PATH, rules_store)

SHADOW = os.getenv("JIMINI_SHADOW") == "1"

@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate_endpoint(req: EvaluateRequest):
    if req.api_key != API_KEY:
        raise HTTPException(401, "Unauthorized")

    decision, rule_ids, enforce_even_in_shadow = evaluate(
        req.text,
        req.agent_id,
        rules_store,
        direction=req.direction,
        endpoint=req.endpoint,
    )

    # Shadow mode: allow unless a rule demands enforcement in shadow
    if SHADOW and decision in ("block", "flag") and not enforce_even_in_shadow:
        return EvaluateResponse(decision="allow", rule_ids=rule_ids)

    return EvaluateResponse(decision=decision, rule_ids=rule_ids)

@app.get("/v1/audit/verify")
async def audit_verify():
    return verify_chain()

@app.get("/health")
async def health():
    return {"ok": True, "shadow": SHADOW}
