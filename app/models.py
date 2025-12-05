from enum import Enum
from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional, Dict, Any, Pattern
from datetime import datetime


class Action(str, Enum):
    BLOCK = "block"
    FLAG = "flag"
    ALLOW = "allow"
    REDACT = "redact"


class Rule(BaseModel):
    id: str
    title: str
    severity: str
    category: Optional[str] = None  # e.g., pii, toxicity, injection, secrets, hallucination
    pattern: Optional[str] = None
    min_count: Optional[int] = 1
    max_chars: Optional[int] = None
    llm_prompt: Optional[str] = None
    applies_to: Optional[List[str]] = None
    endpoints: Optional[List[str]] = None
    action: Literal["block", "flag", "allow", "redact"]
    shadow_override: Optional[Literal["enforce"]] = None

    # Runtime fields (not in YAML)
    compiled_pattern: Optional[Pattern] = None

    model_config = {
        "extra": "ignore",  # Allow extra fields in YAML that aren't in model
    }


class EvaluateRequest(BaseModel):
    api_key: str = "changeme"
    text: str
    endpoint: str
    direction: str
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None  # Added for unique request tracking


class EvaluateResponse(BaseModel):
    success: bool = True
    decision: Optional[Literal["block", "flag", "allow", "redact"]] = None
    action: Optional[Literal["block", "flag", "allow", "redact"]] = None
    rule_ids: List[str] = Field(default_factory=list)
    redacted_text: Optional[str] = None  # Only set if redaction occurred
    message: str = ""
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    behavior_pattern: Optional[str] = None
    confidence: Optional[float] = None
    contributing_factors: Optional[List[str]] = None
    recommended_action: Optional[str] = None
    adaptive_threshold: Optional[float] = None

    @model_validator(mode="after")
    def _synchronise_decision_action(cls, values: "EvaluateResponse") -> "EvaluateResponse":
        decision = values.decision
        action = values.action

        if decision is None and action is None:
            values.decision = values.action = "allow"
        elif decision is None:
            values.decision = action
        elif action is None:
            values.action = decision

        return values

    @property
    def outcome(self) -> str:
        """Backwards compatible alias for the policy decision."""
        return self.action  # type: ignore[return-value]


class AuditRecord(BaseModel):
    timestamp: str


# Rule Management Models
class RuleCreateRequest(BaseModel):
    """Request model for creating a new rule"""
    id: str
    title: str
    severity: str
    category: Optional[str] = None
    pattern: Optional[str] = None
    min_count: Optional[int] = 1
    max_chars: Optional[int] = None
    llm_prompt: Optional[str] = None
    applies_to: Optional[List[str]] = None
    endpoints: Optional[List[str]] = None
    action: Literal["block", "flag", "allow", "redact"]
    shadow_override: Optional[Literal["enforce"]] = None


class RuleUpdateRequest(BaseModel):
    """Request model for updating an existing rule"""
    title: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    pattern: Optional[str] = None
    min_count: Optional[int] = None
    max_chars: Optional[int] = None
    llm_prompt: Optional[str] = None
    applies_to: Optional[List[str]] = None
    endpoints: Optional[List[str]] = None
    action: Optional[Literal["block", "flag", "allow", "redact"]] = None
    shadow_override: Optional[Literal["enforce"]] = None


class RuleValidationRequest(BaseModel):
    """Request model for validating rule syntax"""
    pattern: Optional[str] = None
    min_count: Optional[int] = 1
    max_chars: Optional[int] = None
    llm_prompt: Optional[str] = None
    applies_to: Optional[List[str]] = None
    endpoints: Optional[List[str]] = None
    action: Literal["block", "flag", "allow"]


class RuleTestRequest(BaseModel):
    """Request model for testing a rule against sample text"""
    rule_id: Optional[str] = None  # If testing existing rule
    rule: Optional[RuleValidationRequest] = None  # If testing new rule
    test_text: str
    endpoint: Optional[str] = None
    direction: Optional[str] = "inbound"


class RuleValidationResponse(BaseModel):
    """Response model for rule validation"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    pattern_compiled: bool = False
    llm_accessible: bool = False


class RuleTestResponse(BaseModel):
    """Response model for rule testing"""
    matched: bool
    action: str
    confidence: Optional[float] = None
    match_details: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None


class RuleListResponse(BaseModel):
    """Response model for listing rules with pagination"""
    rules: List[Rule]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class RuleStatsResponse(BaseModel):
    """Response model for rule statistics."""
    rule_id: str
    title: str
    total_evaluations: int
    matches: int
    blocks: int
    flags: int
    allows: int
    avg_execution_time_ms: float
    last_matched: Optional[str] = None  # ISO timestamp


# =============================================================================
# Decision Log Query Models
# =============================================================================

class DecisionLogEntry(BaseModel):
    """Model for a single decision log entry."""
    request_id: str
    timestamp: str
    action: str
    rule_ids: List[str]
    endpoint: str
    direction: str
    text_excerpt: Optional[str] = None
    agent_id: Optional[str] = None
    latency_ms: Optional[float] = None
    shadow_mode: Optional[bool] = None
    raw_decision: Optional[str] = None  # Original decision before shadow mode
    metadata: Optional[Dict[str, Any]] = None


class DecisionLogResponse(BaseModel):
    """Response model for decision log queries."""
    decisions: List[DecisionLogEntry]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class DecisionStatsResponse(BaseModel):
    """Response model for decision statistics."""
    time_range: str
    total_decisions: int
    decisions_by_action: Dict[str, int]
    decisions_by_rule: Dict[str, int]
    shadow_decisions: int
    avg_latency_ms: float
    peak_rps: float
    unique_endpoints: int


# =============================================================================
# Shadow Mode Models
# =============================================================================

class ShadowStatusResponse(BaseModel):
    """Response model for shadow mode status."""
    enabled: bool
    override_rules: List[str] = []
    shadow_decisions_today: int
    would_have_blocked: int
    would_have_flagged: int
    effectiveness_score: Optional[float] = None  # Percentage of decisions that would change


class ShadowDecisionEntry(BaseModel):
    """Model for shadow mode decision that would have been different."""
    request_id: str
    timestamp: str
    original_decision: str  # What actually happened (allow)
    shadow_decision: str   # What would have happened (block/flag)
    rule_ids: List[str]
    endpoint: str
    text_excerpt: Optional[str] = None
    confidence: Optional[float] = None


class ShadowDecisionsResponse(BaseModel):
    """Response model for shadow decisions that would have been different."""
    decisions: List[ShadowDecisionEntry]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# =============================================================================
# Audit Record Model 
# =============================================================================

class AuditRecord(BaseModel):
    """Audit record model."""
    timestamp: str
    request_id: str
    action: str
    direction: str
    endpoint: str
    rule_ids: List[str] = []
    text_excerpt: str = ""
    text_hash: str
    previous_hash: str
    metadata: Optional[Dict[str, Any]] = None
    
    # Phase 4C: Extended audit fields for compliance
    agent: Optional[str] = None           # User/agent who made the request
    reviewer: Optional[str] = None        # Who reviewed this decision (if applicable)
    rule_version: Optional[str] = None    # Version of rules used
    config_version: Optional[str] = None  # Configuration version
    pii_redacted: bool = False           # Whether PII was redacted from this record
    compliance_flags: List[str] = []      # HIPAA, CJIS, PCI, etc.
    retention_class: Optional[str] = None # Data retention classification
    source_ip: Optional[str] = None       # Source IP (redacted if USE_PII=false)
    user_context: Optional[Dict[str, Any]] = None  # Additional user context


# =============================================================================
# Policy Approval Workflow Models
# =============================================================================

class ApprovalType(str, Enum):
    """Types of policy approvals."""
    CREATE = "create"
    UPDATE = "update" 
    DELETE = "delete"
    ENABLE = "enable"
    DISABLE = "disable"


class ApprovalStatus(str, Enum):
    """Policy approval statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """Request for policy approval."""
    rule_id: str = Field(..., description="ID of the rule to be modified")
    approval_type: ApprovalType = Field(..., description="Type of approval needed")
    rule_data: Dict[str, Any] = Field(..., description="New rule data")
    original_rule_data: Optional[Dict[str, Any]] = Field(None, description="Current rule data (for updates/deletes)")
    justification: str = Field(..., min_length=10, description="Justification for the change")


class ApprovalResponse(BaseModel):
    """Response for approval action."""
    request_id: str
    action: str  # "approve" or "reject"
    reason: Optional[str] = Field(None, description="Reason for rejection (required for reject)")


class PolicyApprovalEntry(BaseModel):
    """Policy approval request entry."""
    request_id: str
    rule_id: str
    approval_type: ApprovalType
    rule_data: Dict[str, Any]
    original_rule_data: Optional[Dict[str, Any]]
    requested_by: str
    requested_at: datetime
    expires_at: datetime
    justification: str
    status: ApprovalStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class ApprovalRequestsPaginatedResponse(BaseModel):
    """Paginated response for approval requests."""
    requests: List[PolicyApprovalEntry]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class ApprovalStatsResponse(BaseModel):
    """Approval statistics response."""
    total_requests: int
    pending: int
    approved: int
    rejected: int
    expired: int
    avg_approval_time_hours: float
    pending_by_type: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
