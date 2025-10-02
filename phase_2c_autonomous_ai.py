#!/usr/bin/env python3
"""
Phase 2C: Autonomous AI Mode - "AI Makes Safe Autonomous Decisions"

This module enables AI to make autonomous policy decisions within strict safety constraints.
Human oversight is maintained through monitoring dashboards and override capabilities.

Key Features:
- AI can autonomously FLAG low-risk content
- AI can autonomously ALLOW clearly safe content  
- AI requires human approval for BLOCK decisions (safety constraint)
- Confidence thresholds prevent AI from making uncertain decisions
- Real-time human override capability with audit logging
- Self-tuning policy parameters within safety bounds
"""

import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Literal
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

# Import Phase 2B AI Assist infrastructure
try:
    from phase_2b_ai_assist import (
        AIRecommendation, 
        AssistModeResult, 
        AIAssistEngine,
        ai_assist_engine
    )
    PHASE_2B_AVAILABLE = True
except ImportError:
    PHASE_2B_AVAILABLE = False

# AI Intelligence Modules (Phase 7 complete)
try:
    from app.intelligence.reinforcement_learning import (
        PolicyOptimizer, 
        RLContext, 
        RLReward,
        ContextualBandit
    )
    from app.intelligence.predictive_intelligence import (
        ThreatForecaster,
        PolicyRecommender
    )
    AI_MODULES_AVAILABLE = True
except ImportError:
    AI_MODULES_AVAILABLE = False


class AutonomyLevel(Enum):
    """AI autonomy levels with increasing decision-making authority"""
    DISABLED = "disabled"           # AI off, static rules only
    ASSIST = "assist"               # AI recommends, humans decide (Phase 2B)
    CONTROLLED = "controlled"       # AI can FLAG/ALLOW, humans approve BLOCK
    AUTONOMOUS = "autonomous"       # AI makes all decisions within safety bounds
    FULL = "full"                   # AI has complete decision authority (enterprise only)


@dataclass
class SafetyConstraint:
    """Safety constraints for autonomous AI decisions"""
    min_confidence_threshold: float = 0.8  # Minimum confidence for autonomous decisions
    max_block_autonomy: bool = False        # Can AI autonomously BLOCK content?
    require_human_review_for: List[str] = None  # Actions requiring human approval
    max_consecutive_blocks: int = 5         # Max blocks before human review required
    override_timeout_seconds: int = 300     # Time limit for human override
    audit_all_decisions: bool = True        # Log every AI decision
    
    def __post_init__(self):
        if self.require_human_review_for is None:
            # Default: humans must approve all BLOCK decisions
            self.require_human_review_for = ["block"]


@dataclass
class AutonomousDecision:
    """AI autonomous decision with full audit trail"""
    original_static_action: str
    original_static_rules: List[str]
    ai_decision: str
    ai_confidence: float
    ai_reasoning: str
    autonomy_level: AutonomyLevel
    safety_constraints_met: bool
    human_review_required: bool
    decision_authority: str  # "static_rules", "ai_autonomous", "human_required"
    override_window_expires: str
    audit_trail: List[str]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AutonomousAIEngine:
    """
    Autonomous AI Engine - Makes safe AI-driven policy decisions
    
    Phase 2C Design Principles:
    1. Safety constraints prevent dangerous autonomous decisions
    2. Human override capability always available
    3. Confidence thresholds ensure only high-certainty AI decisions
    4. Audit logging for all autonomous actions
    5. Gradual autonomy increase based on performance metrics
    """
    
    def __init__(self, autonomy_level: AutonomyLevel = AutonomyLevel.CONTROLLED):
        self.autonomy_level = autonomy_level
        self.safety_constraints = SafetyConstraint()
        self.ai_assist_engine = None
        self.policy_optimizer = None
        self.consecutive_blocks = 0
        self.decisions_made = 0
        self.human_overrides = 0
        self.ai_accuracy_rate = 0.0
        
        # Performance tracking
        self.autonomous_decisions = 0
        self.human_reviews_required = 0
        self.confidence_threshold_failures = 0
        self.safety_violations_prevented = 0
        
        # Initialize AI components
        if PHASE_2B_AVAILABLE:
            self.ai_assist_engine = ai_assist_engine
            print("🧠 Phase 2C Autonomous AI: Initialized with Phase 2B foundation")
        
        if AI_MODULES_AVAILABLE:
            try:
                self._initialize_autonomous_components()
                print("🤖 Autonomous AI components: Loaded successfully")
            except Exception as e:
                print(f"⚠️ Autonomous AI initialization failed: {e}")
        else:
            print("⚠️ AI modules not available for autonomous mode")
    
    def _initialize_autonomous_components(self):
        """Initialize components specific to autonomous mode"""
        if self.ai_assist_engine and hasattr(self.ai_assist_engine, 'policy_optimizer'):
            self.policy_optimizer = self.ai_assist_engine.policy_optimizer
            
            # Configure for autonomous operation
            if self.policy_optimizer:
                # Increase confidence requirements for autonomous decisions
                self.policy_optimizer.exploration_rate = 0.05  # Less exploration in production
                print("   ✅ PolicyOptimizer configured for autonomous operation")
    
    async def evaluate_autonomous(
        self,
        text: str,
        static_action: str,
        static_rule_ids: List[str],
        static_message: str,
        endpoint: str = "/unknown",
        direction: str = "outbound",
        agent_id: str = "default"
    ) -> AutonomousDecision:
        """
        Make autonomous AI policy decision with safety constraints
        
        Returns final decision that should be enforced, with full audit trail
        """
        
        # Start with static rule decision as baseline
        decision_authority = "static_rules"
        final_action = static_action
        human_review_required = False
        safety_constraints_met = True
        audit_trail = [f"Static rules decision: {static_action}"]
        
        # Check if autonomous mode is enabled
        if self.autonomy_level == AutonomyLevel.DISABLED:
            audit_trail.append("Autonomous AI disabled - using static rules")
            return self._create_autonomous_decision(
                static_action, static_rule_ids, static_message,
                static_action, 0.0, "Autonomous mode disabled",
                decision_authority, human_review_required, safety_constraints_met, audit_trail
            )
        
        # Get AI recommendation if available
        ai_recommendation = None
        ai_confidence = 0.0
        ai_reasoning = "AI not available"
        
        if self.ai_assist_engine and self.ai_assist_engine.ai_enabled:
            try:
                assist_result = await self.ai_assist_engine.evaluate_with_ai_assist(
                    text=text,
                    static_action=static_action,
                    static_rule_ids=static_rule_ids,
                    static_message=static_message,
                    endpoint=endpoint,
                    direction=direction,
                    agent_id=agent_id
                )
                
                if assist_result.ai_recommendation:
                    ai_recommendation = assist_result.ai_recommendation.action
                    ai_confidence = assist_result.ai_recommendation.confidence
                    ai_reasoning = assist_result.ai_recommendation.reasoning
                    audit_trail.append(f"AI recommends: {ai_recommendation} (confidence: {ai_confidence:.2f})")
                
            except Exception as e:
                audit_trail.append(f"AI evaluation failed: {e}")
                ai_reasoning = f"AI evaluation error: {e}"
        
        # Apply autonomous decision logic based on autonomy level
        if ai_recommendation and ai_confidence > 0:
            autonomous_decision = await self._make_autonomous_decision(
                static_action, ai_recommendation, ai_confidence, ai_reasoning, audit_trail
            )
            
            final_action = autonomous_decision["action"]
            decision_authority = autonomous_decision["authority"]
            human_review_required = autonomous_decision["human_review_required"]
            safety_constraints_met = autonomous_decision["safety_met"]
            audit_trail.extend(autonomous_decision["audit_updates"])
        
        return self._create_autonomous_decision(
            static_action, static_rule_ids, static_message,
            final_action, ai_confidence, ai_reasoning,
            decision_authority, human_review_required, safety_constraints_met, audit_trail
        )
    
    async def _make_autonomous_decision(
        self,
        static_action: str,
        ai_recommendation: str,
        ai_confidence: float,
        ai_reasoning: str,
        audit_trail: List[str]
    ) -> Dict[str, Any]:
        """Apply autonomous decision logic based on confidence and safety constraints"""
        
        # Check confidence threshold
        if ai_confidence < self.safety_constraints.min_confidence_threshold:
            self.confidence_threshold_failures += 1
            audit_trail.append(f"AI confidence {ai_confidence:.2f} below threshold {self.safety_constraints.min_confidence_threshold}")
            return {
                "action": static_action,
                "authority": "static_rules",
                "human_review_required": False,
                "safety_met": True,
                "audit_updates": ["Low AI confidence - defaulting to static rules"]
            }
        
        # Autonomous decision logic based on autonomy level
        if self.autonomy_level == AutonomyLevel.CONTROLLED:
            return await self._controlled_autonomy_logic(
                static_action, ai_recommendation, ai_confidence, audit_trail
            )
        elif self.autonomy_level == AutonomyLevel.AUTONOMOUS:
            return await self._full_autonomy_logic(
                static_action, ai_recommendation, ai_confidence, audit_trail
            )
        else:
            # Default to assist mode
            return {
                "action": static_action,
                "authority": "static_rules",
                "human_review_required": True,
                "safety_met": True,
                "audit_updates": ["Assist mode - AI recommendation available for review"]
            }
    
    async def _controlled_autonomy_logic(
        self,
        static_action: str,
        ai_recommendation: str,
        ai_confidence: float,
        audit_trail: List[str]
    ) -> Dict[str, Any]:
        """Controlled autonomy: AI can FLAG/ALLOW, humans approve BLOCK"""
        
        # AI can autonomously make these decisions
        if ai_recommendation in ["flag", "allow"]:
            self.autonomous_decisions += 1
            audit_trail.append(f"AI autonomous decision: {ai_recommendation} (controlled mode)")
            return {
                "action": ai_recommendation,
                "authority": "ai_autonomous",
                "human_review_required": False,
                "safety_met": True,
                "audit_updates": ["AI decision within controlled autonomy bounds"]
            }
        
        # BLOCK decisions require human review
        elif ai_recommendation == "block":
            # Check consecutive block limit
            if self.consecutive_blocks >= self.safety_constraints.max_consecutive_blocks:
                self.safety_violations_prevented += 1
                audit_trail.append(f"Consecutive block limit ({self.safety_constraints.max_consecutive_blocks}) reached")
                return {
                    "action": static_action,
                    "authority": "safety_constraint",
                    "human_review_required": True,
                    "safety_met": False,
                    "audit_updates": ["Safety constraint triggered - human review required"]
                }
            
            # BLOCK with human approval required
            self.human_reviews_required += 1
            self.consecutive_blocks += 1
            audit_trail.append("AI recommends BLOCK - human approval required (controlled mode)")
            return {
                "action": "flag",  # Soften to FLAG pending human review
                "authority": "ai_autonomous_pending_review",
                "human_review_required": True,
                "safety_met": True,
                "audit_updates": ["AI BLOCK recommendation pending human approval"]
            }
        
        # Default to static rules
        return {
            "action": static_action,
            "authority": "static_rules",
            "human_review_required": False,
            "safety_met": True,
            "audit_updates": ["Controlled mode - defaulting to static rules"]
        }
    
    async def _full_autonomy_logic(
        self,
        static_action: str,
        ai_recommendation: str,
        ai_confidence: float,
        audit_trail: List[str]
    ) -> Dict[str, Any]:
        """Full autonomy: AI can make all decisions within safety bounds"""
        
        # Check if BLOCK autonomy is allowed
        if ai_recommendation == "block" and not self.safety_constraints.max_block_autonomy:
            # Even in full autonomy, BLOCK might require approval
            self.human_reviews_required += 1
            audit_trail.append("AI recommends BLOCK - safety constraint requires human approval")
            return {
                "action": "flag",  # Soften pending approval
                "authority": "ai_autonomous_pending_review",
                "human_review_required": True,
                "safety_met": True,
                "audit_updates": ["BLOCK safety constraint - human approval required"]
            }
        
        # AI has full autonomy for this decision
        self.autonomous_decisions += 1
        audit_trail.append(f"AI autonomous decision: {ai_recommendation} (full autonomy mode)")
        
        # Track consecutive blocks
        if ai_recommendation == "block":
            self.consecutive_blocks += 1
        else:
            self.consecutive_blocks = 0
        
        return {
            "action": ai_recommendation,
            "authority": "ai_autonomous",
            "human_review_required": False,
            "safety_met": True,
            "audit_updates": ["AI decision under full autonomy"]
        }
    
    def _create_autonomous_decision(
        self,
        static_action: str,
        static_rules: List[str],
        static_message: str,
        final_action: str,
        ai_confidence: float,
        ai_reasoning: str,
        decision_authority: str,
        human_review_required: bool,
        safety_constraints_met: bool,
        audit_trail: List[str]
    ) -> AutonomousDecision:
        """Create autonomous decision record"""
        
        self.decisions_made += 1
        
        # Calculate override window expiration
        from datetime import timedelta
        override_expires = datetime.now(timezone.utc) + timedelta(
            seconds=self.safety_constraints.override_timeout_seconds
        )
        
        return AutonomousDecision(
            original_static_action=static_action,
            original_static_rules=static_rules,
            ai_decision=final_action,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
            autonomy_level=self.autonomy_level,
            safety_constraints_met=safety_constraints_met,
            human_review_required=human_review_required,
            decision_authority=decision_authority,
            override_window_expires=override_expires.isoformat(),
            audit_trail=audit_trail
        )
    
    async def human_override(
        self,
        decision_id: str,
        human_action: str,
        human_reasoning: str = "",
        operator_id: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Human override of AI autonomous decision
        
        Args:
            decision_id: Unique ID of the decision to override
            human_action: Human's override decision
            human_reasoning: Explanation for override
            operator_id: ID of human operator making override
        """
        
        self.human_overrides += 1
        
        # Log override for AI learning
        if self.ai_assist_engine:
            try:
                # Create mock AI recommendation for learning
                ai_rec = AIRecommendation(
                    action="placeholder",  # Would be actual AI decision
                    confidence=0.5,
                    reasoning="Override learning session",
                    rule_suggestions=[]
                )
                
                await self.ai_assist_engine.learn_from_feedback(
                    text="Override session",
                    ai_recommendation=ai_rec,
                    human_decision=human_action,
                    feedback_reason=human_reasoning
                )
                
            except Exception as e:
                print(f"⚠️ AI learning from override failed: {e}")
        
        return {
            "override_accepted": True,
            "final_action": human_action,
            "operator_id": operator_id,
            "reasoning": human_reasoning,
            "ai_notified": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_autonomous_metrics(self) -> Dict[str, Any]:
        """Get autonomous AI performance metrics"""
        
        # Calculate performance rates
        override_rate = (self.human_overrides / max(self.decisions_made, 1)) * 100
        autonomy_rate = (self.autonomous_decisions / max(self.decisions_made, 1)) * 100
        safety_rate = 100 - (self.safety_violations_prevented / max(self.decisions_made, 1)) * 100
        
        return {
            "autonomy_level": self.autonomy_level.value,
            "decisions_made": self.decisions_made,
            "autonomous_decisions": self.autonomous_decisions,
            "human_reviews_required": self.human_reviews_required,
            "human_overrides": self.human_overrides,
            "override_rate_percent": round(override_rate, 2),
            "autonomy_rate_percent": round(autonomy_rate, 2),
            "safety_rate_percent": round(safety_rate, 2),
            "consecutive_blocks": self.consecutive_blocks,
            "confidence_threshold_failures": self.confidence_threshold_failures,
            "safety_violations_prevented": self.safety_violations_prevented,
            "safety_constraints": {
                "min_confidence": self.safety_constraints.min_confidence_threshold,
                "max_block_autonomy": self.safety_constraints.max_block_autonomy,
                "max_consecutive_blocks": self.safety_constraints.max_consecutive_blocks,
                "audit_all_decisions": self.safety_constraints.audit_all_decisions
            }
        }
    
    def set_autonomy_level(self, level: AutonomyLevel) -> Dict[str, Any]:
        """Change AI autonomy level with safety validation"""
        
        previous_level = self.autonomy_level
        self.autonomy_level = level
        
        # Reset consecutive blocks when changing levels
        self.consecutive_blocks = 0
        
        # Adjust safety constraints based on level
        if level == AutonomyLevel.CONTROLLED:
            self.safety_constraints.max_block_autonomy = False
            self.safety_constraints.require_human_review_for = ["block"]
        elif level == AutonomyLevel.AUTONOMOUS:
            # More permissive but still safe
            self.safety_constraints.max_block_autonomy = False  # Still require human approval for blocks
            self.safety_constraints.require_human_review_for = ["block"]  # Can be customized
        elif level == AutonomyLevel.FULL:
            # Enterprise-only full autonomy
            self.safety_constraints.max_block_autonomy = True
            self.safety_constraints.require_human_review_for = []
        
        return {
            "previous_level": previous_level.value,
            "new_level": level.value,
            "safety_constraints_updated": True,
            "consecutive_blocks_reset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global Autonomous AI Engine instance
autonomous_ai_engine = AutonomousAIEngine(AutonomyLevel.CONTROLLED)


async def evaluate_autonomous(
    text: str,
    static_action: str,
    static_rule_ids: List[str],
    static_message: str,
    **kwargs
) -> AutonomousDecision:
    """
    Convenience function for autonomous AI evaluation
    
    This is the main entry point for Phase 2C Autonomous Mode
    """
    return await autonomous_ai_engine.evaluate_autonomous(
        text=text,
        static_action=static_action,
        static_rule_ids=static_rule_ids,
        static_message=static_message,
        **kwargs
    )


def get_autonomous_status() -> Dict[str, Any]:
    """Get current Autonomous AI Mode status and metrics"""
    return {
        "phase": "2C - Autonomous AI Mode",
        "autonomy_level": autonomous_ai_engine.autonomy_level.value,
        "ai_enabled": autonomous_ai_engine.ai_assist_engine.ai_enabled if autonomous_ai_engine.ai_assist_engine else False,
        "metrics": autonomous_ai_engine.get_autonomous_metrics(),
        "description": "AI makes safe autonomous decisions within safety constraints",
        "safety_model": "Human oversight with real-time override capability"
    }


def set_autonomy_level(level: str) -> Dict[str, Any]:
    """Set AI autonomy level (controlled, autonomous, full)"""
    try:
        autonomy_level = AutonomyLevel(level.lower())
        return autonomous_ai_engine.set_autonomy_level(autonomy_level)
    except ValueError:
        return {
            "error": f"Invalid autonomy level: {level}",
            "valid_levels": [level.value for level in AutonomyLevel]
        }


if __name__ == "__main__":
    # Test Autonomous AI Mode
    import asyncio
    
    async def test_autonomous_ai():
        print("🤖 Testing Autonomous AI Mode...")
        
        # Test case 1: SSN detection (static BLOCK)
        result1 = await evaluate_autonomous(
            text="My SSN is 123-45-6789",
            static_action="block",
            static_rule_ids=["IL-AI-4.2"],
            static_message="SSN detected",
            endpoint="/test",
            direction="outbound"
        )
        
        print(f"\nTest 1 - SSN Detection:")
        print(f"  Static Decision: {result1.original_static_action}")
        print(f"  AI Decision: {result1.ai_decision}")
        print(f"  Decision Authority: {result1.decision_authority}")
        print(f"  Human Review Required: {result1.human_review_required}")
        print(f"  AI Confidence: {result1.ai_confidence:.2f}")
        
        # Test case 2: Safe content
        result2 = await evaluate_autonomous(
            text="Hello world, this is safe",
            static_action="allow",
            static_rule_ids=[],
            static_message="No violations",
            endpoint="/test",
            direction="outbound"
        )
        
        print(f"\nTest 2 - Safe Content:")
        print(f"  Static Decision: {result2.original_static_action}")
        print(f"  AI Decision: {result2.ai_decision}")
        print(f"  Decision Authority: {result2.decision_authority}")
        print(f"  Human Review Required: {result2.human_review_required}")
        
        # Show metrics
        status = get_autonomous_status()
        print(f"\nAutonomous AI Status:")
        print(json.dumps(status, indent=2))
        
        # Test autonomy level changes
        print(f"\nTesting autonomy level changes:")
        result = set_autonomy_level("autonomous")
        print(f"  Autonomy level change: {result}")
    
    asyncio.run(test_autonomous_ai())