from fastapi import FastAPI, HTTPException
from app.config import API_KEY, RULES_PATH
from app.rules_loader import RulesHandler
from app.enforcement import evaluate
from app.models import EvaluateRequest, EvaluateResponse

app = FastAPI()
rules_store: dict = {}
RulesHandler(RULES_PATH, rules_store)

@app.post('/v1/evaluate', response_model=EvaluateResponse)
async def evaluate_endpoint(req: EvaluateRequest):
    if req.api_key != API_KEY:
        raise HTTPException(401, 'Unauthorized')
    decision, rule_ids = evaluate(req.text, req.agent_id, rules_store)
    return EvaluateResponse(decision=decision, rule_ids=rule_ids)
