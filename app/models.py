from enum import Enum
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any, Pattern


class Action(str, Enum):
    BLOCK = "block"
    FLAG = "flag"
    ALLOW = "allow"


class Rule(BaseModel):
    id: str
    title: str
    severity: str
    pattern: Optional[str] = None
    min_count: Optional[int] = 1
    max_chars: Optional[int] = None
    llm_prompt: Optional[str] = None
    applies_to: Optional[List[str]] = None
    endpoints: Optional[List[str]] = None
    action: Literal["block", "flag", "allow"]
    shadow_override: Optional[Literal["enforce"]] = None

    # Runtime fields (not in YAML)
    compiled_pattern: Optional[Pattern] = None

    model_config = {
        "extra": "ignore",  # Allow extra fields in YAML that aren't in model
    }


class EvaluateRequest(BaseModel):
    api_key: str
    text: str
    endpoint: str
    direction: str
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None  # Added for unique request tracking


class EvaluateResponse(BaseModel):
    action: Literal["block", "flag", "allow"]
    rule_ids: List[str] = []
    message: str = ""


class AuditRecord(BaseModel):
    timestamp: str
    request_id: str
    action: str
    direction: str
    endpoint: str
    rule_ids: List[str] = []
    text_excerpt: str = ""
    text_hash: str
    previous_hash: str
    metadata: Optional[Dict[str, Any]] = None  # Added for additional context
    metadata: Optional[Dict[str, Any]] = None  # Added for additional context
