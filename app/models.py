from pydantic import BaseModel
from typing import List, Literal

class Rule(BaseModel):
    id: str
    title: str
    pattern: str            # regex
    severity: Literal['error','warning','info']
    action: Literal['block','flag','allow']
    tags: List[str] = []

class EvaluateRequest(BaseModel):
    api_key: str
    agent_id: str
    text: str

class EvaluateResponse(BaseModel):
    decision: Literal['block','flag','allow']
    rule_ids: List[str]

class AuditRecord(BaseModel):
    timestamp: str
    agent_id: str
    decision: str
    rule_ids: List[str]
    excerpt: str
