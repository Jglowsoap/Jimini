from pydantic import BaseModel
from typing import List, Literal, Optional

class Rule(BaseModel):
    id: str
    title: str
    text: Optional[str] = None
    pattern: Optional[str] = None
    llm_prompt: Optional[str] = None
    severity: Literal['error','warning','info']
    action: Literal['block','flag','allow']
    tags: List[str] = []

    # enforcement extras
    min_count: Optional[int] = None
    max_chars: Optional[int] = None
    applies_to: Optional[List[str]] = None
    endpoints: Optional[List[str]] = None
    shadow_override: Optional[Literal['enforce','ignore']] = None

class EvaluateRequest(BaseModel):
    api_key: str
    agent_id: str
    text: str
    direction: Optional[str] = None
    endpoint: Optional[str] = None

class EvaluateResponse(BaseModel):
    decision: Literal['block','flag','allow']
    rule_ids: List[str]

class AuditRecord(BaseModel):
    timestamp: str
    agent_id: str
    decision: str
    rule_ids: List[str]
    excerpt: str
    # --- tamper-evident chain fields (optional) ---
    prev_hash: Optional[str] = None
    hash: Optional[str] = None
    chain_hash: Optional[str] = None 