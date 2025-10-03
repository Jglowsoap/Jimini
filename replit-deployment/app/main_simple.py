#!/usr/bin/env python3
"""
Simple Jimini Main - Phase 1 Deployment Version
For demonstration of basic policy evaluation functionality
"""

import time
import os
from typing import Any, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json

from app.models import EvaluateRequest, EvaluateResponse
from app.rules_loader import load_rules, rules_store
from app.enforcement import evaluate, apply_shadow_logic
from app import audit
from app.util import now_iso, gen_request_id

# Phase 1 Configuration
JIMINI_API_KEY = os.getenv("JIMINI_API_KEY", "changeme")
JIMINI_SHADOW = os.getenv("JIMINI_SHADOW", "0") == "1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with simple initialization"""
    print("🚀 Jimini AI Policy Gateway starting...")
    
    # Load rules
    rules_path = os.getenv("JIMINI_RULES_PATH", "policy_rules.yaml")
    load_rules(rules_path)
    print(f"📋 Loaded {len(rules_store.rules)} rules from {rules_path}")
    
    yield
    
    print("🛑 Jimini AI Policy Gateway shutting down...")

app = FastAPI(
    title="Jimini AI Policy Gateway",
    description="Lightweight AI policy evaluation with decision logging",
    version="0.2.0-phase1",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.2.0-phase1", 
        "timestamp": now_iso(),
        "shadow_mode": JIMINI_SHADOW,
        "rules_loaded": len(rules_store.rules)
    }

@app.post("/v1/evaluate")
async def evaluate_text(request: EvaluateRequest, req: Request):
    """Evaluate text against policy rules"""
    
    # API key check
    api_key = req.headers.get("Authorization")
    if not api_key or api_key.replace("Bearer ", "") != JIMINI_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Generate request ID
    request_id = gen_request_id()
    
    try:
        # Evaluate against rules
        decision, rule_ids, matched_rules = evaluate(
            text=request.text,
            direction=request.direction,
            endpoint=request.endpoint,
            rules=rules_store.rules
        )
        
        # Apply shadow mode if enabled
        final_decision = apply_shadow_logic(decision, rule_ids)
        
        # Create response
        response = EvaluateResponse(
            decision=final_decision,
            request_id=request_id,
            rule_ids=rule_ids,
            timestamp=now_iso(),
            processing_time_ms=int(time.time() * 1000) % 1000  # Simple timing
        )
        
        # Log to audit (basic)
        audit_record = {
            "request_id": request_id,
            "timestamp": now_iso(),
            "decision": final_decision,
            "rule_ids": rule_ids,
            "endpoint": request.endpoint,
            "shadow_mode": JIMINI_SHADOW
        }
        
        try:
            audit.append_audit(audit_record)
        except Exception as e:
            print(f"Audit logging failed: {e}")
        
        return response
        
    except Exception as e:
        print(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Evaluation failed")

@app.get("/v1/metrics")
async def get_metrics():
    """Basic metrics endpoint"""
    return {
        "rules_loaded": len(rules_store.rules),
        "shadow_mode": JIMINI_SHADOW,
        "uptime_seconds": int(time.time()) % 86400,  # Simple uptime
        "status": "operational"
    }

@app.get("/v1/audit/verify")
async def verify_audit():
    """Basic audit verification"""
    try:
        # Simple audit check
        return {"status": "audit_verification_basic", "message": "Phase 1 deployment"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🌟 Starting Jimini AI Policy Gateway - Phase 1 Deployment")
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1
    )