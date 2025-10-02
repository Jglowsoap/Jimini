#!/usr/bin/env python3
"""
Phase 2B: AI Assist Mode - "AI Recommends, Humans Decide"

This module enables AI-powered policy recommendations while maintaining
human oversight and static rule enforcement for safety.

Key Features:
- AI recommendations run in parallel to static rules
- Static rules always take precedence (safety first)
- AI provides insights and suggested actions
- Human oversight for all AI recommendations
- Data collection for autonomous mode training
"""

import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

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


@dataclass
class AIRecommendation:
    """AI policy recommendation with confidence and reasoning"""
    action: str  # "block", "flag", "allow"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    rule_suggestions: List[str]
    risk_score: Optional[float] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class AssistModeResult:
    """Combined result from static rules + AI recommendations"""
    # Static rule decision (always enforced)
    static_action: str
    static_rule_ids: List[str]
    static_message: str
    
    # AI recommendations (advisory only)
    ai_recommendation: Optional[AIRecommendation]
    ai_available: bool
    
    # Comparison analysis
    agreement: bool  # Do AI and static rules agree?
    confidence_delta: Optional[float] = None
    learning_opportunity: bool = False
    
    # Metadata
    evaluation_time_ms: float = 0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AIAssistEngine:
    """
    AI Assist Mode Engine - Provides AI recommendations alongside static rule enforcement
    
    Phase 2B Design Principles:
    1. Static rules ALWAYS take precedence (safety first)
    2. AI runs in parallel for recommendations only
    3. Human oversight required for AI suggestions
    4. Data collection for autonomous mode training
    5. Zero production risk from AI decisions
    """
    
    def __init__(self):
        self.policy_optimizer = None
        self.threat_forecaster = None
        self.policy_recommender = None
        self.ai_enabled = False
        
        # Metrics
        self.recommendations_generated = 0
        self.agreements_count = 0
        self.disagreements_count = 0
        self.high_confidence_recommendations = 0
        
        # Initialize AI components if available
        if AI_MODULES_AVAILABLE:
            try:
                self._initialize_ai_components()
                self.ai_enabled = True
                print("🧠 AI Assist Mode: Initialized successfully")
            except Exception as e:
                print(f"⚠️ AI Assist Mode: Failed to initialize - {e}")
                self.ai_enabled = False
        else:
            print("⚠️ AI Assist Mode: AI modules not available")
    
    def _initialize_ai_components(self):
        """Initialize AI intelligence components"""
        # Reinforcement Learning Policy Optimizer
        self.policy_optimizer = PolicyOptimizer(
            learning_rate=0.01,
            exploration_rate=0.1,
            context_dimensions=["text_length", "endpoint_type", "time_of_day", "user_pattern"]
        )
        
        # Threat Forecasting
        self.threat_forecaster = ThreatForecaster()
        
        # Policy Recommender
        self.policy_recommender = PolicyRecommender()
        
        print(f"   ✅ PolicyOptimizer initialized with {len(self.policy_optimizer.context_dimensions)} context dimensions")
        print(f"   ✅ ThreatForecaster initialized")
        print(f"   ✅ PolicyRecommender initialized")
    
    async def evaluate_with_ai_assist(
        self, 
        text: str, 
        static_action: str, 
        static_rule_ids: List[str], 
        static_message: str,
        endpoint: str = "/unknown",
        direction: str = "outbound",
        agent_id: str = "default"
    ) -> AssistModeResult:
        """
        Evaluate request with AI assistance while maintaining static rule enforcement
        
        Args:
            text: Content to evaluate
            static_action: Decision from static rules (always enforced)
            static_rule_ids: Rules that triggered in static evaluation
            static_message: Message from static evaluation
            endpoint: API endpoint being accessed
            direction: Request direction (inbound/outbound)
            agent_id: Agent or user identifier
            
        Returns:
            AssistModeResult with both static decision and AI recommendation
        """
        start_time = time.time()
        
        # Always start with static rule decision (safety first)
        result = AssistModeResult(
            static_action=static_action,
            static_rule_ids=static_rule_ids,
            static_message=static_message,
            ai_recommendation=None,
            ai_available=self.ai_enabled,
            agreement=True  # Default to agreement if no AI recommendation
        )
        
        # Generate AI recommendation if AI is available
        if self.ai_enabled and self.policy_optimizer:
            try:
                ai_recommendation = await self._generate_ai_recommendation(
                    text, endpoint, direction, agent_id, static_action, static_rule_ids
                )
                result.ai_recommendation = ai_recommendation
                
                # Analyze agreement between static and AI
                if ai_recommendation:
                    result.agreement = (static_action == ai_recommendation.action)
                    result.confidence_delta = ai_recommendation.confidence
                    result.learning_opportunity = (
                        not result.agreement and ai_recommendation.confidence > 0.7
                    )
                    
                    # Update metrics
                    self.recommendations_generated += 1
                    if result.agreement:
                        self.agreements_count += 1
                    else:
                        self.disagreements_count += 1
                    if ai_recommendation.confidence > 0.8:
                        self.high_confidence_recommendations += 1
                        
            except Exception as e:
                print(f"⚠️ AI recommendation failed: {e}")
                # AI failure doesn't affect static rule decision
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result
    
    async def _generate_ai_recommendation(
        self,
        text: str,
        endpoint: str,
        direction: str,
        agent_id: str,
        static_action: str,
        static_rule_ids: List[str]
    ) -> Optional[AIRecommendation]:
        """Generate AI policy recommendation based on learned patterns"""
        
        try:
            # Create context for AI evaluation
            context = RLContext(
                text_length=len(text),
                endpoint_type=self._classify_endpoint(endpoint),
                time_of_day=datetime.now().hour,
                user_pattern=self._analyze_user_pattern(agent_id),
                direction=direction,
                static_rules_triggered=len(static_rule_ids)
            )
            
            # Get AI recommendation from policy optimizer
            ai_action, confidence = self.policy_optimizer.recommend_action(
                context=context,
                text_content=text
            )
            
            # Generate reasoning for the recommendation
            reasoning = self._generate_reasoning(
                ai_action, confidence, context, text, static_action
            )
            
            # Get suggested rule improvements
            rule_suggestions = await self._get_rule_suggestions(
                text, ai_action, static_rule_ids, confidence
            )
            
            # Calculate risk score if threat forecaster available
            risk_score = None
            if self.threat_forecaster:
                risk_score = self.threat_forecaster.assess_threat_level(text, context)
            
            return AIRecommendation(
                action=ai_action,
                confidence=confidence,
                reasoning=reasoning,
                rule_suggestions=rule_suggestions,
                risk_score=risk_score
            )
            
        except Exception as e:
            print(f"⚠️ AI recommendation generation failed: {e}")
            return None
    
    def _classify_endpoint(self, endpoint: str) -> str:
        """Classify endpoint type for AI context"""
        if "/api/" in endpoint:
            return "api"
        elif "/chat" in endpoint or "/message" in endpoint:
            return "chat"
        elif "/upload" in endpoint or "/file" in endpoint:
            return "file_transfer"
        elif "/auth" in endpoint or "/login" in endpoint:
            return "authentication"
        else:
            return "general"
    
    def _analyze_user_pattern(self, agent_id: str) -> str:
        """Analyze user behavioral patterns for AI context"""
        # Simple pattern analysis (could be enhanced with historical data)
        if agent_id == "default" or not agent_id:
            return "anonymous"
        elif agent_id.startswith("admin"):
            return "administrative"
        elif agent_id.startswith("bot"):
            return "automated"
        else:
            return "standard_user"
    
    def _generate_reasoning(
        self, 
        ai_action: str, 
        confidence: float, 
        context: RLContext, 
        text: str, 
        static_action: str
    ) -> str:
        """Generate human-readable reasoning for AI recommendation"""
        
        reasons = []
        
        # Confidence-based reasoning
        if confidence > 0.9:
            reasons.append("High confidence based on similar historical patterns")
        elif confidence > 0.7:
            reasons.append("Moderate confidence from learned behavioral patterns")
        else:
            reasons.append("Low confidence - limited similar training data")
        
        # Context-based reasoning
        if context.text_length > 500:
            reasons.append("Long content increases potential for policy violations")
        
        if context.endpoint_type == "file_transfer":
            reasons.append("File transfer endpoints have higher data leakage risk")
        elif context.endpoint_type == "chat":
            reasons.append("Chat endpoints frequently contain PII and sensitive data")
        
        # Time-based reasoning
        if context.time_of_day < 6 or context.time_of_day > 22:
            reasons.append("Off-hours activity increases suspicious behavior probability")
        
        # Agreement analysis
        if ai_action != static_action:
            reasons.append(f"AI recommendation differs from static rules ({static_action})")
            if ai_action == "block" and static_action == "allow":
                reasons.append("AI detected potential threat not caught by static rules")
            elif ai_action == "allow" and static_action == "block":
                reasons.append("AI suggests static rules may be over-restrictive")
        else:
            reasons.append("AI recommendation aligns with static rule evaluation")
        
        return ". ".join(reasons) + "."
    
    async def _get_rule_suggestions(
        self, 
        text: str, 
        ai_action: str, 
        static_rule_ids: List[str], 
        confidence: float
    ) -> List[str]:
        """Generate rule improvement suggestions based on AI analysis"""
        
        suggestions = []
        
        # High confidence disagreements suggest rule gaps
        if confidence > 0.8 and ai_action == "block" and not static_rule_ids:
            suggestions.append("Consider adding pattern rule for similar content")
            
        # Suggest rule refinements
        if len(static_rule_ids) > 2:
            suggestions.append("Multiple rule triggers - consider rule consolidation")
        
        # Pattern-based suggestions
        if self.policy_recommender:
            try:
                ai_suggestions = self.policy_recommender.suggest_rule_improvements(
                    text, ai_action, static_rule_ids
                )
                suggestions.extend(ai_suggestions)
            except Exception as e:
                print(f"⚠️ Rule suggestion generation failed: {e}")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def get_assist_mode_metrics(self) -> Dict[str, Any]:
        """Get AI Assist Mode performance metrics"""
        agreement_rate = (
            self.agreements_count / max(self.recommendations_generated, 1)
        ) * 100
        
        high_confidence_rate = (
            self.high_confidence_recommendations / max(self.recommendations_generated, 1)
        ) * 100
        
        return {
            "ai_enabled": self.ai_enabled,
            "recommendations_generated": self.recommendations_generated,
            "agreement_rate_percent": round(agreement_rate, 1),
            "disagreements_count": self.disagreements_count,
            "high_confidence_rate_percent": round(high_confidence_rate, 1),
            "learning_opportunities": self.disagreements_count,
            "status": "active" if self.ai_enabled else "disabled"
        }
    
    async def learn_from_feedback(
        self, 
        text: str, 
        ai_recommendation: AIRecommendation, 
        human_decision: str, 
        feedback_reason: str = ""
    ):
        """
        Learn from human feedback on AI recommendations
        
        Args:
            text: Original text that was evaluated
            ai_recommendation: The AI's recommendation
            human_decision: The final human decision
            feedback_reason: Optional reason for human decision
        """
        
        if not self.ai_enabled or not self.policy_optimizer:
            return
        
        try:
            # Convert human feedback to reward signal
            reward_value = self._calculate_reward(
                ai_recommendation.action, human_decision, ai_recommendation.confidence
            )
            
            # Create reward object for learning
            reward = RLReward(
                value=reward_value,
                feedback_type="human_override" if human_decision != ai_recommendation.action else "human_confirmation",
                confidence_adjustment=0.1 if human_decision == ai_recommendation.action else -0.2,
                reason=feedback_reason
            )
            
            # Update AI model with feedback
            context = RLContext(
                text_length=len(text),
                endpoint_type="feedback_session",
                time_of_day=datetime.now().hour,
                user_pattern="human_trainer"
            )
            
            self.policy_optimizer.update_from_feedback(context, reward)
            
            print(f"🧠 AI learned from human feedback: {human_decision} (reward: {reward_value})")
            
        except Exception as e:
            print(f"⚠️ AI learning from feedback failed: {e}")
    
    def _calculate_reward(self, ai_action: str, human_decision: str, confidence: float) -> float:
        """Calculate reward signal for AI learning"""
        
        if ai_action == human_decision:
            # AI was correct - positive reward scaled by confidence
            return 1.0 * confidence
        else:
            # AI was wrong - negative reward scaled by confidence
            return -1.0 * confidence


# Global AI Assist Engine instance
ai_assist_engine = AIAssistEngine()


async def evaluate_with_ai_assist(
    text: str,
    static_action: str,
    static_rule_ids: List[str],
    static_message: str,
    **kwargs
) -> AssistModeResult:
    """
    Convenience function for AI-assisted evaluation
    
    This is the main entry point for Phase 2B AI Assist Mode
    """
    return await ai_assist_engine.evaluate_with_ai_assist(
        text=text,
        static_action=static_action,
        static_rule_ids=static_rule_ids,
        static_message=static_message,
        **kwargs
    )


def get_ai_assist_status() -> Dict[str, Any]:
    """Get current AI Assist Mode status and metrics"""
    return {
        "phase": "2B - AI Assist Mode",
        "ai_enabled": ai_assist_engine.ai_enabled,
        "ai_modules_available": AI_MODULES_AVAILABLE,
        "metrics": ai_assist_engine.get_assist_mode_metrics(),
        "description": "AI provides recommendations while static rules enforce decisions",
        "safety_model": "Human oversight required, static rules always take precedence"
    }


if __name__ == "__main__":
    # Test AI Assist Mode
    import asyncio
    
    async def test_ai_assist():
        print("🧠 Testing AI Assist Mode...")
        
        # Test case 1: SSN detection
        result = await evaluate_with_ai_assist(
            text="My SSN is 123-45-6789",
            static_action="block",
            static_rule_ids=["IL-AI-4.2"],
            static_message="SSN detected",
            endpoint="/test",
            direction="outbound"
        )
        
        print(f"Test 1 - SSN:")
        print(f"  Static: {result.static_action}")
        print(f"  AI Available: {result.ai_available}")
        if result.ai_recommendation:
            print(f"  AI Recommends: {result.ai_recommendation.action} (confidence: {result.ai_recommendation.confidence:.2f})")
            print(f"  Agreement: {result.agreement}")
        
        # Test case 2: Safe text
        result2 = await evaluate_with_ai_assist(
            text="Hello world",
            static_action="allow",
            static_rule_ids=[],
            static_message="No violations detected",
            endpoint="/test",
            direction="outbound"
        )
        
        print(f"\nTest 2 - Safe text:")
        print(f"  Static: {result2.static_action}")
        print(f"  AI Available: {result2.ai_available}")
        if result2.ai_recommendation:
            print(f"  AI Recommends: {result2.ai_recommendation.action} (confidence: {result2.ai_recommendation.confidence:.2f})")
            print(f"  Agreement: {result2.agreement}")
        
        # Show metrics
        status = get_ai_assist_status()
        print(f"\nAI Assist Status:")
        print(json.dumps(status, indent=2))
    
    asyncio.run(test_ai_assist())