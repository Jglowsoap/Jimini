# app/main.py
from collections import defaultdict, deque
import time
import os
from typing import Any, Dict, Deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import urllib.request
import json

from app.models import EvaluateRequest, EvaluateResponse
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
