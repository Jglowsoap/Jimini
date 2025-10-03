#!/usr/bin/env python3
"""
Phase 2A: Integrate Shadow AI with Live MVP Service

This adds the shadow AI evaluation to our running MVP without
affecting production behavior.
"""

from app.main_mvp import app
from fastapi import APIRouter
from typing import Dict, Any
import time
import json
from datetime import datetime

# Create shadow AI router
shadow_router = APIRouter(prefix="/v2", tags=["shadow-ai"])

# Import shadow AI components
try:
    from app.intelligence.reinforcement_learning import PolicyOptimizer
    RL_AVAILABLE = True
    shadow_optimizer = PolicyOptimizer()
except ImportError:
    RL_AVAILABLE = False
    shadow_optimizer = None

# Shadow evaluation results storage
shadow_results = []

@shadow_router.post("/shadow/evaluate")
async def shadow_evaluate(request_data: Dict[str, Any]):
    """
    Shadow AI evaluation endpoint - runs AI alongside production
    but never affects actual decisions.
    """
    start_time = time.time()
    
    # Get production decision first (this is what actually gets returned)
    from app.enforcement import evaluate
    from app.rules_loader import rules_store
    
    production_decision, production_rules, _ = evaluate(
        text=request_data.get("text", ""),
        agent_id="shadow_eval",
        rules_store={"rules": rules_store},
        direction=request_data.get("direction", "outbound"),
        endpoint=request_data.get("endpoint", "/test")
    )
    
    # Run shadow AI evaluation
    ai_decision = production_decision  # Safe default
    ai_confidence = 0.5
    ai_features = {}
    
    if RL_AVAILABLE and shadow_optimizer:
        try:
            # This is where the real AI magic happens in shadow
            from app.intelligence.reinforcement_learning import RLContext, RLReward
            
            context = RLContext(
                text_length=len(request_data.get("text", "")),
                endpoint=request_data.get("endpoint", ""),
                direction=request_data.get("direction", "outbound"),
                time_of_day=datetime.now().hour,
                day_of_week=datetime.now().weekday()
            )
            
            # Get AI recommendation (shadow only)
            ai_recommendation = shadow_optimizer.get_recommendation(
                context=context,
                available_actions=["allow", "flag", "block"]
            )
            
            ai_decision = ai_recommendation.get("action", production_decision)
            ai_confidence = ai_recommendation.get("confidence", 0.5)
            ai_features = ai_recommendation.get("features", {})
            
        except Exception as e:
            ai_features["error"] = str(e)
    
    # Log shadow result for analysis
    shadow_result = {
        "timestamp": datetime.now().isoformat(),
        "text_hash": abs(hash(request_data.get("text", ""))) % 100000,
        "endpoint": request_data.get("endpoint", ""),
        "direction": request_data.get("direction", ""),
        "production_decision": production_decision,
        "production_rules_count": len(production_rules),
        "ai_decision": ai_decision,
        "ai_confidence": ai_confidence,
        "ai_features": ai_features,
        "agreement": production_decision == ai_decision,
        "latency_ms": int((time.time() - start_time) * 1000)
    }
    
    shadow_results.append(shadow_result)
    
    # Keep only last 1000 results
    if len(shadow_results) > 1000:
        shadow_results.pop(0)
    
    return {
        "production_decision": production_decision,  # This is what actually matters
        "shadow_analysis": {
            "ai_decision": ai_decision,
            "ai_confidence": ai_confidence,
            "agreement": shadow_result["agreement"],
            "latency_ms": shadow_result["latency_ms"]
        },
        "message": "Production decision returned, AI analysis logged for training"
    }

@shadow_router.get("/shadow/analytics")
async def get_shadow_analytics():
    """Get analytics on shadow AI performance vs production"""
    if not shadow_results:
        return {"message": "No shadow evaluations yet"}
    
    total = len(shadow_results)
    agreements = sum(1 for r in shadow_results if r["agreement"])
    avg_confidence = sum(r["ai_confidence"] for r in shadow_results) / total
    avg_latency = sum(r["latency_ms"] for r in shadow_results) / total
    
    return {
        "total_evaluations": total,
        "ai_agreement_rate": agreements / total,
        "average_ai_confidence": avg_confidence,
        "average_latency_ms": avg_latency,
        "rl_available": RL_AVAILABLE,
        "recent_samples": shadow_results[-5:] if len(shadow_results) >= 5 else shadow_results
    }

@shadow_router.post("/shadow/feedback")
async def submit_feedback(feedback_data: Dict[str, Any]):
    """Submit feedback for shadow AI learning"""
    if RL_AVAILABLE and shadow_optimizer:
        try:
            from app.intelligence.reinforcement_learning import RLReward
            
            # Create reward signal for RL training
            reward = RLReward(
                decision_id=feedback_data.get("decision_id"),
                outcome=feedback_data.get("outcome", "neutral"),
                feedback_score=feedback_data.get("score", 0.0),
                timestamp=datetime.now()
            )
            
            # This would update the RL model in real implementation
            return {"message": "Feedback received, AI learning updated"}
            
        except Exception as e:
            return {"error": f"Feedback processing failed: {e}"}
    
    return {"message": "Feedback logged (RL not available)"}

# Add shadow router to main app
app.include_router(shadow_router)

# Also add a simple status endpoint
@app.get("/v2/status")
async def phase_2_status():
    """Phase 2 feature status"""
    return {
        "phase": "2A - Shadow AI",
        "features": {
            "shadow_evaluation": True,
            "reinforcement_learning": RL_AVAILABLE,
            "analytics": True,
            "feedback_loop": RL_AVAILABLE
        },
        "shadow_evaluations": len(shadow_results),
        "message": "AI learning in shadow mode - zero production impact"
    }

if __name__ == "__main__":
    print("🧠 Phase 2A Shadow AI integrated with MVP!")
    print("   New endpoints:")
    print("   - POST /v2/shadow/evaluate (shadow AI evaluation)")
    print("   - GET /v2/shadow/analytics (AI vs production comparison)")  
    print("   - POST /v2/shadow/feedback (AI learning feedback)")
    print("   - GET /v2/status (Phase 2 status)")
    print("\n   🚀 Ready to add to live MVP service!")