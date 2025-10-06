# app/main.py
from collections import defaultdict, deque
import time
import os
from typing import Any, Dict, Deque, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
import urllib.request
import json

from app.models import (
    EvaluateRequest, EvaluateResponse, 
    ApprovalRequest, ApprovalResponse,
    RuleValidationRequest, RuleTestRequest
)
from app.rules_loader import load_rules, rules_store
from app.enforcement import evaluate, apply_shadow_logic
from app import audit
from app.audit_logger import log_policy_decision, verify_audit_chain, get_audit_stats
from app.config import get_config
from app.telemetry import Telemetry, TelemetryEvent
from app.util import now_iso, gen_request_id
from config.loader import get_current_config, mask_secrets, Config
from app.resilience import (
    resilience_manager, 
    graceful_error_handler,
    ErrorResponses,
    create_error_response
)
# Phase 5 - Operational Excellence imports
from app.observability import (
    get_metrics_collector, 
    prometheus_metrics_endpoint,
    setup_fastapi_instrumentation,
    MetricsMiddleware,
    track_policy_decision
)
from app.data_privacy import (
    get_data_manager,
    DataExportRequest,
    DataDeletionRequest
)
from app.operational_guardrails import (
    get_alert_manager,
    get_service_controller,
    get_deadletter_tool,
    get_runbook_automation
)
from app.continuous_improvement import (
    get_traffic_generator,
    get_benchmark_runner
)

# Phase 6A - Intelligence Expansion imports
try:
    from app.intelligence import (
        validate_intelligence_setup,
        add_intelligence_routes
    )
    INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    print(f"Intelligence features not available: {e}")
    INTELLIGENCE_AVAILABLE = False


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load rules
    rules_path = os.environ.get("JIMINI_RULES_PATH", "policy_rules.yaml")
    load_rules(rules_path)

    yield  # Application is running

    # Shutdown: Add cleanup logic here if needed
    pass


# Initialize FastAPI with enhanced documentation
app = FastAPI(
    title="Jimini AI Policy Gateway",
    description="""
    **Enterprise AI Policy Enforcement Gateway with Security & Compliance**
    
    Jimini provides real-time policy evaluation for AI applications with:
    
    * 🔒 **Security**: PII redaction, RBAC authentication, audit chains
    * 📋 **Policy Engine**: Rules-as-code with regex, thresholds, and LLM checks  
    * 📊 **Observability**: Metrics, SARIF export, OpenTelemetry integration
    * 🛡️ **Resilience**: Circuit breakers, shadow mode, error handling
    
    ## Authentication
    
    All `/v1/evaluate` requests require a valid `api_key` in the request body.
    Admin endpoints require RBAC authentication with JWT Bearer tokens.
    
    ## Rate Limits
    
    Default limits: 1000 requests/minute per API key.
    Contact enterprise@jimini.ai for higher limits.
    """,
    version="0.2.0",
    contact={
        "name": "Jimini Support",
        "email": "support@jimini.ai",
        "url": "https://github.com/jimini-ai/jimini"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {"url": "https://api.jimini.ai", "description": "Production server"},
        {"url": "http://localhost:9000", "description": "Local development server"}
    ],
    lifespan=lifespan
)

# Load configuration with fail-fast validation first
try:
    config = get_current_config()
except SystemExit as e:
    print(f"Configuration validation failed: {e}")
    raise

# Add security middleware stack
from app.security_middleware import SecurityMiddlewareManager

SecurityMiddlewareManager.create_middleware_stack(app, {
    "enable_security_headers": True,
    "enable_input_validation": True,
    "enable_rate_limiting": config.app.env == "prod"  # Only in production
})

# Add resilience middleware
app.middleware("http")(graceful_error_handler)

# Add CORS middleware for production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.app.env == "dev" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

telemetry = Telemetry.instance()

# Constants for shadow mode behavior
SHADOW_MODE = config.app.shadow_mode
metrics_shadow = defaultdict(int)  # Track shadow decisions

# API key from config
API_KEY = config.app.api_key

# simple in-memory metrics
METRICS_TOTALS: Dict[str, int] = defaultdict(int)
METRICS_RULES: Dict[str, int] = defaultdict(int)
METRICS_SHADOW: Dict[str, int] = defaultdict(int)
METRICS_ENDPOINTS: Dict[str, int] = defaultdict(int)
METRICS_DIRECTIONS: Dict[str, int] = defaultdict(int)
RECENT_DECISIONS: Deque[Dict[str, Any]] = deque(maxlen=100)


@app.get(
    "/health",
    summary="System Health Check",
    description="Basic health check endpoint for load balancers and monitoring systems.",
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "shadow_mode": True,
                        "loaded_rules": 26,
                        "version": "0.2.0"
                    }
                }
            }
        }
    },
    tags=["System Health"]
)
async def health() -> Dict[str, Any]:
    """Basic health check endpoint"""
    from app.__version__ import __version__
    return {
        "status": "ok", 
        "shadow_mode": SHADOW_MODE, 
        "loaded_rules": int(len(rules_store)),
        "version": __version__
    }


@app.get("/ready")
async def readiness() -> Dict[str, Any]:
    """Readiness check with configuration status"""
    try:
        current_config = get_current_config()
        
        # Check if config is valid
        config_status = "ok"
        
        # Check disk writeable for audit logs
        audit_writable = True
        try:
            audit_dir = os.path.dirname(current_config.siem.jsonl.file_path)
            if not os.path.exists(audit_dir):
                os.makedirs(audit_dir, exist_ok=True)
            test_file = os.path.join(audit_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception:
            audit_writable = False
            config_status = "warning"
        
        # Circuit breaker and resilience status
        resilience_health = resilience_manager.get_health_status()
        circuits_healthy = all(
            cb["state"] != "open" 
            for cb in resilience_health["circuit_breakers"].values()
        )
        
        return {
            "ready": config_status == "ok" and audit_writable and circuits_healthy,
            "config_version": current_config.version,
            "profile": current_config.profile,
            "audit_writable": audit_writable,
            "circuits_healthy": circuits_healthy,
            "loaded_rules": int(len(rules_store)),
            "resilience": resilience_health
        }
        
    except Exception as e:
        return {"ready": False, "error": str(e)}


@app.get("/about")
async def about() -> Dict[str, Any]:
    """Configuration disclosure for compliance"""
    try:
        current_config = get_current_config()
        masked_config = mask_secrets(current_config)
        
        return {
            "service": "Jimini AI Policy Gateway",
            "version": current_config.version,
            "profile": current_config.profile,
            "data_flows": {
                "audit_retention": f"{current_config.siem.jsonl.retention_days} days",
                "pii_processing": current_config.app.use_pii,
                "shadow_mode": current_config.app.shadow_mode,
                "enabled_forwarders": {
                    "jsonl": current_config.siem.jsonl.enabled,
                    "splunk": current_config.siem.splunk.enabled,
                    "elastic": current_config.siem.elastic.enabled
                },
                "enabled_notifiers": {
                    "slack": current_config.notifiers.slack.enabled,
                    "teams": current_config.notifiers.teams.enabled
                }
            },
            "config_summary": masked_config
        }
    except Exception as e:
        return {"error": str(e)}


@app.get(
    "/v1/resilience",
    summary="Resilience Health Status",
    description="Monitor circuit breakers, dead letter queue, and error handling status.",
    responses={
        200: {
            "description": "Resilience system status",
            "content": {
                "application/json": {
                    "example": {
                        "circuit_breakers": {
                            "openai": {
                                "state": "closed",
                                "failure_count": 0,
                                "success_count": 15
                            }
                        },
                        "dead_letter_queue": {
                            "size": 0,
                            "max_size": 1000
                        }
                    }
                }
            }
        }
    },
    tags=["Monitoring"]
)
async def resilience_health() -> Dict[str, Any]:
    """Get resilience system health status"""
    return resilience_manager.get_health_status()


@app.get("/admin/metrics")
async def admin_metrics(request: Request) -> Dict[str, Any]:
    """Admin endpoint for comprehensive metrics dump (RBAC protected)"""
    from app.rbac import get_rbac, Role
    rbac = get_rbac()
    
    # Check ADMIN role access
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required for metrics dump"
        )
    
    try:
        from app.circuit_breaker import circuit_manager
        from app.deadletter import deadletter_queue
        
        return {
            "total_requests": METRICS_TOTALS.get("total", 0),
            "decisions": dict(METRICS_TOTALS),
            "rules": dict(METRICS_RULES),
            "shadow_decisions": dict(metrics_shadow),
            "circuit_states": circuit_manager.get_all_states(),
            "deadletter_stats": deadletter_queue.get_stats(),
            "recent_decisions": list(RECENT_DECISIONS),
            "config_version": config.version,
            "rbac_status": rbac.get_rbac_status()
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/circuit/{name}/open")
async def admin_circuit_open(name: str, request: Request) -> Dict[str, str]:
    """Admin endpoint to manually open circuit breaker (RBAC protected)"""
    from app.rbac import get_rbac, Role
    from app.circuit_breaker import circuit_manager
    rbac = get_rbac()
    
    # Check ADMIN role access
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required for circuit control"
        )
    
    try:
        breaker = circuit_manager.get_breaker(name)
        breaker.force_open()
        return {"message": f"Circuit {name} manually opened", "state": breaker.get_state()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin/circuit/{name}/close")
async def admin_circuit_close(name: str, request: Request) -> Dict[str, str]:
    """Admin endpoint to manually close circuit breaker (RBAC protected)"""
    from app.rbac import get_rbac, Role
    from app.circuit_breaker import circuit_manager
    rbac = get_rbac()
    
    # Check ADMIN role access
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required for circuit control"
        )
    
    try:
        breaker = circuit_manager.get_breaker(name)
        breaker.force_close()
        return {"message": f"Circuit {name} manually closed", "state": breaker.get_state()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/admin/security")
async def admin_security_status(request: Request) -> Dict[str, Any]:
    """Security and compliance status endpoint (REVIEWER+ access)"""
    from app.rbac import get_rbac, Role
    from app.redaction import get_redactor
    rbac = get_rbac()
    
    # Check REVIEWER role access
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.REVIEWER):
        raise HTTPException(
            status_code=403,
            detail="Reviewer access required for security status"
        )
    
    try:
        redactor = get_redactor()
        current_config = get_current_config()
        
        return {
            "rbac_status": rbac.get_rbac_status(),
            "redaction_summary": redactor.get_redaction_summary(),
            "security_config": {
                "rbac_enabled": current_config.security.rbac_enabled,
                "pii_processing": current_config.app.use_pii,
                "tls_verification": {
                    "splunk": current_config.siem.splunk.verify_tls,
                    "elastic": current_config.siem.elastic.verify_tls
                }
            },
            "compliance_features": {
                "audit_chain": "enabled",
                "pii_redaction": "enabled" if redactor.should_redact() else "disabled",
                "data_retention": f"{current_config.siem.jsonl.retention_days} days"
            }
        }
    except Exception as e:
        return {"error": str(e)}


def determine_shadow_enforcement(rule_ids):
    """Determine if a rule should be enforced even in shadow mode."""
    # Look for rules with shadow_override: enforce
    for rule_id in rule_ids:
        rule = next((r for r in rules_store if r.id == rule_id), None)
        if rule and rule.shadow_override == "enforce":
            return True
    return False


def apply_shadow_logic(decision: str, rule_ids: list) -> tuple:
    """Apply shadow mode logic to decision

    Args:
        decision: The original decision (BLOCK, FLAG, ALLOW)
        rule_ids: List of rule IDs that triggered

    Returns:
        tuple: (original_decision, effective_decision)
    """
    # Check if any rule is in shadow_overrides
    enforce_even_in_shadow = any(r in config.app.shadow_overrides for r in rule_ids)

    # Shadow override logic
    if (
        config.app.shadow_mode
        and decision.upper() in ("BLOCK", "FLAG")
        and not enforce_even_in_shadow
    ):
        return decision, "ALLOW"
    else:
        return decision, decision


def post_webhook_alert(
    agent_id=None, endpoint=None, action=None, rule_ids=None, text_excerpt=None
):
    """Send webhook alert for blocked content or severe flags."""
    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        return

    payload = {
        "text": f"*Jimini Alert* - {action}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Policy violation detected*\nAction: `{action}`\nEndpoint: `{endpoint}`\nAgent: `{agent_id or 'n/a'}`\nRules: {', '.join(rule_ids or [])}",
                },
            }
        ],
    }

    if text_excerpt:
        payload["blocks"].append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Excerpt*:\n```{text_excerpt[:200]}```",
                },
            }
        )

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as _:
            pass
    except Exception:
        # Don't let webhook failures impact the API response
        pass


@app.post(
    "/v1/evaluate", 
    response_model=EvaluateResponse,
    summary="Evaluate Content Against Policy Rules",
    description="""
    **Evaluate text content against configured policy rules and return enforcement decision.**
    
    This is the core evaluation endpoint that processes text content through the policy engine
    and returns an enforcement decision based on matched rules.
    
    ## Request Processing
    
    1. **Authentication**: Validates API key
    2. **Policy Evaluation**: Runs content through rule engine
    3. **Decision Logic**: Applies precedence (block > flag > allow)
    4. **Shadow Mode**: May override decision based on configuration
    5. **Audit Logging**: Records decision in tamper-evident audit chain
    6. **Telemetry**: Updates metrics and optionally sends to forwarders
    
    ## Shadow Mode Behavior
    
    When `JIMINI_SHADOW=1` or shadow mode is enabled:
    - `block` and `flag` decisions are returned as `allow`
    - Original `rule_ids` are still included for monitoring
    - Per-rule `shadow_override: enforce` bypasses shadow mode
    
    ## Rate Limiting
    
    Default: 1000 requests/minute per API key.
    Returns HTTP 429 when exceeded.
    """,
    responses={
        200: {
            "description": "Successful evaluation",
            "content": {
                "application/json": {
                    "examples": {
                        "allow_decision": {
                            "summary": "Allowed Content",
                            "value": {
                                "action": "allow",
                                "rule_ids": [],
                                "message": "Evaluation completed. Decision: allow"
                            }
                        },
                        "flag_decision": {
                            "summary": "Flagged Content",
                            "value": {
                                "action": "flag", 
                                "rule_ids": ["EMAIL-1.0"],
                                "message": "Evaluation completed. Decision: flag"
                            }
                        },
                        "block_decision": {
                            "summary": "Blocked Content",
                            "value": {
                                "action": "block",
                                "rule_ids": ["API-KEY-1.0", "GITHUB-TOKEN-1.0"],
                                "message": "Evaluation completed. Decision: block"
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "Invalid API key"},
        422: {"description": "Invalid request format"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    },
    tags=["Policy Evaluation"]
)
async def evaluate_text(request: EvaluateRequest):
    """Evaluate text against policy rules and return decision."""
    request_id = request.request_id or gen_request_id()
    t0 = time.perf_counter()

    # Check API key
    api_key = request.api_key
    if api_key != os.environ.get("JIMINI_API_KEY", "changeme"):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Get current configuration
    cfg = get_current_config()
    
    # Inbound telemetry
    telemetry.record_event(
        TelemetryEvent(
            ts=now_iso(),
            endpoint="/v1/evaluate",
            direction="inbound",
            decision="SHADOW" if cfg.app.shadow_mode else "ALLOW",
            shadow_mode=cfg.app.shadow_mode,
            rule_ids=[],
            request_id=request_id,
        )
    )

    # Convert rules_store to the format expected by evaluate function
    rules_dict = {}
    for rule in rules_store:
        compiled_regex = None
        if rule.pattern:
            import re

            try:
                compiled_regex = re.compile(rule.pattern)
            except re.error:
                pass
        rules_dict[rule.id] = (rule, compiled_regex)

    # Phase 6B: Enhanced evaluation with risk assessment
    try:
        from app.enforcement import evaluate_with_risk_assessment
        decision, rule_ids, enforce_even_in_shadow, risk_assessment = evaluate_with_risk_assessment(
            text=request.text,
            agent_id=request.agent_id or "api",
            rules_store=rules_dict,
            direction=request.direction,
            endpoint=request.endpoint,
            user_id=getattr(request, 'user_id', None),
            request_id=request_id
        )
    except ImportError:
        # Fallback to standard evaluation if risk scoring not available
        from app.enforcement import evaluate
        decision, rule_ids, enforce_even_in_shadow = evaluate(
            text=request.text,
            agent_id=request.agent_id or "api",
            rules_store=rules_dict,
            direction=request.direction,
            endpoint=request.endpoint,
        )
        risk_assessment = None

    latency = round((time.perf_counter() - t0) * 1000, 2)

    # Apply shadow logic
    raw_decision, effective_decision = apply_shadow_logic(decision, rule_ids)

    # Log to enhanced audit chain (tamper-evident)
    log_policy_decision(
        action=effective_decision.lower() if effective_decision else "allow",
        request_id=request_id,
        direction=request.direction or "inbound",
        endpoint=request.endpoint or "/v1/evaluate",
        rule_ids=rule_ids,
        text_excerpt=request.text[:200] if len(request.text) > 200 else request.text,
        metadata={
            "agent_id": request.agent_id or "api",
            "latency_ms": latency,
            "shadow_mode": cfg.app.shadow_mode,
            "raw_decision": raw_decision if raw_decision != effective_decision else None
        }
    )

    # Record outbound telemetry
    telemetry_decision = effective_decision
    if (
        cfg.app.shadow_mode
        and effective_decision == "ALLOW"
        and raw_decision != "ALLOW"
    ):
        telemetry_decision = "SHADOW"  # Mark as shadow decision for telemetry

    telemetry.record_event(
        TelemetryEvent(
            ts=now_iso(),
            endpoint="/v1/evaluate",
            direction="outbound",
            decision=telemetry_decision,
            shadow_mode=cfg.app.shadow_mode,
            rule_ids=rule_ids,
            request_id=request_id,
            latency_ms=latency,
            meta={"raw_decision": raw_decision},
        )
    )

    # Webhook alert for blocks and severe flags (customize as needed)
    if decision == "block" or ("HALLUC-1.0" in rule_ids and decision == "flag"):
        post_webhook_alert(
            agent_id=request.agent_id,
            endpoint=getattr(request, "endpoint", None),
            action=decision,
            rule_ids=rule_ids,
            text_excerpt=request.text[:500] if hasattr(request, "text") else None,
        )

    # Make sure we call flush to ensure events are written
    telemetry.flush()

    # Construct response with shadow mode info and Phase 6B risk assessment
    response = EvaluateResponse(
        action=effective_decision.lower(),  # Convert back to lowercase for API consistency
        rule_ids=rule_ids,
        message=f"Evaluation completed. Decision: {effective_decision}",
    )
    
    # Phase 6B: Add risk assessment to response if available
    if risk_assessment:
        # Add risk assessment data as dynamic attributes
        response.risk_score = risk_assessment["risk_score"]
        response.risk_level = risk_assessment["risk_level"] 
        response.behavior_pattern = risk_assessment["behavior_pattern"]
        response.confidence = risk_assessment["confidence"]
        response.contributing_factors = risk_assessment["contributing_factors"]
        response.recommended_action = risk_assessment["recommended_action"]
        response.adaptive_threshold = risk_assessment["adaptive_threshold"]
    
    return response


# =============================================================================
# Rule Management API Endpoints
# =============================================================================

@app.get(
    "/v1/rules",
    summary="List Policy Rules", 
    description="Get a paginated list of all policy rules with optional filtering",
    responses={
        200: {
            "description": "Paginated list of rules",
            "content": {
                "application/json": {
                    "example": {
                        "rules": [
                            {
                                "id": "GITHUB-TOKEN-1.0",
                                "title": "GitHub Personal Access Token",
                                "severity": "high",
                                "action": "block",
                                "pattern": "ghp_[A-Za-z0-9]{36}"
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 50,
                        "has_next": False,
                        "has_prev": False
                    }
                }
            }
        }
    },
    tags=["Rule Management"]
)
async def list_rules(
    request: Request,
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None
):
    """List all policy rules with pagination and filtering."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager, RuleValidationError
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to list rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        return rule_manager.list_rules(
            page=page,
            page_size=page_size,
            action_filter=action,
            severity_filter=severity,
            search_query=search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/rules/{rule_id}",
    summary="Get Rule by ID",
    description="Retrieve a specific policy rule by its ID",
    tags=["Rule Management"]
)
async def get_rule_by_id(rule_id: str, request: Request):
    """Get a specific rule by ID."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager, RuleNotFoundError
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        return rule_manager.get_rule(rule_id)
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/rules",
    summary="Create New Rule",
    description="Create a new policy rule",
    responses={
        201: {"description": "Rule created successfully"},
        400: {"description": "Rule validation failed"},
        409: {"description": "Rule ID already exists"}
    },
    tags=["Rule Management"]
)
async def create_rule(rule_request: "RuleCreateRequest", request: Request):
    """Create a new policy rule."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager, RuleValidationError
    from app.models import RuleCreateRequest
    
    # Check ADMIN role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to create rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        new_rule = rule_manager.create_rule(rule_request)
        return new_rule
    except RuleValidationError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put(
    "/v1/rules/{rule_id}",
    summary="Update Rule",
    description="Update an existing policy rule",
    tags=["Rule Management"]
)
async def update_rule(rule_id: str, rule_update: "RuleUpdateRequest", request: Request):
    """Update an existing policy rule."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager, RuleNotFoundError, RuleValidationError
    from app.models import RuleUpdateRequest
    
    # Check ADMIN role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to update rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        updated_rule = rule_manager.update_rule(rule_id, rule_update)
        return updated_rule
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/v1/rules/{rule_id}",
    summary="Delete Rule",
    description="Delete a policy rule",
    tags=["Rule Management"]
)
async def delete_rule(rule_id: str, request: Request):
    """Delete a policy rule."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager, RuleNotFoundError
    
    # Check ADMIN role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to delete rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        rule_manager.delete_rule(rule_id)
        return {"message": f"Rule '{rule_id}' deleted successfully"}
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/rules/validate",
    summary="Validate Rule",
    description="Validate rule syntax and configuration without creating it",
    tags=["Rule Management"]
)
async def validate_rule(request: Request, rule_request: RuleValidationRequest = Body(...)):
    """Validate rule syntax and configuration."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to validate rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        return rule_manager.validate_rule(rule_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/rules/test",
    summary="Test Rule",
    description="Test a rule against sample text to see if it matches",
    tags=["Rule Management"]
)
async def test_rule(request: Request, rule_test: RuleTestRequest = Body(...)):
    """Test a rule against sample text."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager, RuleNotFoundError
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to test rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        return rule_manager.test_rule(rule_test)
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/rules/dryrun",
    summary="Dry-Run Rule Test",
    description="Test a rule against sample data without saving it",
    tags=["Rule Management"]
)
async def dryrun_rule(request: Request, rule_test: RuleTestRequest = Body(...)):
    """Perform a dry-run test of a rule without saving it."""
    from app.rbac import get_rbac, Role
    from app.enforcement import evaluate
    from app.models import Rule
    import re
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to dry-run rules"
        )
    
    try:
        # Get pattern from rule object or use provided rule_id
        if rule_test.rule:
            pattern = rule_test.rule.pattern
            action = rule_test.rule.action or "flag"
            rule_id = rule_test.rule_id or "dryrun-test"
            title = "Dry Run Test"
        elif rule_test.rule_id:
            # Test existing rule
            from app.rule_management import get_rule_manager
            from app.rules_loader import rules_store
            rule_manager = get_rule_manager()
            
            # Find the rule in rules_store
            existing_rule = None
            for rule in rules_store:
                if rule.id == rule_test.rule_id:
                    existing_rule = rule
                    break
            
            if not existing_rule:
                raise HTTPException(status_code=404, detail=f"Rule '{rule_test.rule_id}' not found")
            
            pattern = existing_rule.pattern
            action = existing_rule.action
            rule_id = rule_test.rule_id
            title = existing_rule.title
        else:
            raise HTTPException(status_code=400, detail="Either rule or rule_id must be provided")
        
        # Validate pattern exists
        if not pattern:
            raise HTTPException(status_code=400, detail="Rule pattern is required")
        
        # Create a temporary rule for testing
        temp_rule = Rule(
            id=rule_id,
            title=title,
            pattern=pattern,
            action=action,
            severity="medium",
            category="test",
            enabled=True
        )
        # Compile the pattern
        try:
            compiled_pattern = re.compile(pattern)
            temp_rule.compiled_pattern = compiled_pattern
        except re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {str(e)}")
        
        # Create rules_dict for evaluate function (same format as used in enforcement)
        rules_dict = {rule_id: (temp_rule, compiled_pattern)}
        
        # Test against sample text
        decision, rule_ids, enforce_even_in_shadow = evaluate(
            text=rule_test.test_text,
            agent_id="dryrun-test",
            rules_store=rules_dict,
            direction=rule_test.direction or "outbound",
            endpoint=rule_test.endpoint or "/dryrun"
        )
        
        return {
            "matched": bool(rule_ids),
            "action": decision,
            "rule_ids": rule_ids,
            "message": f"Matched {len(rule_ids)} rule(s)" if rule_ids else "No rules matched",
            "test_text": rule_test.test_text
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/rules/publish",
    summary="Publish Rule",
    description="Publish a validated rule to production",
    tags=["Rule Management"]
)
async def publish_rule(request: Request, rule_data: dict = Body(...)):
    """Publish a validated rule to production."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager
    from app.models import RuleCreateRequest
    
    # Check ADMIN role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to publish rules"
        )
    
    try:
        rule_manager = get_rule_manager()
        
        # Create the rule directly (bypassing approval workflow)
        rule_id = rule_data.get("id") or rule_data.get("rule_id")
        if not rule_id:
            raise HTTPException(status_code=400, detail="Rule ID is required")
        
        # Ensure the rule_data has the required fields
        if "title" not in rule_data:
            rule_data["title"] = f"Published Rule {rule_id}"
        if "pattern" not in rule_data and "llm_prompt" not in rule_data:
            raise HTTPException(status_code=400, detail="Rule pattern or llm_prompt is required")
        if "action" not in rule_data:
            rule_data["action"] = "flag"
        if "severity" not in rule_data:
            rule_data["severity"] = "medium"
        
        # Create RuleCreateRequest from dict
        rule_request = RuleCreateRequest(**rule_data)
        
        # Create the rule
        new_rule = rule_manager.create_rule(rule_request)
        
        return {
            "message": f"Rule '{rule_id}' published successfully",
            "rule_id": rule_id,
            "published_by": user,
            "published_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/rules/{rule_id}/stats",
    summary="Get Rule Statistics",
    description="Get performance and usage statistics for a specific rule",
    tags=["Rule Management"]
)
async def get_rule_stats(rule_id: str, request: Request):
    """Get statistics for a specific rule."""
    from app.rbac import get_rbac, Role
    from app.rule_management import get_rule_manager, RuleNotFoundError
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view rule statistics"
        )
    
    try:
        rule_manager = get_rule_manager()
        return rule_manager.get_rule_stats(rule_id)
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================

@app.get("/v1/metrics")
async def metrics() -> Dict[str, Any]:
    return {
        "shadow_mode": SHADOW_MODE,
        "totals": dict(METRICS_TOTALS),
        "rules": dict(METRICS_RULES),
        "shadow_overrides": dict(METRICS_SHADOW),
        "endpoints": dict(METRICS_ENDPOINTS),
        "directions": dict(METRICS_DIRECTIONS),
        "recent": list(RECENT_DECISIONS),
        "loaded_rules": len(rules_store),
    }


@app.get("/v1/audit/verify")
async def audit_verify() -> Dict[str, Any]:
    """Verify integrity of audit log chain using enhanced audit logger."""
    return verify_audit_chain()

@app.get("/v1/audit/statistics")
async def audit_statistics() -> Dict[str, Any]:
    """Get audit log statistics and summary."""
    return get_audit_stats()


@app.get("/v1/audit/sarif")
async def audit_sarif(date_prefix: str = None) -> Dict[str, Any]:
    """Return audit logs in SARIF format."""
    records = audit.get_records_by_date_prefix(date_prefix)

    # Convert audit records to SARIF results
    results = []
    for record in records:
        if record.action in ["block", "flag"]:
            results.append(
                {
                    "ruleId": "+".join(record.rule_ids)
                    if record.rule_ids
                    else "unknown",
                    "level": "error" if record.action == "block" else "warning",
                    "message": {
                        "text": f"Content {'blocked' if record.action == 'block' else 'flagged'} due to policy violation."
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": record.endpoint},
                                "region": {"snippet": {"text": record.text_excerpt}},
                            }
                        }
                    ],
                }
            )

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "Jimini"}}, "results": results}],
    }


# =============================================================================
# Decision Log Query Endpoints
# =============================================================================

@app.get(
    "/v1/decisions",
    summary="Query Decision Logs",
    description="Get paginated list of policy evaluation decisions with filtering",
    responses={
        200: {
            "description": "Paginated decision logs",
            "content": {
                "application/json": {
                    "example": {
                        "decisions": [
                            {
                                "request_id": "req_12345",
                                "timestamp": "2025-10-06T10:30:00Z",
                                "action": "block", 
                                "rule_ids": ["GITHUB-TOKEN-1.0"],
                                "endpoint": "/v1/evaluate",
                                "direction": "inbound",
                                "latency_ms": 15.2
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "page_size": 50,
                        "has_next": False,
                        "has_prev": False
                    }
                }
            }
        }
    },
    tags=["Decision Logs"]
)
async def query_decisions(
    request: Request,
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = None,
    rule_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    search: Optional[str] = None
):
    """Query decision logs with filtering and pagination."""
    from app.rbac import get_rbac, Role
    from app.decision_logs import get_decision_log_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to query decisions"
        )
    
    try:
        log_manager = get_decision_log_manager()
        return log_manager.query_decisions(
            page=page,
            page_size=page_size,
            action_filter=action,
            rule_filter=rule_id,
            endpoint_filter=endpoint,
            start_time=start_time,
            end_time=end_time,
            search_text=search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/decisions/stats",
    summary="Get Decision Statistics",
    description="Get aggregated statistics for policy decisions in a time range",
    tags=["Decision Logs"]
)
async def get_decision_stats(
    request: Request,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Get aggregated decision statistics for a time range."""
    from app.rbac import get_rbac, Role
    from app.decision_logs import get_decision_log_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view decision statistics"
        )
    
    # Convert empty strings to None
    if start_time == "":
        start_time = None
    if end_time == "":
        end_time = None
    
    try:
        log_manager = get_decision_log_manager()
        return log_manager.get_decision_stats(
            start_time=start_time,
            end_time=end_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/decisions/{request_id}",
    summary="Get Decision by Request ID",
    description="Retrieve a specific policy decision by request ID",
    tags=["Decision Logs"]
)
async def get_decision(request_id: str, request: Request):
    """Get a specific decision by request ID."""
    from app.rbac import get_rbac, Role
    from app.decision_logs import get_decision_log_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view decisions"
        )
    
    try:
        log_manager = get_decision_log_manager()
        decision = log_manager.get_decision_by_request_id(request_id)
        
        if not decision:
            raise HTTPException(
                status_code=404, 
                detail=f"Decision with request ID '{request_id}' not found"
            )
        
        return decision
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Shadow Mode Visibility Endpoints  
# =============================================================================

@app.get(
    "/v1/shadow/status",
    summary="Shadow Mode Status",
    description="Get current shadow mode configuration and effectiveness metrics",
    responses={
        200: {
            "description": "Shadow mode status",
            "content": {
                "application/json": {
                    "example": {
                        "enabled": True,
                        "override_rules": ["CRITICAL-API-1.0"],
                        "shadow_decisions_today": 45,
                        "would_have_blocked": 32,
                        "would_have_flagged": 13,
                        "effectiveness_score": 23.5
                    }
                }
            }
        }
    },
    tags=["Shadow Mode"]
)
async def get_shadow_status(request: Request):
    """Get current shadow mode status and statistics."""
    from app.rbac import get_rbac, Role
    from app.decision_logs import get_decision_log_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view shadow mode status"
        )
    
    try:
        log_manager = get_decision_log_manager()
        return log_manager.get_shadow_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/shadow/decisions",
    summary="Shadow Mode Decisions", 
    description="Get decisions that would have been different without shadow mode",
    tags=["Shadow Mode"]
)
async def get_shadow_decisions(
    request: Request,
    page: int = 1,
    page_size: int = 50,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Get decisions that would have been different without shadow mode."""
    from app.rbac import get_rbac, Role
    from app.decision_logs import get_decision_log_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view shadow decisions"
        )
    
    try:
        log_manager = get_decision_log_manager()
        return log_manager.get_shadow_decisions(
            page=page,
            page_size=page_size,
            start_time=start_time,
            end_time=end_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Policy Approval Workflow Endpoints
# =============================================================================

@app.post(
    "/v1/approvals",
    summary="Request Policy Approval",
    description="Submit a policy rule change for approval workflow",
    responses={
        201: {
            "description": "Approval request created",
            "content": {
                "application/json": {
                    "example": {
                        "request_id": "approval_abc12345",
                        "message": "Approval request created successfully",
                        "expires_at": "2025-10-09T10:30:00Z"
                    }
                }
            }
        }
    },
    tags=["Policy Approval"]
)
async def create_approval_request(
    approval_request: ApprovalRequest, 
    request: Request
):
    """Submit a policy rule change for approval."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager
    from app.models import ApprovalRequest
    
    # Check ADMIN role access for creating approvals
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to request policy approvals"
        )
    
    try:
        approval_manager = get_approval_manager()
        
        request_id = approval_manager.create_approval_request(
            rule_id=approval_request.rule_id,
            approval_type=approval_request.approval_type,
            rule_data=approval_request.rule_data,
            requested_by=user,
            justification=approval_request.justification,
            original_rule_data=approval_request.original_rule_data
        )
        
        approval_entry = approval_manager.get_approval_request(request_id)
        
        return {
            "request_id": request_id,
            "message": "Approval request created successfully",
            "expires_at": approval_entry.expires_at.isoformat() if approval_entry else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/approvals",
    summary="List Approval Requests",
    description="Get paginated list of policy approval requests with filtering",
    tags=["Policy Approval"]
)
async def list_approval_requests(
    request: Request,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    requested_by: Optional[str] = None
):
    """List policy approval requests with filtering."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager, ApprovalStatus
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to list approvals"
        )
    
    try:
        approval_manager = get_approval_manager()
        
        status_filter = None
        if status:
            try:
                status_filter = ApprovalStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status '{status}'. Valid values: {[s.value for s in ApprovalStatus]}"
                )
        
        return approval_manager.list_approval_requests(
            status_filter=status_filter,
            requested_by=requested_by,
            page=page,
            page_size=page_size
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Policy Approval Workflow Endpoints
# =============================================================================

@app.post(
    "/v1/approvals",
    summary="Request Policy Approval",
    description="Submit a policy rule change for approval workflow",
    responses={
        201: {
            "description": "Approval request created",
            "content": {
                "application/json": {
                    "example": {
                        "request_id": "approval_abc12345",
                        "message": "Approval request created successfully",
                        "expires_at": "2025-10-09T10:30:00Z"
                    }
                }
            }
        }
    },
    tags=["Policy Approval"]
)
async def create_approval_request(
    approval_request: ApprovalRequest, 
    request: Request
):
    """Submit a policy rule change for approval."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager
    
    # Check ADMIN role access for creating approvals
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to request policy approvals"
        )
    
    try:
        approval_manager = get_approval_manager()
        
        request_id = approval_manager.create_approval_request(
            rule_id=approval_request.rule_id,
            approval_type=approval_request.approval_type,
            rule_data=approval_request.rule_data,
            requested_by=user,
            justification=approval_request.justification,
            original_rule_data=approval_request.original_rule_data
        )
        
        approval_entry = approval_manager.get_approval_request(request_id)
        
        return {
            "request_id": request_id,
            "message": "Approval request created successfully",
            "expires_at": approval_entry.expires_at.isoformat() if approval_entry else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/approvals",
    summary="List Approval Requests",
    description="Get paginated list of policy approval requests with filtering",
    tags=["Policy Approval"]
)
async def list_approval_requests(
    request: Request,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
    requested_by: Optional[str] = None
):
    """List policy approval requests with filtering."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager, ApprovalStatus
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to list approvals"
        )
    
    try:
        approval_manager = get_approval_manager()
        
        status_filter = None
        if status:
            try:
                status_filter = ApprovalStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status '{status}'. Valid values: {[s.value for s in ApprovalStatus]}"
                )
        
        return approval_manager.list_approval_requests(
            status_filter=status_filter,
            requested_by=requested_by,
            page=page,
            page_size=page_size
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/v1/approvals/{request_id}",
    summary="Get Approval Request",
    description="Retrieve a specific policy approval request by ID",
    tags=["Policy Approval"]
)
async def get_approval_request(request_id: str, request: Request):
    """Get a specific approval request by ID."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view approval requests"
        )
    
    try:
        approval_manager = get_approval_manager()
        approval_request = approval_manager.get_approval_request(request_id)
        
        if not approval_request:
            raise HTTPException(
                status_code=404,
                detail=f"Approval request '{request_id}' not found"
            )
        
        from dataclasses import asdict
        return asdict(approval_request)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/approvals/{request_id}/approve",
    summary="Approve Request",
    description="Approve a pending policy approval request",
    tags=["Policy Approval"]
)
async def approve_request(request_id: str, request: Request):
    """Approve a pending policy approval request."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager
    from app.rule_management import get_rule_manager
    
    # Check ADMIN role access for approving
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to approve policy requests"
        )
    
    try:
        approval_manager = get_approval_manager()
        rule_manager = get_rule_manager()
        
        # Get the approval request
        approval_request = approval_manager.get_approval_request(request_id)
        if not approval_request:
            raise HTTPException(
                status_code=404,
                detail=f"Approval request '{request_id}' not found"
            )
        
        # Approve the request
        approval_manager.approve_request(request_id, user)
        
        # Execute the approved change
        if approval_request.approval_type == "create":
            rule_manager.create_rule(approval_request.rule_data)
        elif approval_request.approval_type == "update":
            rule_manager.update_rule(approval_request.rule_id, approval_request.rule_data)
        elif approval_request.approval_type == "delete":
            rule_manager.delete_rule(approval_request.rule_id)
        
        return {
            "message": f"Approval request {request_id} approved and applied successfully",
            "approved_by": user,
            "applied_at": datetime.now(timezone.utc).isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/approvals/{request_id}/reject",
    summary="Reject Request",
    description="Reject a pending policy approval request",
    tags=["Policy Approval"]
)
async def reject_request(
    request_id: str, 
    approval_response: ApprovalResponse,
    request: Request
):
    """Reject a pending policy approval request."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager
    
    # Check ADMIN role access for rejecting
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Admin access required to reject policy requests"
        )
    
    # Validate rejection reason is provided
    if not approval_response.reason or len(approval_response.reason.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="Rejection reason must be at least 5 characters"
        )
    
    try:
        approval_manager = get_approval_manager()
        
        # Get the approval request to verify it exists
        approval_request = approval_manager.get_approval_request(request_id)
        if not approval_request:
            raise HTTPException(
                status_code=404,
                detail=f"Approval request '{request_id}' not found"
            )
        
        # Reject the request
        approval_manager.reject_request(
            request_id, 
            user, 
            approval_response.reason
        )
        
        return {
            "message": f"Approval request {request_id} rejected successfully",
            "rejected_by": user,
            "reason": approval_response.reason,
            "rejected_at": datetime.now(timezone.utc).isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/v1/approvals/{request_id}/decline",
    summary="Decline Request",
    description="Decline a pending policy approval request (alias for reject)",
    tags=["Policy Approval"]
)
async def decline_request(
    request_id: str, 
    request: Request,
    decline_reason: dict = Body(...)
):
    """Decline a pending policy approval request."""
    # Create ApprovalResponse from decline request
    approval_response = ApprovalResponse(
        request_id=request_id,
        action="reject",
        reason=decline_reason.get("reason", "Declined")
    )
    return await reject_request(request_id, approval_response, request)


@app.get(
    "/v1/approvals/stats",
    summary="Approval Statistics",
    description="Get aggregated statistics for policy approval workflows",
    tags=["Policy Approval"]
)
async def get_approval_stats(request: Request):
    """Get approval workflow statistics."""
    from app.rbac import get_rbac, Role
    from app.policy_approval import get_approval_manager
    
    # Check VIEWER role access
    rbac = get_rbac()
    user = rbac.extract_user_from_request(request)
    if not rbac.has_role(user, Role.USER):
        raise HTTPException(
            status_code=403,
            detail="Viewer access required to view approval statistics"
        )
    
    try:
        approval_manager = get_approval_manager()
        return approval_manager.get_approval_stats()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Add telemetry endpoints
@app.get("/v1/telemetry/counters")
async def telemetry_counters():
    """Return current telemetry counters."""
    return telemetry.snapshot_counters()


@app.get("/v1/telemetry/flush")
async def telemetry_flush():
    """Force flush of telemetry events."""
    telemetry.flush()
    return {"status": "ok", "message": "Telemetry events flushed"}


# Phase 5A - Observability & Metrics Endpoints

@app.get("/v1/metrics/prom")
async def prometheus_metrics():
    """Prometheus metrics endpoint for monitoring dashboards."""
    return await prometheus_metrics_endpoint()


# Phase 5B - Data Management & Privacy (GDPR/CCPA)

@app.post("/v1/data/export/{user_id}")
async def export_user_data(user_id: str, request: DataExportRequest):
    """Export user data for GDPR/CCPA right-to-access compliance."""
    request.user_id = user_id
    data_manager = get_data_manager()
    return await data_manager.export_user_data(request)


@app.delete("/v1/data/delete/{user_id}")
async def delete_user_data(user_id: str, request: DataDeletionRequest):
    """Delete/redact user data for GDPR/CCPA right-to-be-forgotten compliance."""
    request.user_id = user_id
    data_manager = get_data_manager()
    return await data_manager.delete_user_data(request)


# Phase 5E - Operational Guardrails

@app.post("/admin/disable-forwarder/{target}")
async def disable_forwarder(target: str):
    """Disable a specific SIEM forwarder."""
    service_controller = get_service_controller()
    success = service_controller.disable_service(f"forwarder_{target}", "manual_disable")
    return {"disabled": success, "target": target}


@app.post("/admin/mute-notifier/{target}")
async def mute_notifier(target: str, duration_minutes: int = 60):
    """Mute notifications for a specific target.""" 
    service_controller = get_service_controller()
    success = service_controller.mute_service(f"notifier_{target}", duration_minutes)
    return {"muted": success, "target": target, "duration_minutes": duration_minutes}


@app.post("/admin/replay-deadletter")
async def replay_deadletter_messages(target: str, max_messages: int = 100):
    """Replay messages from dead letter queue."""
    deadletter_tool = get_deadletter_tool()
    results = await deadletter_tool.replay_messages(target, max_messages)
    return results


@app.get("/admin/service-status")
async def get_service_status():
    """Get operational status of all services."""
    service_controller = get_service_controller()
    return service_controller.get_service_status()


@app.post("/admin/health-check-all")
async def comprehensive_health_check():
    """Run comprehensive health check of all services."""
    runbook = get_runbook_automation()
    return await runbook.health_check_all_services()


# Phase 5F - Continuous Improvement

@app.post("/admin/load-test")
async def run_load_test(duration_seconds: int = 60, target_rps: int = 100):
    """Run synthetic load test for performance validation."""
    traffic_generator = get_traffic_generator()
    metrics = await traffic_generator.generate_load(duration_seconds, target_rps, 10)
    return {"metrics": metrics.__dict__, "timestamp": now_iso()}


@app.post("/admin/benchmark")
async def run_benchmark_suite():
    """Run complete benchmark suite for performance validation."""
    benchmark_runner = get_benchmark_runner()
    results = await benchmark_runner.run_full_benchmark_suite()
    return results


# Phase 6A - Intelligence Expansion Routes
if INTELLIGENCE_AVAILABLE:
    try:
        add_intelligence_routes(app)
        print("✅ Intelligence expansion features enabled")
        
        # Phase 6B - Risk Scoring Routes
        from app.intelligence import add_risk_scoring_routes, RISK_SCORING_AVAILABLE
        if RISK_SCORING_AVAILABLE and add_risk_scoring_routes:
            add_risk_scoring_routes(app)
            print("✅ Risk scoring features enabled")
        else:
            print("ℹ️ Risk scoring features not available (install: pip install scikit-learn)")
            
    except Exception as e:
        print(f"⚠️ Failed to add intelligence routes: {e}")
else:
    print("ℹ️ Intelligence expansion features not available (install: pip install spacy transformers)")


# Entry points for console scripts
def run_server():
    """Entry point for jimini-server console script."""
    import uvicorn
    from app.__version__ import __version__
    
    print(f"🚀 Starting Jimini AI Policy Gateway v{__version__}")
    print("🔧 Loading configuration...")
    
    # Load configuration
    config = get_current_config()
    
    host = "0.0.0.0"
    port = 9000
    
    # Override with environment variables if set
    if "JIMINI_HOST" in os.environ:
        host = os.environ["JIMINI_HOST"]
    if "JIMINI_PORT" in os.environ:
        port = int(os.environ["JIMINI_PORT"])
        
    print(f"🌐 Server starting on http://{host}:{port}")
    print("📋 API endpoints:")
    print("  • POST /v1/evaluate - Policy evaluation")
    print("  • GET /v1/metrics - System metrics")
    print("  • GET /v1/metrics/prom - Prometheus metrics")  
    print("  • GET /health - Health check")
    print("  • POST /v1/data/export/{user_id} - GDPR data export")
    print("  • DELETE /v1/data/delete/{user_id} - GDPR data deletion")
    print("  • GET /admin/* - Admin endpoints (RBAC protected)")
    print("  • POST /admin/load-test - Performance testing")
    print("  • POST /admin/benchmark - Benchmark suite")
    
    # Setup Phase 5 instrumentation
    setup_fastapi_instrumentation(app)
    
    # Add metrics middleware
    metrics_collector = get_metrics_collector()
    app.add_middleware(MetricsMiddleware, collector=metrics_collector)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


def run_uvicorn():
    """Entry point for jimini-uvicorn with reload support."""
    import uvicorn
    from app.__version__ import __version__
    
    print(f"🔄 Starting Jimini in development mode v{__version__}")
    
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0",
        port=9001,
        reload=True,
        log_level="debug"
    )
