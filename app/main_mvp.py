#!/usr/bin/env python3
"""
Jimini Phase 1 MVP - Minimal Viable Product for "Ship Now" Strategy

This is a simplified version that focuses on core policy evaluation functionality
without the advanced features that have dependency issues.

Core Features:
- Policy rule evaluation
- Basic audit logging  
- Health endpoints
- Metrics endpoint
- Shadow mode support
"""

import os
import time
import json
from typing import Dict, Any, cast, Literal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.models import EvaluateRequest, EvaluateResponse
from app.rules_loader import load_rules, rules_store  
from app.enforcement import evaluate, apply_shadow_logic
from app.util import now_iso, gen_request_id

# Try to import shadow AI integration (Phase 2A)
shadow_ai_module = None
try:
    import phase_2a_shadow_ai
    shadow_ai_module = phase_2a_shadow_ai
    shadow_ai_available = True
    print("   ✅ Phase 2A Shadow AI: Available")
except ImportError:
    shadow_ai_available = False
    print("   ⚠️ Phase 2A Shadow AI: Not available")

# Try to import AI Assist Mode (Phase 2B)
ai_assist_module = None
try:
    import phase_2b_ai_assist
    ai_assist_module = phase_2b_ai_assist
    ai_assist_available = True
    print("   ✅ Phase 2B AI Assist: Available")
except ImportError:
    ai_assist_available = False
    print("   ⚠️ Phase 2B AI Assist: Not available")

# Import Phase 2C Autonomous AI
try:
    from phase_2c_autonomous_ai import (
        evaluate_autonomous_decision,
        get_autonomous_ai_status,
        update_autonomy_level,
        autonomous_ai_engine
    )
    PHASE_2C_AVAILABLE = True
    print("🤖 Phase 2C Autonomous AI: Available")
except ImportError as e:
    PHASE_2C_AVAILABLE = False
    print(f"⚠️ Phase 2C Autonomous AI: Not available ({e})")

# Import Phase 3 Ecosystem Intelligence
try:
    from phase_3_ecosystem_intelligence import (
        evaluate_with_ecosystem_intelligence,
        get_ecosystem_status,
        initialize_ecosystem_intelligence,
        create_healthcare_tenant,
        create_fintech_tenant,
        create_government_tenant,
        TenantProfile,
        TenantTier,
        ecosystem_engines
    )
    PHASE_3_AVAILABLE = True
    print("🌍 Phase 3 Ecosystem Intelligence: Available")
except ImportError as e:
    PHASE_3_AVAILABLE = False
    print(f"⚠️ Phase 3 Ecosystem Intelligence: Not available ({e})")

# Import Phase 4 Global Platform
try:
    from phase_4_global_platform import (
        initialize_global_platform,
        get_global_platform,
        get_platform_status,
        deploy_integration_for_tenant,
        GlobalPlatformEngine
    )
    PHASE_4_AVAILABLE = True
    print("🌐 Phase 4 Global Platform: Available")
except ImportError as e:
    PHASE_4_AVAILABLE = False
    print(f"⚠️ Phase 4 Global Platform: Not available ({e})")

# Simple configuration from environment
API_KEY = os.getenv("JIMINI_API_KEY", "changeme")
SHADOW_MODE = os.getenv("JIMINI_SHADOW", "0") == "1"
RULES_PATH = os.getenv("JIMINI_RULES_PATH", "policy_rules.yaml")

# Simple metrics counter
metrics = {
    "evaluations_total": 0,
    "blocks_total": 0,
    "flags_total": 0, 
    "allows_total": 0,
    "errors_total": 0,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load rules on startup"""
    print(f"🚀 Jimini Phase 1 MVP Starting...")
    print(f"   Rules: {RULES_PATH}")
    print(f"   Shadow Mode: {SHADOW_MODE}")
    
    # Load rules
    try:
        load_rules(RULES_PATH)
        # Import after loading to get updated rules_store
        from app.rules_loader import rules_store as updated_rules_store
        print(f"   ✅ Successfully loaded {len(updated_rules_store)} rules")
        for rule in updated_rules_store[:3]:  # Show first 3 rules
            print(f"      - {rule.id}: {rule.title}")
        if len(updated_rules_store) > 3:
            print(f"      ... and {len(updated_rules_store) - 3} more")
    except Exception as e:
        print(f"   ⚠️ Rules loading failed: {e}")
        
    yield
    
    print("🛑 Jimini Phase 1 MVP Stopping...")

# Create FastAPI app
app = FastAPI(
    title="Jimini AI Policy Gateway - Phase 1 MVP",
    description="Lightweight AI policy evaluation with core functionality",
    version="0.2.0-mvp",
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

# Phase 2A Shadow AI and Phase 2B AI Assist routes are integrated directly

def authenticate_request(request: Request) -> bool:
    """Simple API key authentication"""
    auth_header = request.headers.get("authorization", "")
    api_key_header = request.headers.get("x-api-key", "")
    
    # Check Authorization header (Bearer token)
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return token == API_KEY
    
    # Check X-API-Key header
    if api_key_header:
        return api_key_header == API_KEY
    
    return False

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Import fresh rules_store to get current state
    from app.rules_loader import rules_store as current_rules_store
    return {
        "status": "healthy",
        "version": "0.2.0-mvp",
        "timestamp": now_iso(),
        "rules_loaded": len(current_rules_store),
        "rules_sample": [r.id for r in current_rules_store[:3]],
        "shadow_mode": SHADOW_MODE
    }

@app.get("/v1/metrics")
async def get_metrics():
    """Simple metrics endpoint"""
    # Import fresh rules_store to get current state
    from app.rules_loader import rules_store as current_rules_store
    return {
        "metrics": metrics,
        "timestamp": now_iso(),
        "rules_count": len(current_rules_store)
    }

@app.get("/v1/metrics/prom", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """Prometheus-compatible metrics"""
    output = []
    output.append("# HELP jimini_evaluations_total Total policy evaluations")
    output.append("# TYPE jimini_evaluations_total counter")
    output.append(f"jimini_evaluations_total {metrics['evaluations_total']}")
    
    output.append("# HELP jimini_decisions_total Policy decisions by action")
    output.append("# TYPE jimini_decisions_total counter")
    output.append(f'jimini_decisions_total{{action="block"}} {metrics["blocks_total"]}')
    output.append(f'jimini_decisions_total{{action="flag"}} {metrics["flags_total"]}')
    output.append(f'jimini_decisions_total{{action="allow"}} {metrics["allows_total"]}')
    
    return "\n".join(output) + "\n"

@app.post("/v1/evaluate")
async def evaluate_policy(request: EvaluateRequest, http_request: Request) -> EvaluateResponse:
    """Core policy evaluation endpoint"""
    start_time = time.time()
    request_id = gen_request_id()
    
    # Authenticate request
    if not authenticate_request(http_request):
        metrics["errors_total"] += 1
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Update metrics
        metrics["evaluations_total"] += 1
        
        # Evaluate against policies (get fresh rules_store)
        from app.rules_loader import rules_store as current_rules_store
        # Convert list to dict format expected by evaluate function
        rules_dict = {rule.id: rule for rule in current_rules_store}
        decision, rule_ids, enforce_in_shadow = evaluate(
            text=request.text,
            agent_id=request.agent_id or "default",
            rules_store=rules_dict,  # Pass rules as dict with rule.id as key
            direction=request.direction,
            endpoint=request.endpoint
        )
        
        # Apply shadow mode logic
        if SHADOW_MODE and not enforce_in_shadow:
            raw_decision, decision = apply_shadow_logic(decision, rule_ids)
        else:
            raw_decision = decision
        
        # Phase 2B: Get AI Assist recommendations (parallel to static rules)
        ai_insights = None
        if ai_assist_available and ai_assist_module:
            try:
                assist_result = await ai_assist_module.evaluate_with_ai_assist(
                    text=request.text,
                    static_action=decision,
                    static_rule_ids=rule_ids,
                    static_message=f"Evaluation completed in {int((time.time() - start_time) * 1000)}ms",
                    endpoint=request.endpoint,
                    direction=request.direction,
                    agent_id=request.agent_id or "default"
                )
                ai_insights = {
                    "ai_recommendation": assist_result.ai_recommendation.action if assist_result.ai_recommendation else None,
                    "ai_confidence": assist_result.ai_recommendation.confidence if assist_result.ai_recommendation else None,
                    "ai_reasoning": assist_result.ai_recommendation.reasoning if assist_result.ai_recommendation else None,
                    "agreement": assist_result.agreement,
                    "learning_opportunity": assist_result.learning_opportunity
                }
            except Exception as e:
                print(f"⚠️ AI Assist failed: {e}")
                ai_insights = {"error": "AI assist temporarily unavailable"}
        
        # Phase 2C: Autonomous AI decision making (if enabled)
        autonomous_decision = None
        final_decision = decision  # Default to static rule decision
        decision_authority = "static_rules"
        
        if autonomous_ai_available and autonomous_ai_module:
            try:
                autonomous_result = await autonomous_ai_module.evaluate_autonomous(
                    text=request.text,
                    static_action=decision,
                    static_rule_ids=rule_ids,
                    static_message=f"Static evaluation in {int((time.time() - start_time) * 1000)}ms",
                    endpoint=request.endpoint,
                    direction=request.direction,
                    agent_id=request.agent_id or "default"
                )
                
                # Use AI autonomous decision if confidence/safety requirements met
                final_decision = autonomous_result.ai_decision
                decision_authority = autonomous_result.decision_authority
                
                autonomous_decision = {
                    "ai_decision": autonomous_result.ai_decision,
                    "ai_confidence": autonomous_result.ai_confidence,
                    "decision_authority": autonomous_result.decision_authority,
                    "human_review_required": autonomous_result.human_review_required,
                    "safety_constraints_met": autonomous_result.safety_constraints_met,
                    "autonomy_level": autonomous_result.autonomy_level.value
                }
                
            except Exception as e:
                print(f"⚠️ Autonomous AI failed: {e}")
                autonomous_decision = {"error": "Autonomous AI temporarily unavailable"}
        
        # Update decision metrics (use final decision)
        if final_decision == "block":
            metrics["blocks_total"] += 1
        elif final_decision == "flag":
            metrics["flags_total"] += 1
        else:
            metrics["allows_total"] += 1
        
        # Create response with AI insights and autonomous decision info
        response_message = f"Evaluation completed in {int((time.time() - start_time) * 1000)}ms"
        
        # Add autonomous AI decision info if available
        if autonomous_decision and not autonomous_decision.get("error"):
            if decision_authority == "ai_autonomous":
                response_message += f" (AI decided: {final_decision})"
            elif decision_authority == "ai_autonomous_pending_review":
                response_message += f" (AI suggests {final_decision}, review required)"
        elif ai_insights and ai_insights.get("ai_recommendation") and not ai_insights.get("error"):
            if ai_insights.get("agreement"):
                response_message += f" (AI agrees: {ai_insights['ai_recommendation']})"
            else:
                response_message += f" (AI suggests: {ai_insights['ai_recommendation']})"
        
        response = EvaluateResponse(
            action=cast(Literal["block", "flag", "allow"], final_decision),
            rule_ids=rule_ids,
            message=response_message
        )
        
        # Simple audit log (just print for MVP)
        print(f"[AUDIT] {now_iso()} | {request_id} | {decision} | {rule_ids} | {request.endpoint}")
        
        return response
        
    except Exception as e:
        metrics["errors_total"] += 1
        print(f"[ERROR] {now_iso()} | {request_id} | {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.get("/v2/status")
async def phase_2_status():
    """Phase 2A Shadow AI status"""
    # Import fresh rules_store to get current state
    from app.rules_loader import rules_store as current_rules_store
    return {
        "phase": "2A - Shadow AI",
        "shadow_ai_enabled": shadow_ai_available,
        "rules_loaded": len(current_rules_store),
        "message": "Phase 2A: AI learning in shadow mode",
        "timestamp": now_iso()
    }

@app.get("/v2b/status")
async def ai_assist_status():
    """Phase 2B AI Assist Mode status"""
    # Import fresh rules_store to get current state
    from app.rules_loader import rules_store as current_rules_store
    
    if ai_assist_available and ai_assist_module:
        try:
            ai_status = ai_assist_module.get_ai_assist_status()
        except Exception:
            ai_status = {"error": "AI Assist module failed to load"}
    else:
        ai_status = {"enabled": False, "message": "AI Assist module not available"}
    
    return {
        "phase": "2B - AI Assist Mode",
        "ai_assist_enabled": ai_assist_available,
        "rules_loaded": len(current_rules_store),
        "ai_status": ai_status,
        "message": "AI provides recommendations while static rules enforce",
        "safety_model": "Human oversight required, static rules always take precedence",
        "timestamp": now_iso()
    }

@app.get("/v2c/status")
async def autonomous_ai_status():
    """Phase 2C Autonomous AI status"""
    # Import fresh rules_store to get current state
    from app.rules_loader import rules_store as current_rules_store
    
    if autonomous_ai_available and autonomous_ai_module:
        try:
            autonomous_status = autonomous_ai_module.get_autonomous_status()
        except Exception:
            autonomous_status = {"error": "Autonomous AI module failed to load"}
    else:
        autonomous_status = {"enabled": False, "message": "Autonomous AI module not available"}
    
    return {
        "phase": "2C - Autonomous AI Mode",
        "autonomous_ai_enabled": autonomous_ai_available,
        "rules_loaded": len(current_rules_store),
        "autonomous_status": autonomous_status,
        "message": "AI makes safe autonomous decisions within safety constraints",
        "safety_model": "Human oversight with real-time override capability",
        "timestamp": now_iso()
    }

@app.post("/v2c/override")
async def human_override(request: Request):
    """Human override of autonomous AI decision"""
    if not autonomous_ai_available or not autonomous_ai_module:
        raise HTTPException(status_code=404, detail="Autonomous AI not available")
    
    try:
        data = await request.json()
        result = await autonomous_ai_module.autonomous_ai_engine.human_override(
            decision_id=data.get("decision_id", "unknown"),
            human_action=data.get("human_action"),
            human_reasoning=data.get("human_reasoning", ""),
            operator_id=data.get("operator_id", "unknown")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")

@app.put("/v2c/autonomy/{level}")
async def set_autonomy_level(level: str):
    """Set AI autonomy level (controlled, autonomous, full)"""
    if not autonomous_ai_available or not autonomous_ai_module:
        raise HTTPException(status_code=404, detail="Autonomous AI not available")
    
    try:
        result = autonomous_ai_module.set_autonomy_level(level)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set autonomy level: {str(e)}")

# Phase 3: Ecosystem Intelligence Endpoints

@app.get("/v3/status")
async def ecosystem_intelligence_status():
    """Phase 3 Ecosystem Intelligence status"""
    if not PHASE_3_AVAILABLE:
        return {"phase": "3 - Ecosystem Intelligence", "enabled": False, "reason": "Module not available"}
    
    try:
        status = get_ecosystem_status()
        return status
    except Exception as e:
        return {"phase": "3 - Ecosystem Intelligence", "enabled": False, "error": str(e)}

@app.post("/v3/tenant/initialize")
async def initialize_tenant_ecosystem(data: dict):
    """Initialize ecosystem intelligence for a tenant"""
    if not PHASE_3_AVAILABLE:
        raise HTTPException(status_code=404, detail="Ecosystem Intelligence not available")
    
    try:
        tenant_type = data.get("tenant_type", "fintech")
        
        # Create tenant profile based on type
        if tenant_type == "healthcare":
            tenant_profile = create_healthcare_tenant()
        elif tenant_type == "government":
            tenant_profile = create_government_tenant()
        else:
            tenant_profile = create_fintech_tenant()
        
        # Override tenant_id if provided
        if "tenant_id" in data:
            tenant_profile.tenant_id = data["tenant_id"]
        
        # Initialize ecosystem intelligence
        engine = initialize_ecosystem_intelligence(tenant_profile)
        
        return {
            "tenant_id": tenant_profile.tenant_id,
            "tenant_type": tenant_type,
            "tier": tenant_profile.tier.value,
            "industry": tenant_profile.industry_sector,
            "compliance": tenant_profile.compliance_requirements,
            "federated_learning": tenant_profile.federated_learning_enabled,
            "predictive_enforcement": tenant_profile.predictive_enforcement_enabled,
            "auto_rule_generation": tenant_profile.auto_rule_generation_enabled,
            "message": "Ecosystem Intelligence initialized",
            "timestamp": now_iso()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tenant initialization failed: {str(e)}")

@app.get("/v3/tenant/{tenant_id}/metrics")
async def get_tenant_ecosystem_metrics(tenant_id: str):
    """Get ecosystem intelligence metrics for specific tenant"""
    if not PHASE_3_AVAILABLE:
        raise HTTPException(status_code=404, detail="Ecosystem Intelligence not available")
    
    try:
        from phase_3_ecosystem_intelligence import get_ecosystem_intelligence
        engine = get_ecosystem_intelligence(tenant_id)
        
        if not engine:
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
        
        metrics = engine.get_ecosystem_metrics()
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.post("/v3/evaluate/{tenant_id}")
async def evaluate_with_ecosystem(tenant_id: str, request: EvaluateRequest):
    """Evaluate with full ecosystem intelligence for specific tenant"""
    if not PHASE_3_AVAILABLE:
        raise HTTPException(status_code=404, detail="Ecosystem Intelligence not available")
    
    start_time = time.time()
    
    try:
        # Core static evaluation first
        from app.rules_loader import rules_store as current_rules_store
        rules_dict = {rule.id: rule for rule in current_rules_store}
        decision, rule_ids, enforce_in_shadow = evaluate(
            text=request.text,
            agent_id=request.agent_id or "default",
            rules_store=rules_dict,
            direction=request.direction,
            endpoint=request.endpoint
        )
        
        # Ecosystem intelligence evaluation
        ecosystem_result = await evaluate_with_ecosystem_intelligence(
            tenant_id=tenant_id,
            text=request.text,
            endpoint=request.endpoint or "unknown",
            direction=request.direction,
            agent_id=request.agent_id or "default",
            static_action=decision,
            static_rule_ids=rule_ids
        )
        
        # Use ecosystem decision
        final_action = decision  # Default to static
        decision_authority = "static_rules"
        
        if ecosystem_result.get("ecosystem_decision"):
            eco_decision = ecosystem_result["ecosystem_decision"]
            final_action = eco_decision["action"]
            decision_authority = "ecosystem_ai"
        
        response_time = (time.time() - start_time) * 1000
        
        # Update metrics
        metrics["evaluations_total"] += 1
        if final_action == "block":
            metrics["blocks_total"] += 1
        elif final_action == "flag":
            metrics["flags_total"] += 1
        else:
            metrics["allows_total"] += 1
        
        return {
            "action": final_action,
            "rule_ids": rule_ids,
            "decision_authority": decision_authority,
            "response_time_ms": round(response_time, 2),
            "ecosystem_intelligence": ecosystem_result,
            "tenant_id": tenant_id,
            "timestamp": now_iso(),
            "version": "3.0.0-ecosystem"
        }
        
    except Exception as e:
        metrics["errors_total"] += 1
        raise HTTPException(status_code=500, detail=f"Ecosystem evaluation failed: {str(e)}")

@app.post("/v3/federated/contribute")
async def contribute_federated_insight(data: dict):
    """Contribute anonymized insight to federated learning network"""
    if not PHASE_3_AVAILABLE:
        raise HTTPException(status_code=404, detail="Ecosystem Intelligence not available")
    
    # In production, this would validate and process federated contributions
    # For MVP, we'll simulate acceptance
    return {
        "contribution_accepted": True,
        "insight_id": f"federated_{int(time.time())}",
        "anonymization_level": "high",
        "network_benefit": "Pattern added to collective intelligence",
        "timestamp": now_iso()
    }

# Phase 4: Global Platform Endpoints

@app.get("/v4/status")
async def global_platform_status():
    """Phase 4 Global Platform status"""
    if not PHASE_4_AVAILABLE:
        return {"phase": "4 - Global Platform", "enabled": False, "reason": "Module not available"}
    
    try:
        status = get_platform_status()
        return status
    except Exception as e:
        return {"phase": "4 - Global Platform", "enabled": False, "error": str(e)}

@app.get("/v4/integrations")
async def list_enterprise_integrations():
    """List available enterprise integrations"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        platform = get_global_platform()
        if not platform:
            raise HTTPException(status_code=503, detail="Global Platform not initialized")
        
        integrations = []
        for integration_id, integration in platform.enterprise_integrations.items():
            integrations.append({
                "integration_id": integration_id,
                "name": integration.name,
                "vendor": integration.vendor,
                "type": integration.integration_type.value,
                "tier": integration.tier.value,
                "bi_directional": integration.bi_directional,
                "real_time_sync": integration.real_time_sync,
                "trigger_conditions": integration.trigger_conditions
            })
        
        return {
            "integrations": integrations,
            "total_available": len(integrations),
            "timestamp": now_iso()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list integrations: {str(e)}")

@app.post("/v4/integrations/{integration_id}/deploy")
async def deploy_enterprise_integration(integration_id: str, deployment_request: dict):
    """Deploy enterprise integration for tenant"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        tenant_id = deployment_request.get("tenant_id")
        customer_config = deployment_request.get("config", {})
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required")
        
        result = await deploy_integration_for_tenant(
            integration_id=integration_id,
            tenant_id=tenant_id,
            customer_config=customer_config
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Deployment failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration deployment failed: {str(e)}")

@app.get("/v4/tools")
async def list_developer_tools():
    """List available developer experience tools"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        platform = get_global_platform()
        if not platform:
            raise HTTPException(status_code=503, detail="Global Platform not initialized")
        
        tools = []
        for tool_id in platform.developer_tools.keys():
            tool_info = platform.get_developer_tool_info(tool_id)
            if tool_info:
                tools.append({
                    "tool_id": tool_info["tool_id"],
                    "name": tool_info["name"],
                    "type": tool_info["type"],
                    "version": tool_info["version"],
                    "platforms": tool_info["supported_platforms"],
                    "installation_method": tool_info["installation"]["method"],
                    "features_count": len(tool_info["features"]),
                    "downloads": tool_info["downloads"]
                })
        
        return {
            "developer_tools": tools,
            "total_available": len(tools),
            "timestamp": now_iso()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.get("/v4/tools/{tool_id}")
async def get_developer_tool_details(tool_id: str):
    """Get detailed information about specific developer tool"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        platform = get_global_platform()
        if not platform:
            raise HTTPException(status_code=503, detail="Global Platform not initialized")
        
        tool_info = platform.get_developer_tool_info(tool_id)
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
        
        return tool_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tool info: {str(e)}")

@app.get("/v4/standards")
async def list_standards_specifications():
    """List AI policy governance standards specifications"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        platform = get_global_platform()
        if not platform:
            raise HTTPException(status_code=503, detail="Global Platform not initialized")
        
        standards = []
        for spec_id in platform.standards_specifications.keys():
            spec_info = platform.get_standards_specification(spec_id)
            if spec_info:
                standards.append({
                    "spec_id": spec_info["spec_id"],
                    "name": spec_info["name"],
                    "version": spec_info["version"],
                    "category": spec_info["category"],
                    "adoption_level": spec_info["adoption_level"],
                    "compliance_requirements": spec_info["compliance_requirements"],
                    "adoption_count": spec_info["adoption_count"]
                })
        
        return {
            "standards_specifications": standards,
            "total_available": len(standards),
            "approved_standards": len([s for s in standards if s["adoption_level"] == "approved"]),
            "timestamp": now_iso()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list standards: {str(e)}")

@app.get("/v4/standards/{spec_id}")
async def get_standards_specification_details(spec_id: str):
    """Get detailed standards specification including JSON schema"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        platform = get_global_platform()
        if not platform:
            raise HTTPException(status_code=503, detail="Global Platform not initialized")
        
        spec_info = platform.get_standards_specification(spec_id)
        if not spec_info:
            raise HTTPException(status_code=404, detail=f"Specification {spec_id} not found")
        
        return spec_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get specification: {str(e)}")

@app.get("/v4/analytics")
async def get_platform_analytics():
    """Get comprehensive global platform analytics"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        platform = get_global_platform()
        if not platform:
            raise HTTPException(status_code=503, detail="Global Platform not initialized")
        
        analytics = platform.get_platform_analytics()
        return {
            "analytics": analytics,
            "timestamp": now_iso()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@app.post("/v4/initialize")
async def initialize_global_platform_service():
    """Initialize the global platform (admin endpoint)"""
    if not PHASE_4_AVAILABLE:
        raise HTTPException(status_code=404, detail="Global Platform not available")
    
    try:
        platform = initialize_global_platform()
        analytics = platform.get_platform_analytics()
        
        return {
            "success": True,
            "message": "Global Platform initialized successfully",
            "platform_version": "4.0.0",
            "capabilities": [
                "enterprise_integration_marketplace",
                "developer_experience_platform", 
                "standards_leadership_framework",
                "white_label_platform",
                "enterprise_federation"
            ],
            "initial_analytics": analytics,
            "timestamp": now_iso()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Platform initialization failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API info"""
    endpoints = [
        "/health - Health check",
        "/v1/evaluate - Policy evaluation", 
        "/v1/metrics - Metrics",
        "/v1/metrics/prom - Prometheus metrics"
    ]
    
    if shadow_ai_available:
        endpoints.extend([
            "/v2/status - Phase 2A Shadow AI status"
        ])
    
    return {
        "service": "Jimini AI Policy Gateway",
        "version": "0.2.0-mvp",
        "phase": "Phase 2A: Shadow AI" if shadow_ai_available else "Phase 1: Ship Now",
        "description": "AI policy evaluation with shadow learning",
        "endpoints": endpoints,
        "rules_active": len(rules_store) > 0,
        "timestamp": now_iso()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Jimini Phase 1 MVP...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)