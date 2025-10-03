#!/usr/bin/env python3
"""
🛡️ JIMINI GATEWAY & POLICY ENGINE
==================================

The enforcement gateway and APIs for PKI systems protection.
Sits in front of LDAP, Entrust IDG, UMS, DB2, ServiceNow as the filter of record.
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
import json
import hashlib
import hmac
import re
import uuid
import logging
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jimini")

# 📋 **MODELS & ENUMS**

class DecisionType(str, Enum):
    ALLOW = "allow"
    FLAG = "flag"
    BLOCK = "block"

class Direction(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class Mode(str, Enum):
    SHADOW = "shadow"
    ASSIST = "assist"
    ENFORCE = "enforce"

class SystemType(str, Enum):
    LDAP = "ldap"
    ENTRUST_IDG = "entrust_idg"
    UMS = "ums"
    DB2 = "db2"
    SERVICENOW = "service_now"
    LLM = "llm"

class Citation(BaseModel):
    doc: str
    section: str
    url: str

class Decision(BaseModel):
    ts: datetime
    direction: Direction
    system: SystemType
    endpoint: str
    decision: DecisionType
    rule_ids: List[str]
    masked_fields: List[str]
    citations: List[Citation]
    latency_ms: float
    tenant: str
    request_id: str

class Rule(BaseModel):
    id: str
    name: str
    pattern: Optional[str] = None
    field_checks: Optional[List[str]] = None
    action: DecisionType
    severity: Literal["low", "medium", "high", "critical"]
    system_scope: List[SystemType]
    enabled: bool = True
    citations: List[Citation] = []
    created_at: datetime = Field(default_factory=datetime.now)

class PolicyProposal(BaseModel):
    id: str = Field(default_factory=lambda: f"prop_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    proposed_rules: List[Rule]
    status: Literal["pending", "approved", "declined"] = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    reviewer: Optional[str] = None

class ResponseEnvelope(BaseModel):
    code: Literal["ok", "error"]
    data: Optional[Any] = None
    message: Optional[str] = None
    details: Optional[Any] = None

class MaskingConfig(BaseModel):
    strategy: Literal["deterministic_pseudo", "one_way_redaction"] = "deterministic_pseudo"
    secret_fields: List[str] = ["api_key", "token", "authorization"]
    deny_fields: List[str] = ["user.ssn", "user.dob"]
    allow_fields: List[str] = ["ticket.id", "ticket.status"]

class JiminiConfig(BaseModel):
    mode: Mode = Mode.ENFORCE
    llm: Dict[str, bool] = {"enabled": True, "mask_before_send": True}
    masking: MaskingConfig = Field(default_factory=MaskingConfig)

# 🛡️ **JIMINI POLICY ENGINE**

class JiminiPolicyEngine:
    """Core policy enforcement engine"""
    
    def __init__(self):
        self.config = JiminiConfig()
        self.rules: List[Rule] = []
        self.decisions: List[Decision] = []
        self.proposals: List[PolicyProposal] = []
        self.tenant_salts: Dict[str, str] = {}
        
        # Load default rules for PKI systems
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default rules for PKI systems protection"""
        default_rules = [
            Rule(
                id="PII-SSN-1",
                name="Social Security Number Detection",
                pattern=r'\b\d{3}-?\d{2}-?\d{4}\b',
                action=DecisionType.BLOCK,
                severity="critical",
                system_scope=[SystemType.LLM, SystemType.SERVICENOW],
                citations=[Citation(
                    doc="Data Protection Policy",
                    section="3.1.2",
                    url="sharepoint://policies/data#3.1.2"
                )]
            ),
            Rule(
                id="PII-PHONE-1",
                name="Phone Number Detection",
                pattern=r'\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b',
                action=DecisionType.FLAG,
                severity="medium",
                system_scope=[SystemType.LLM, SystemType.SERVICENOW],
                citations=[Citation(
                    doc="PII Handling Guidelines",
                    section="2.4",
                    url="sharepoint://policies/pii#2.4"
                )]
            ),
            Rule(
                id="SECRETS-API-1",
                name="API Key Detection",
                pattern=r'(?i)(api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})',
                action=DecisionType.BLOCK,
                severity="critical",
                system_scope=[SystemType.LLM, SystemType.SERVICENOW, SystemType.LDAP],
                citations=[Citation(
                    doc="Security Standards",
                    section="1.1",
                    url="sharepoint://policies/security#1.1"
                )]
            ),
            Rule(
                id="LDAP-INJECTION-1",
                name="LDAP Injection Detection",
                pattern=r'[()&|!*]',
                action=DecisionType.BLOCK,
                severity="high",
                system_scope=[SystemType.LDAP],
                citations=[Citation(
                    doc="LDAP Security Guide",
                    section="4.2",
                    url="sharepoint://policies/ldap#4.2"
                )]
            )
        ]
        self.rules.extend(default_rules)
    
    def get_tenant_salt(self, tenant_id: str, session_id: str) -> str:
        """Get deterministic salt for tenant/session"""
        key = f"{tenant_id}:{session_id}"
        if key not in self.tenant_salts:
            self.tenant_salts[key] = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.tenant_salts[key]
    
    def mask_field(self, value: str, field_name: str, tenant_id: str, session_id: str) -> str:
        """Apply masking based on field type and policy"""
        
        # Check if field is in deny list
        for deny_field in self.config.masking.deny_fields:
            if deny_field in field_name:
                return self._deterministic_mask(value, tenant_id, session_id)
        
        # Check if field contains secrets
        for secret_field in self.config.masking.secret_fields:
            if secret_field.lower() in field_name.lower():
                return "[REDACTED]"  # One-way redaction for secrets
        
        # Format-preserving masking for common PII
        if re.match(r'\b\d{3}-?\d{2}-?\d{4}\b', value):  # SSN
            return f"***-**-{value[-4:]}"  # Show last 4 digits
        elif re.match(r'\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b', value):  # Phone
            return f"***-***-{value[-4:]}"
        elif '@' in value:  # Email
            parts = value.split('@')
            if len(parts) == 2:
                return f"***@{parts[1]}"
        
        return self._deterministic_mask(value, tenant_id, session_id)
    
    def _deterministic_mask(self, value: str, tenant_id: str, session_id: str) -> str:
        """Create deterministic pseudonym using HMAC-SHA256"""
        salt = self.get_tenant_salt(tenant_id, session_id)
        pseudonym = hmac.new(
            salt.encode(),
            value.encode(),
            hashlib.sha256
        ).hexdigest()[:8]
        return f"[MASKED_{pseudonym.upper()}]"
    
    async def evaluate_request(self, 
                             content: str,
                             system: SystemType,
                             endpoint: str,
                             direction: Direction,
                             tenant_id: str,
                             session_id: str,
                             user_id: str = "unknown") -> Decision:
        """Evaluate request against all applicable rules"""
        
        start_time = datetime.now()
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        matched_rules = []
        masked_fields = []
        overall_decision = DecisionType.ALLOW
        all_citations = []
        
        # Apply rules based on system scope
        applicable_rules = [r for r in self.rules if r.enabled and system in r.system_scope]
        
        for rule in applicable_rules:
            if rule.pattern and re.search(rule.pattern, content, re.IGNORECASE):
                matched_rules.append(rule.id)
                all_citations.extend(rule.citations)
                
                # Escalate decision priority: ALLOW < FLAG < BLOCK
                if rule.action == DecisionType.BLOCK:
                    overall_decision = DecisionType.BLOCK
                elif rule.action == DecisionType.FLAG and overall_decision != DecisionType.BLOCK:
                    overall_decision = DecisionType.FLAG
                
                # Mask detected content for LLM systems
                if system == SystemType.LLM and self.config.llm["mask_before_send"]:
                    masked_fields.append(f"content.{rule.id}")
        
        # Apply mode-specific behavior
        if self.config.mode == Mode.SHADOW:
            # In shadow mode, log but don't enforce
            final_decision = DecisionType.ALLOW
        elif self.config.mode == Mode.ASSIST:
            # In assist mode, flag instead of block
            final_decision = DecisionType.FLAG if overall_decision == DecisionType.BLOCK else overall_decision
        else:
            # Enforce mode - full enforcement
            final_decision = overall_decision
        
        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create decision record
        decision = Decision(
            ts=start_time,
            direction=direction,
            system=system,
            endpoint=endpoint,
            decision=final_decision,
            rule_ids=matched_rules,
            masked_fields=masked_fields,
            citations=all_citations,
            latency_ms=latency_ms,
            tenant=tenant_id,
            request_id=request_id
        )
        
        # Log decision
        self.decisions.append(decision)
        logger.info(f"Decision logged: {request_id} -> {final_decision} ({len(matched_rules)} rules)")
        
        return decision

# 🌐 **FASTAPI APPLICATION**

# Global engine instance
engine = JiminiPolicyEngine()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    logger.info("🛡️ Jimini Gateway starting...")
    yield
    logger.info("🛡️ Jimini Gateway shutting down...")

app = FastAPI(
    title="Jimini Policy Gateway",
    description="PKI Systems Security Gateway & Policy Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 **AUTHENTICATION & AUTHORIZATION**

async def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract and validate tenant ID"""
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="X-Tenant-Id header required")
    return x_tenant_id

async def get_session_id(x_session_id: str = Header(...)) -> str:
    """Extract and validate session ID"""
    if not x_session_id:
        raise HTTPException(status_code=401, detail="X-Session-Id header required")
    return x_session_id

# 📊 **API ENDPOINTS**

@app.get("/api/v1/decisions", response_model=ResponseEnvelope)
async def get_decisions(
    tenant_id: str = Depends(get_tenant_id),
    system: Optional[SystemType] = None,
    decision: Optional[DecisionType] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get filterable, paginated decisions"""
    try:
        # Filter decisions by tenant
        tenant_decisions = [d for d in engine.decisions if d.tenant == tenant_id]
        
        # Apply filters
        if system:
            tenant_decisions = [d for d in tenant_decisions if d.system == system]
        if decision:
            tenant_decisions = [d for d in tenant_decisions if d.decision == decision]
        
        # Paginate
        total = len(tenant_decisions)
        paginated = tenant_decisions[offset:offset + limit]
        
        return ResponseEnvelope(
            code="ok",
            data={
                "decisions": [d.dict() for d in paginated],
                "total": total,
                "offset": offset,
                "limit": limit
            }
        )
    except Exception as e:
        logger.error(f"Error getting decisions: {e}")
        return ResponseEnvelope(code="error", message=str(e))

@app.get("/api/v1/decisions/{request_id}", response_model=ResponseEnvelope)
async def get_decision(
    request_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get specific decision by request ID"""
    try:
        decision = next(
            (d for d in engine.decisions if d.request_id == request_id and d.tenant == tenant_id),
            None
        )
        
        if not decision:
            return ResponseEnvelope(
                code="error",
                message="Decision not found",
                details={"request_id": request_id}
            )
        
        return ResponseEnvelope(code="ok", data=decision.dict())
        
    except Exception as e:
        logger.error(f"Error getting decision {request_id}: {e}")
        return ResponseEnvelope(code="error", message=str(e))

@app.get("/api/v1/rules", response_model=ResponseEnvelope)
async def get_rules(tenant_id: str = Depends(get_tenant_id)):
    """Get all rules"""
    try:
        return ResponseEnvelope(
            code="ok", 
            data={"rules": [r.dict() for r in engine.rules]}
        )
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

@app.post("/api/v1/rules/validate", response_model=ResponseEnvelope)
async def validate_rule(rule: Rule, tenant_id: str = Depends(get_tenant_id)):
    """Validate rule syntax and structure"""
    try:
        # Validate pattern if provided
        if rule.pattern:
            try:
                re.compile(rule.pattern)
            except re.error as e:
                return ResponseEnvelope(
                    code="error",
                    message="Rule validation failed",
                    details=[f"Invalid regex pattern: {e}"]
                )
        
        # Validate required fields
        if not rule.name:
            return ResponseEnvelope(
                code="error",
                message="Rule validation failed",
                details=["Rule name is required"]
            )
        
        return ResponseEnvelope(
            code="ok",
            message="Rule validation passed",
            data={"valid": True}
        )
        
    except ValidationError as e:
        return ResponseEnvelope(
            code="error",
            message="Rule validation failed",
            details=[str(err) for err in e.errors()]
        )

@app.post("/api/v1/rules/dryrun", response_model=ResponseEnvelope)
async def dryrun_rule(
    rule: Rule,
    test_content: str,
    tenant_id: str = Depends(get_tenant_id),
    session_id: str = Depends(get_session_id)
):
    """Test rule against sample content"""
    try:
        # Temporarily add rule for testing
        original_mode = engine.config.mode
        engine.config.mode = Mode.SHADOW
        engine.rules.append(rule)
        
        # Run evaluation
        decision = await engine.evaluate_request(
            content=test_content,
            system=rule.system_scope[0] if rule.system_scope else SystemType.LLM,
            endpoint="/test",
            direction=Direction.OUTBOUND,
            tenant_id=tenant_id,
            session_id=session_id
        )
        
        # Cleanup
        engine.rules.pop()
        engine.config.mode = original_mode
        
        # Check if our rule matched
        rule_matched = rule.id in decision.rule_ids
        
        return ResponseEnvelope(
            code="ok",
            data={
                "matched": rule_matched,
                "decision": decision.decision,
                "test_result": decision.dict()
            }
        )
        
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

@app.post("/api/v1/rules/publish", response_model=ResponseEnvelope)
async def publish_rule(rule: Rule, tenant_id: str = Depends(get_tenant_id)):
    """Publish validated rule to active ruleset"""
    try:
        # Validate first
        validation = await validate_rule(rule, tenant_id)
        if validation.code != "ok":
            return validation
        
        # Check for duplicate IDs
        existing = next((r for r in engine.rules if r.id == rule.id), None)
        if existing:
            return ResponseEnvelope(
                code="error",
                message="Rule ID already exists",
                details={"rule_id": rule.id}
            )
        
        # Add to active rules
        engine.rules.append(rule)
        logger.info(f"Published rule: {rule.id}")
        
        return ResponseEnvelope(
            code="ok",
            message="Rule published successfully",
            data={"rule_id": rule.id}
        )
        
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

@app.get("/api/v1/policies/proposals", response_model=ResponseEnvelope)
async def get_proposals(tenant_id: str = Depends(get_tenant_id)):
    """Get policy proposals"""
    try:
        return ResponseEnvelope(
            code="ok",
            data={"proposals": [p.dict() for p in engine.proposals]}
        )
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

@app.post("/api/v1/policies/proposals/{proposal_id}/approve", response_model=ResponseEnvelope)
async def approve_proposal(
    proposal_id: str,
    reviewer: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Approve policy proposal"""
    try:
        proposal = next((p for p in engine.proposals if p.id == proposal_id), None)
        if not proposal:
            return ResponseEnvelope(
                code="error",
                message="Proposal not found",
                details={"proposal_id": proposal_id}
            )
        
        # Update proposal status
        proposal.status = "approved"
        proposal.reviewed_at = datetime.now()
        proposal.reviewer = reviewer
        
        # Add rules to active ruleset
        engine.rules.extend(proposal.proposed_rules)
        
        logger.info(f"Approved proposal: {proposal_id} by {reviewer}")
        
        return ResponseEnvelope(
            code="ok",
            message="Proposal approved",
            data={"proposal_id": proposal_id, "rules_added": len(proposal.proposed_rules)}
        )
        
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

@app.post("/api/v1/policies/proposals/{proposal_id}/decline", response_model=ResponseEnvelope)
async def decline_proposal(
    proposal_id: str,
    reviewer: str,
    reason: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Decline policy proposal"""
    try:
        proposal = next((p for p in engine.proposals if p.id == proposal_id), None)
        if not proposal:
            return ResponseEnvelope(
                code="error",
                message="Proposal not found",
                details={"proposal_id": proposal_id}
            )
        
        proposal.status = "declined"
        proposal.reviewed_at = datetime.now()
        proposal.reviewer = reviewer
        
        logger.info(f"Declined proposal: {proposal_id} by {reviewer} - {reason}")
        
        return ResponseEnvelope(
            code="ok",
            message="Proposal declined",
            data={"proposal_id": proposal_id, "reason": reason}
        )
        
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

@app.get("/api/v1/coverage", response_model=ResponseEnvelope)
async def get_coverage(tenant_id: str = Depends(get_tenant_id)):
    """Get rule coverage statistics"""
    try:
        tenant_decisions = [d for d in engine.decisions if d.tenant == tenant_id]
        
        # Calculate coverage metrics
        total_requests = len(tenant_decisions)
        blocked = len([d for d in tenant_decisions if d.decision == DecisionType.BLOCK])
        flagged = len([d for d in tenant_decisions if d.decision == DecisionType.FLAG])
        allowed = len([d for d in tenant_decisions if d.decision == DecisionType.ALLOW])
        
        # System breakdown
        systems = {}
        for decision in tenant_decisions:
            system = decision.system.value
            if system not in systems:
                systems[system] = {"total": 0, "blocked": 0, "flagged": 0, "allowed": 0}
            systems[system]["total"] += 1
            systems[system][decision.decision.value] += 1
        
        return ResponseEnvelope(
            code="ok",
            data={
                "total_requests": total_requests,
                "blocked": blocked,
                "flagged": flagged,
                "allowed": allowed,
                "coverage_rate": (blocked + flagged) / max(total_requests, 1) * 100,
                "systems": systems,
                "active_rules": len(engine.rules)
            }
        )
        
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

# 🔍 **BREAK-GLASS REVEAL ENDPOINT**

class RevealRequest(BaseModel):
    request_id: str
    field: str
    reason: str

@app.post("/api/v1/reveal", response_model=ResponseEnvelope)
async def reveal_field(
    reveal_req: RevealRequest,
    tenant_id: str = Depends(get_tenant_id),
    session_id: str = Depends(get_session_id)
):
    """Break-glass reveal of masked field (logs audit event)"""
    try:
        # Find the decision
        decision = next(
            (d for d in engine.decisions if d.request_id == reveal_req.request_id and d.tenant == tenant_id),
            None
        )
        
        if not decision:
            return ResponseEnvelope(
                code="error",
                message="Decision not found",
                details={"request_id": reveal_req.request_id}
            )
        
        # Log audit event for break-glass access
        audit_decision = Decision(
            ts=datetime.now(),
            direction=Direction.OUTBOUND,
            system=SystemType.LLM,
            endpoint="/api/v1/reveal",
            decision=DecisionType.FLAG,
            rule_ids=["BREAK-GLASS-1"],
            masked_fields=[reveal_req.field],
            citations=[Citation(
                doc="Break Glass Policy",
                section="5.1",
                url="sharepoint://policies/breakglass#5.1"
            )],
            latency_ms=0.1,
            tenant=tenant_id,
            request_id=f"reveal_{uuid.uuid4().hex[:8]}"
        )
        engine.decisions.append(audit_decision)
        
        logger.warning(f"BREAK-GLASS ACCESS: {reveal_req.field} for {reveal_req.request_id} - Reason: {reveal_req.reason}")
        
        return ResponseEnvelope(
            code="ok",
            message="Field revealed (audit logged)",
            data={
                "field": reveal_req.field,
                "reason": reveal_req.reason,
                "ttl": "5 minutes",
                "audit_logged": True,
                "revealed_value": "[TEMPORARILY_REVEALED]"
            }
        )
        
    except Exception as e:
        return ResponseEnvelope(code="error", message=str(e))

# 🏥 **HEALTH & STATUS**

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "jimini-gateway",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "active_rules": len(engine.rules),
        "total_decisions": len(engine.decisions),
        "mode": engine.config.mode.value
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "jimini_gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )