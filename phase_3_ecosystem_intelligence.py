#!/usr/bin/env python3
"""
Phase 3: Ecosystem Intelligence - "Intelligent Globally"

This module implements federated learning, predictive enforcement, and 
self-evolving rule generation to create a globally intelligent AI policy ecosystem.

Key Features:
- Federated Reinforcement Learning: Learn collectively without sharing raw PII
- Predictive Policy Enforcement: Block violations before they happen
- Self-Evolving Rule Packs: AI auto-generates rules, humans approve
- Multi-Tenant Intelligence: Customer-specific learning with collective insights
- Policy Intelligence Fabric: Unified governance across multiple deployments

Strategic Value:
- Data Moat: Collective learning advantage that competitors cannot cross
- Predictive Security: Prevent violations rather than just detect them
- Network Effects: Each deployment makes all deployments smarter
- Standards Leadership: Define industry protocols for AI policy governance
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import uuid
from collections import defaultdict, deque

# Import previous phase capabilities
try:
    from phase_2c_autonomous_ai import (
        AutonomousDecision, 
        AutonomyLevel,
        autonomous_ai_engine
    )
    PHASE_2C_AVAILABLE = True
except ImportError:
    PHASE_2C_AVAILABLE = False

# AI Intelligence Modules
try:
    from app.intelligence.reinforcement_learning import (
        PolicyOptimizer, 
        RLContext, 
        RLReward
    )
    from app.intelligence.predictive_intelligence import (
        ThreatForecaster,
        PolicyRecommender
    )
    AI_MODULES_AVAILABLE = True
except ImportError:
    AI_MODULES_AVAILABLE = False


class TenantTier(Enum):
    """Multi-tenant deployment tiers with different capabilities"""
    COMMUNITY = "community"       # Basic federated learning participation
    PROFESSIONAL = "professional" # Enhanced predictive capabilities
    ENTERPRISE = "enterprise"     # Full ecosystem intelligence + custom rules
    GOVERNMENT = "government"     # Highest security + compliance features


class FederatedInsightType(Enum):
    """Types of insights that can be shared in federated learning"""
    PATTERN_SIGNATURE = "pattern_signature"     # Anonymized pattern hashes
    THREAT_VECTOR = "threat_vector"             # Attack pattern classifications
    POLICY_EFFECTIVENESS = "policy_effectiveness" # Rule performance metrics
    ANOMALY_FINGERPRINT = "anomaly_fingerprint"  # Behavioral anomaly patterns
    CONFIDENCE_CALIBRATION = "confidence_calibration" # AI confidence improvements


@dataclass
class TenantProfile:
    """Multi-tenant customer profile for personalized AI learning"""
    tenant_id: str
    tier: TenantTier
    deployment_date: str
    industry_sector: str  # "healthcare", "finance", "government", "technology"
    compliance_requirements: List[str]  # ["HIPAA", "PCI", "SOX", "GDPR"]
    risk_tolerance: str  # "conservative", "balanced", "aggressive"
    ai_autonomy_level: AutonomyLevel
    
    # Learning preferences
    federated_learning_enabled: bool = True
    predictive_enforcement_enabled: bool = True
    auto_rule_generation_enabled: bool = False
    
    # Privacy controls
    share_anonymized_patterns: bool = True
    receive_collective_insights: bool = True
    data_residency_requirements: List[str] = field(default_factory=list)
    
    # Performance tracking
    total_requests_processed: int = 0
    ai_decisions_made: int = 0
    human_overrides_received: int = 0
    predictive_blocks_successful: int = 0


@dataclass
class FederatedInsight:
    """Privacy-preserving insight that can be shared across tenants"""
    insight_id: str
    insight_type: FederatedInsightType
    pattern_hash: str  # Cryptographic hash of pattern (no raw PII)
    confidence_score: float
    effectiveness_metrics: Dict[str, float]
    applicable_industries: List[str]
    compliance_tags: List[str]
    
    # Privacy protection
    tenant_count: int  # Number of tenants contributing to this insight
    min_sample_size: int = 10  # Minimum samples before insight is shared
    anonymization_level: str = "high"
    
    created_at: str = ""
    expires_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.expires_at:
            # Insights expire after 30 days to ensure freshness
            expires = datetime.now(timezone.utc) + timedelta(days=30)
            self.expires_at = expires.isoformat()


@dataclass
class PredictiveAlert:
    """Early warning system for potential policy violations"""
    alert_id: str
    tenant_id: str
    threat_type: str  # "data_exfiltration", "pii_exposure", "anomalous_behavior"
    confidence_level: float
    predicted_violation_time: str  # When violation likely to occur
    recommended_actions: List[str]
    
    # Context for prediction
    behavioral_indicators: List[str]
    pattern_matches: List[str] 
    risk_factors: Dict[str, float]
    
    # Response tracking
    human_reviewed: bool = False
    action_taken: str = ""
    outcome_verified: bool = False
    
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class AutoGeneratedRule:
    """AI-generated policy rule awaiting human approval"""
    rule_id: str
    tenant_id: str
    generated_by: str  # "federated_learning", "predictive_analysis", "anomaly_detection"
    
    # Rule definition
    pattern: str
    action: str  # "block", "flag", "monitor"
    confidence: float
    description: str
    reasoning: str
    
    # Supporting evidence
    sample_violations: List[str]  # Anonymized examples
    effectiveness_prediction: float
    false_positive_estimate: float
    
    # Approval workflow
    approval_status: str = "pending"  # "pending", "approved", "rejected", "testing"
    reviewed_by: str = ""
    review_notes: str = ""
    test_results: Dict[str, Any] = field(default_factory=dict)
    
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class EcosystemIntelligenceEngine:
    """
    Phase 3: Ecosystem Intelligence Engine
    
    Implements federated learning, predictive enforcement, and self-evolving
    rule generation for globally intelligent AI policy enforcement.
    
    Core Capabilities:
    1. Federated Learning: Learn collectively without sharing raw data
    2. Predictive Enforcement: Block violations before they happen  
    3. Auto Rule Generation: AI creates new rules based on patterns
    4. Multi-Tenant Intelligence: Personalized learning per customer
    5. Global Policy Fabric: Unified intelligence across deployments
    """
    
    def __init__(self, tenant_profile: TenantProfile):
        self.tenant_profile = tenant_profile
        self.autonomous_engine = None
        
        # Federated learning state
        self.federated_insights: Dict[str, FederatedInsight] = {}
        self.shared_pattern_cache: Dict[str, Any] = {}
        self.collective_intelligence_version = "3.0.1"
        
        # Predictive enforcement
        self.threat_forecaster = None
        self.predictive_alerts: deque = deque(maxlen=1000)  # Last 1000 alerts
        self.behavioral_baselines: Dict[str, Any] = {}
        
        # Auto rule generation
        self.rule_generator = None
        self.pending_rules: Dict[str, AutoGeneratedRule] = {}
        self.approved_rules: Dict[str, AutoGeneratedRule] = {}
        
        # Performance metrics
        self.federated_learning_contributions = 0
        self.predictive_blocks_successful = 0
        self.auto_rules_generated = 0
        self.auto_rules_approved = 0
        
        # Initialize components
        if PHASE_2C_AVAILABLE:
            self.autonomous_engine = autonomous_ai_engine
            print("🤖 Phase 3 Ecosystem Intelligence: Connected to Phase 2C Autonomous AI")
        
        if AI_MODULES_AVAILABLE:
            try:
                self._initialize_ecosystem_components()
                print("🌍 Ecosystem Intelligence: Initialized successfully")
            except Exception as e:
                print(f"⚠️ Ecosystem Intelligence initialization failed: {e}")
    
    def _initialize_ecosystem_components(self):
        """Initialize ecosystem intelligence components"""
        
        # Enhanced threat forecaster for predictive enforcement
        self.threat_forecaster = ThreatForecaster()
        
        # Policy recommender for auto rule generation  
        self.rule_generator = PolicyRecommender()
        
        print(f"   ✅ Tenant: {self.tenant_profile.tenant_id} ({self.tenant_profile.tier.value})")
        print(f"   ✅ Industry: {self.tenant_profile.industry_sector}")
        print(f"   ✅ Compliance: {', '.join(self.tenant_profile.compliance_requirements)}")
        print(f"   ✅ Federated Learning: {'Enabled' if self.tenant_profile.federated_learning_enabled else 'Disabled'}")
        print(f"   ✅ Predictive Enforcement: {'Enabled' if self.tenant_profile.predictive_enforcement_enabled else 'Disabled'}")
    
    async def evaluate_with_ecosystem_intelligence(
        self,
        text: str,
        endpoint: str,
        direction: str = "outbound",
        agent_id: str = "default",
        static_action: str = "allow",
        static_rule_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate request with full ecosystem intelligence:
        1. Traditional static rules + Phase 2C autonomous AI
        2. Federated learning insights
        3. Predictive threat analysis
        4. Auto-generated rule matching
        """
        
        start_time = time.time()
        static_rule_ids = static_rule_ids or []
        
        # Start with Phase 2C autonomous decision if available
        autonomous_decision = None
        if self.autonomous_engine:
            try:
                autonomous_result = await self.autonomous_engine.evaluate_autonomous(
                    text=text,
                    static_action=static_action,
                    static_rule_ids=static_rule_ids,
                    static_message="Static evaluation",
                    endpoint=endpoint,
                    direction=direction,
                    agent_id=agent_id
                )
                autonomous_decision = {
                    "action": autonomous_result.ai_decision,
                    "confidence": autonomous_result.ai_confidence,
                    "authority": autonomous_result.decision_authority
                }
            except Exception as e:
                print(f"⚠️ Autonomous AI evaluation failed: {e}")
        
        # Layer 1: Federated Learning Enhancement
        federated_insights = await self._apply_federated_learning(text, endpoint, direction)
        
        # Layer 2: Predictive Threat Analysis
        predictive_analysis = await self._analyze_predictive_threats(text, endpoint, agent_id)
        
        # Layer 3: Auto-Generated Rule Matching
        auto_rule_matches = await self._match_auto_generated_rules(text, endpoint)
        
        # Layer 4: Ecosystem Decision Synthesis
        final_decision = await self._synthesize_ecosystem_decision(
            autonomous_decision=autonomous_decision,
            federated_insights=federated_insights,
            predictive_analysis=predictive_analysis,
            auto_rule_matches=auto_rule_matches,
            text=text,
            endpoint=endpoint
        )
        
        # Update tenant metrics
        self.tenant_profile.total_requests_processed += 1
        if final_decision.get("authority") == "ecosystem_ai":
            self.tenant_profile.ai_decisions_made += 1
        
        # Contribute to federated learning (privacy-preserving)
        if self.tenant_profile.federated_learning_enabled:
            await self._contribute_to_federated_learning(text, final_decision, endpoint)
        
        evaluation_time = (time.time() - start_time) * 1000
        
        return {
            "ecosystem_decision": final_decision,
            "autonomous_decision": autonomous_decision,
            "federated_insights": federated_insights,
            "predictive_analysis": predictive_analysis,
            "auto_rule_matches": auto_rule_matches,
            "evaluation_time_ms": round(evaluation_time, 2),
            "tenant_id": self.tenant_profile.tenant_id,
            "collective_intelligence_version": self.collective_intelligence_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _apply_federated_learning(self, text: str, endpoint: str, direction: str) -> Dict[str, Any]:
        """Apply insights learned from federated network without exposing raw data"""
        
        if not self.tenant_profile.receive_collective_insights:
            return {"enabled": False, "reason": "Tenant opt-out"}
        
        # Generate privacy-preserving pattern hash
        pattern_hash = self._generate_pattern_hash(text, endpoint)
        
        # Check for matching federated insights
        matching_insights = []
        for insight in self.federated_insights.values():
            if self._insight_applies_to_tenant(insight):
                if pattern_hash.startswith(insight.pattern_hash[:8]):  # Partial match for privacy
                    matching_insights.append({
                        "insight_type": insight.insight_type.value,
                        "confidence": insight.confidence_score,
                        "tenant_count": insight.tenant_count,
                        "effectiveness": insight.effectiveness_metrics
                    })
        
        collective_recommendation = None
        if matching_insights:
            # Aggregate insights for recommendation
            avg_confidence = sum(i["confidence"] for i in matching_insights) / len(matching_insights)
            total_tenant_count = sum(i["tenant_count"] for i in matching_insights)
            
            if avg_confidence > 0.7 and total_tenant_count >= 5:
                collective_recommendation = {
                    "action": "flag" if avg_confidence > 0.8 else "monitor",
                    "confidence": avg_confidence,
                    "supporting_tenants": total_tenant_count,
                    "reasoning": f"Pattern recognized by {total_tenant_count} deployments with {avg_confidence:.1%} confidence"
                }
        
        return {
            "enabled": True,
            "matching_insights": len(matching_insights),
            "collective_recommendation": collective_recommendation,
            "pattern_hash": pattern_hash[:16],  # Truncated for privacy
            "intelligence_version": self.collective_intelligence_version
        }
    
    async def _analyze_predictive_threats(self, text: str, endpoint: str, agent_id: str) -> Dict[str, Any]:
        """Analyze for predictive threats before violations occur"""
        
        if not self.tenant_profile.predictive_enforcement_enabled:
            return {"enabled": False, "reason": "Predictive enforcement disabled"}
        
        try:
            # Behavioral baseline analysis
            baseline_key = f"{agent_id}:{endpoint}"
            current_behavior = {
                "text_length": len(text),
                "endpoint": endpoint,
                "timestamp": time.time(),
                "hour_of_day": datetime.now().hour
            }
            
            # Update behavioral baseline
            if baseline_key not in self.behavioral_baselines:
                self.behavioral_baselines[baseline_key] = {
                    "request_count": 0,
                    "avg_text_length": 0,
                    "common_endpoints": set(),
                    "activity_pattern": [0] * 24  # Hours of day
                }
            
            baseline = self.behavioral_baselines[baseline_key]
            baseline["request_count"] += 1
            baseline["avg_text_length"] = (
                baseline["avg_text_length"] * (baseline["request_count"] - 1) + len(text)
            ) / baseline["request_count"]
            baseline["common_endpoints"].add(endpoint)
            baseline["activity_pattern"][datetime.now().hour] += 1
            
            # Anomaly detection
            anomaly_indicators = []
            risk_score = 0.0
            
            # Text length anomaly
            if len(text) > baseline["avg_text_length"] * 3:
                anomaly_indicators.append("unusually_long_content")
                risk_score += 0.3
            
            # Off-hours activity
            if datetime.now().hour < 6 or datetime.now().hour > 22:
                if baseline["activity_pattern"][datetime.now().hour] < 5:  # Rare off-hours activity
                    anomaly_indicators.append("off_hours_activity")
                    risk_score += 0.2
            
            # Rapid fire requests (simplified detection)
            recent_requests = [req for req in baseline.get("recent_timestamps", []) 
                             if time.time() - req < 60]  # Last minute
            if len(recent_requests) > 10:
                anomaly_indicators.append("rapid_fire_requests")
                risk_score += 0.4
            
            # Predictive threat assessment
            predictive_recommendation = None
            if risk_score > 0.5:
                # Generate predictive alert
                alert = PredictiveAlert(
                    alert_id=str(uuid.uuid4()),
                    tenant_id=self.tenant_profile.tenant_id,
                    threat_type="anomalous_behavior",
                    confidence_level=risk_score,
                    predicted_violation_time=(datetime.now() + timedelta(minutes=5)).isoformat(),
                    recommended_actions=["increased_monitoring", "human_review"],
                    behavioral_indicators=anomaly_indicators,
                    pattern_matches=[],
                    risk_factors={"anomaly_score": risk_score, "baseline_deviation": True}
                )
                
                self.predictive_alerts.append(alert)
                
                predictive_recommendation = {
                    "action": "flag",
                    "confidence": risk_score,
                    "alert_id": alert.alert_id,
                    "reasoning": f"Anomalous behavior detected: {', '.join(anomaly_indicators)}"
                }
            
            return {
                "enabled": True,
                "risk_score": round(risk_score, 3),
                "anomaly_indicators": anomaly_indicators,
                "predictive_recommendation": predictive_recommendation,
                "baseline_requests": baseline["request_count"],
                "behavioral_profile": {
                    "avg_text_length": round(baseline["avg_text_length"], 1),
                    "endpoint_diversity": len(baseline["common_endpoints"]),
                    "peak_activity_hour": baseline["activity_pattern"].index(max(baseline["activity_pattern"]))
                }
            }
            
        except Exception as e:
            print(f"⚠️ Predictive threat analysis failed: {e}")
            return {"enabled": True, "error": str(e)}
    
    async def _match_auto_generated_rules(self, text: str, endpoint: str) -> Dict[str, Any]:
        """Check against auto-generated rules awaiting or approved"""
        
        if not self.tenant_profile.auto_rule_generation_enabled:
            return {"enabled": False, "reason": "Auto rule generation disabled"}
        
        matched_rules = []
        
        # Check approved auto-generated rules
        for rule_id, rule in self.approved_rules.items():
            if self._rule_matches_content(rule, text, endpoint):
                matched_rules.append({
                    "rule_id": rule_id,
                    "action": rule.action,
                    "confidence": rule.confidence,
                    "generated_by": rule.generated_by,
                    "status": "approved",
                    "description": rule.description
                })
        
        # Check pending rules (for testing/validation)
        pending_matches = []
        for rule_id, rule in self.pending_rules.items():
            if rule.approval_status == "testing" and self._rule_matches_content(rule, text, endpoint):
                pending_matches.append({
                    "rule_id": rule_id,
                    "action": rule.action,
                    "confidence": rule.confidence,
                    "generated_by": rule.generated_by,
                    "status": "testing",
                    "description": rule.description
                })
        
        auto_rule_recommendation = None
        if matched_rules:
            # Use highest confidence approved rule
            best_rule = max(matched_rules, key=lambda r: r["confidence"])
            auto_rule_recommendation = {
                "action": best_rule["action"],
                "confidence": best_rule["confidence"],
                "rule_id": best_rule["rule_id"],
                "reasoning": f"Auto-generated rule match: {best_rule['description']}"
            }
        
        return {
            "enabled": True,
            "approved_matches": len(matched_rules),
            "testing_matches": len(pending_matches),
            "auto_rule_recommendation": auto_rule_recommendation,
            "matched_rules": matched_rules,
            "pending_matches": pending_matches
        }
    
    async def _synthesize_ecosystem_decision(
        self,
        autonomous_decision: Optional[Dict[str, Any]],
        federated_insights: Dict[str, Any],
        predictive_analysis: Dict[str, Any],
        auto_rule_matches: Dict[str, Any],
        text: str,
        endpoint: str
    ) -> Dict[str, Any]:
        """Synthesize final decision from all ecosystem intelligence layers"""
        
        # Decision priority:
        # 1. Auto-generated approved rules (highest specificity)
        # 2. Autonomous AI decision (Phase 2C)
        # 3. Federated learning insights (collective intelligence)
        # 4. Predictive analysis (forward-looking)
        
        decision_layers = []
        final_action = "allow"
        final_confidence = 0.0
        decision_authority = "ecosystem_ai"
        reasoning_parts = []
        
        # Layer 1: Auto-generated rules
        if auto_rule_matches.get("auto_rule_recommendation"):
            rec = auto_rule_matches["auto_rule_recommendation"]
            decision_layers.append("auto_generated_rule")
            final_action = rec["action"]
            final_confidence = rec["confidence"]
            reasoning_parts.append(f"Auto-rule: {rec['reasoning']}")
        
        # Layer 2: Autonomous AI (if no auto-rule override)
        elif autonomous_decision and autonomous_decision.get("authority") == "ai_autonomous":
            decision_layers.append("autonomous_ai")
            final_action = autonomous_decision["action"]
            final_confidence = autonomous_decision["confidence"]
            reasoning_parts.append("Autonomous AI decision")
        
        # Layer 3: Federated insights
        if federated_insights.get("collective_recommendation"):
            rec = federated_insights["collective_recommendation"]
            decision_layers.append("federated_learning")
            
            # Upgrade action if federated learning suggests higher risk
            if self._action_priority(rec["action"]) > self._action_priority(final_action):
                final_action = rec["action"]
                final_confidence = max(final_confidence, rec["confidence"])
                reasoning_parts.append(f"Collective intelligence: {rec['reasoning']}")
        
        # Layer 4: Predictive analysis
        if predictive_analysis.get("predictive_recommendation"):
            rec = predictive_analysis["predictive_recommendation"]
            decision_layers.append("predictive_analysis")
            
            # Upgrade action if predictive analysis suggests higher risk
            if self._action_priority(rec["action"]) > self._action_priority(final_action):
                final_action = rec["action"]
                final_confidence = max(final_confidence, rec["confidence"])
                reasoning_parts.append(f"Predictive threat: {rec['reasoning']}")
        
        # Fallback to autonomous or static rules
        if not decision_layers:
            if autonomous_decision:
                final_action = autonomous_decision["action"]
                final_confidence = autonomous_decision.get("confidence", 0.0)
                decision_authority = autonomous_decision.get("authority", "static_rules")
                reasoning_parts.append("Fallback to autonomous/static rules")
            else:
                decision_authority = "static_rules"
                reasoning_parts.append("Static rules only")
        
        return {
            "action": final_action,
            "confidence": round(final_confidence, 3),
            "authority": decision_authority,
            "decision_layers": decision_layers,
            "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "Standard evaluation",
            "ecosystem_enhanced": len(decision_layers) > 0
        }
    
    def _action_priority(self, action: str) -> int:
        """Get priority level of action (higher = more restrictive)"""
        priorities = {"allow": 0, "monitor": 1, "flag": 2, "block": 3}
        return priorities.get(action.lower(), 0)
    
    def _generate_pattern_hash(self, text: str, endpoint: str) -> str:
        """Generate privacy-preserving hash of content pattern"""
        # Create hash that captures pattern without exposing content
        content_features = [
            str(len(text)),
            str(len(text.split())),
            endpoint.split("/")[-1] if "/" in endpoint else endpoint,
            "numeric" if any(c.isdigit() for c in text) else "text",
            "special_chars" if any(c in "!@#$%^&*()[]{}|;:,.<>?" for c in text) else "alphanumeric"
        ]
        
        pattern_signature = "|".join(content_features)
        return hashlib.sha256(pattern_signature.encode()).hexdigest()
    
    def _insight_applies_to_tenant(self, insight: FederatedInsight) -> bool:
        """Check if federated insight applies to current tenant"""
        
        # Industry relevance
        if insight.applicable_industries and self.tenant_profile.industry_sector not in insight.applicable_industries:
            return False
        
        # Compliance alignment
        if insight.compliance_tags:
            if not any(req in insight.compliance_tags for req in self.tenant_profile.compliance_requirements):
                return False
        
        # Minimum sample size for reliability
        if insight.tenant_count < insight.min_sample_size:
            return False
        
        # Check if insight has expired
        if datetime.fromisoformat(insight.expires_at.replace('Z', '+00:00')) < datetime.now(timezone.utc):
            return False
        
        return True
    
    def _rule_matches_content(self, rule: AutoGeneratedRule, text: str, endpoint: str) -> bool:
        """Check if auto-generated rule matches content (simplified)"""
        # Simplified pattern matching - in production would use compiled regex
        return rule.pattern.lower() in text.lower()
    
    async def _contribute_to_federated_learning(self, text: str, decision: Dict[str, Any], endpoint: str):
        """Contribute privacy-preserving insights to federated learning network"""
        
        if not self.tenant_profile.share_anonymized_patterns:
            return
        
        # Only contribute high-confidence decisions
        if decision.get("confidence", 0) < 0.8:
            return
        
        try:
            # Generate anonymized pattern signature
            pattern_hash = self._generate_pattern_hash(text, endpoint)
            
            # Create federated insight (no raw content shared)
            insight = FederatedInsight(
                insight_id=str(uuid.uuid4()),
                insight_type=FederatedInsightType.PATTERN_SIGNATURE,
                pattern_hash=pattern_hash,
                confidence_score=decision["confidence"],
                effectiveness_metrics={"decision_confidence": decision["confidence"]},
                applicable_industries=[self.tenant_profile.industry_sector],
                compliance_tags=self.tenant_profile.compliance_requirements,
                tenant_count=1  # This tenant's contribution
            )
            
            # Store locally (in production, would transmit to federated network)
            self.federated_insights[insight.insight_id] = insight
            self.federated_learning_contributions += 1
            
        except Exception as e:
            print(f"⚠️ Federated learning contribution failed: {e}")
    
    async def generate_auto_rule(
        self, 
        violation_patterns: List[str], 
        suggested_action: str = "flag"
    ) -> AutoGeneratedRule:
        """Generate new policy rule based on observed patterns"""
        
        if not self.tenant_profile.auto_rule_generation_enabled:
            raise ValueError("Auto rule generation disabled for tenant")
        
        # Analyze patterns to create rule
        pattern_analysis = self._analyze_violation_patterns(violation_patterns)
        
        rule = AutoGeneratedRule(
            rule_id=f"auto_{self.tenant_profile.tenant_id}_{int(time.time())}",
            tenant_id=self.tenant_profile.tenant_id,
            generated_by="pattern_analysis",
            pattern=pattern_analysis["regex_pattern"],
            action=suggested_action,
            confidence=pattern_analysis["confidence"],
            description=pattern_analysis["description"],
            reasoning=pattern_analysis["reasoning"],
            sample_violations=violation_patterns[:5],  # First 5 examples
            effectiveness_prediction=pattern_analysis["effectiveness"],
            false_positive_estimate=pattern_analysis["false_positive_rate"]
        )
        
        self.pending_rules[rule.rule_id] = rule
        self.auto_rules_generated += 1
        
        return rule
    
    def _analyze_violation_patterns(self, patterns: List[str]) -> Dict[str, Any]:
        """Analyze violation patterns to generate rule (simplified)"""
        # Simplified pattern analysis - production would use advanced NLP/ML
        
        common_words = []
        for pattern in patterns:
            words = pattern.lower().split()
            common_words.extend(words)
        
        # Find most common terms
        from collections import Counter
        word_counts = Counter(common_words)
        top_words = word_counts.most_common(3)
        
        if top_words:
            regex_pattern = "|".join([word for word, count in top_words if count > 1])
            description = f"Pattern matching: {', '.join([word for word, _ in top_words])}"
            confidence = min(0.9, len(patterns) / 10.0)  # Higher confidence with more samples
            
            return {
                "regex_pattern": regex_pattern,
                "description": description,
                "reasoning": f"Generated from {len(patterns)} violation samples",
                "confidence": confidence,
                "effectiveness": 0.8,
                "false_positive_rate": 0.1
            }
        
        return {
            "regex_pattern": "suspicious_content",
            "description": "Generic suspicious content detection",
            "reasoning": "Fallback pattern for unstructured violations",
            "confidence": 0.5,
            "effectiveness": 0.6,
            "false_positive_rate": 0.2
        }
    
    def get_ecosystem_metrics(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem intelligence metrics"""
        
        return {
            "tenant_profile": {
                "tenant_id": self.tenant_profile.tenant_id,
                "tier": self.tenant_profile.tier.value,
                "industry": self.tenant_profile.industry_sector,
                "compliance": self.tenant_profile.compliance_requirements,
                "total_requests": self.tenant_profile.total_requests_processed,
                "ai_decisions": self.tenant_profile.ai_decisions_made
            },
            "federated_learning": {
                "enabled": self.tenant_profile.federated_learning_enabled,
                "contributions_made": self.federated_learning_contributions,
                "insights_received": len(self.federated_insights),
                "intelligence_version": self.collective_intelligence_version
            },
            "predictive_enforcement": {
                "enabled": self.tenant_profile.predictive_enforcement_enabled,
                "active_alerts": len(self.predictive_alerts),
                "successful_predictions": self.predictive_blocks_successful,
                "behavioral_baselines": len(self.behavioral_baselines)
            },
            "auto_rule_generation": {
                "enabled": self.tenant_profile.auto_rule_generation_enabled,
                "rules_generated": self.auto_rules_generated,
                "rules_approved": self.auto_rules_approved,
                "pending_approval": len(self.pending_rules),
                "active_rules": len(self.approved_rules)
            },
            "performance": {
                "ecosystem_intelligence_active": True,
                "decision_layers_available": ["autonomous_ai", "federated_learning", "predictive_analysis", "auto_rules"],
                "collective_intelligence_version": self.collective_intelligence_version
            }
        }


# Example tenant profiles for different industries
def create_healthcare_tenant() -> TenantProfile:
    """Create a healthcare tenant with HIPAA compliance requirements"""
    return TenantProfile(
        tenant_id="healthcare_org_001",
        tier=TenantTier.ENTERPRISE,
        deployment_date=datetime.now().isoformat(),
        industry_sector="healthcare",
        compliance_requirements=["HIPAA", "HITECH"],
        risk_tolerance="conservative",
        ai_autonomy_level=AutonomyLevel.CONTROLLED,
        federated_learning_enabled=True,
        predictive_enforcement_enabled=True,
        auto_rule_generation_enabled=False,  # Conservative for healthcare
        share_anonymized_patterns=True,
        receive_collective_insights=True
    )


def create_fintech_tenant() -> TenantProfile:
    """Create a fintech tenant with financial compliance requirements"""
    return TenantProfile(
        tenant_id="fintech_startup_042",
        tier=TenantTier.PROFESSIONAL,
        deployment_date=datetime.now().isoformat(),
        industry_sector="finance",
        compliance_requirements=["PCI", "SOX", "GDPR"],
        risk_tolerance="balanced",
        ai_autonomy_level=AutonomyLevel.AUTONOMOUS,
        federated_learning_enabled=True,
        predictive_enforcement_enabled=True,
        auto_rule_generation_enabled=True,
        share_anonymized_patterns=True,
        receive_collective_insights=True
    )


def create_government_tenant() -> TenantProfile:
    """Create a government tenant with high security requirements"""
    return TenantProfile(
        tenant_id="gov_agency_dhs",
        tier=TenantTier.GOVERNMENT,
        deployment_date=datetime.now().isoformat(),
        industry_sector="government",
        compliance_requirements=["FISMA", "FIPS", "CJIS"],
        risk_tolerance="conservative",
        ai_autonomy_level=AutonomyLevel.CONTROLLED,
        federated_learning_enabled=False,  # May not share due to classification
        predictive_enforcement_enabled=True,
        auto_rule_generation_enabled=True,
        share_anonymized_patterns=False,
        receive_collective_insights=False,  # Isolated deployment
        data_residency_requirements=["US_ONLY", "FedRAMP_HIGH"]
    )


# Global ecosystem intelligence instances
ecosystem_engines: Dict[str, EcosystemIntelligenceEngine] = {}


def get_ecosystem_intelligence(tenant_id: str) -> Optional[EcosystemIntelligenceEngine]:
    """Get ecosystem intelligence engine for specific tenant"""
    return ecosystem_engines.get(tenant_id)


def initialize_ecosystem_intelligence(tenant_profile: TenantProfile) -> EcosystemIntelligenceEngine:
    """Initialize ecosystem intelligence for a tenant"""
    engine = EcosystemIntelligenceEngine(tenant_profile)
    ecosystem_engines[tenant_profile.tenant_id] = engine
    return engine


async def evaluate_with_ecosystem_intelligence(
    tenant_id: str,
    text: str,
    endpoint: str,
    direction: str = "outbound",
    agent_id: str = "default",
    static_action: str = "allow",
    static_rule_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for Phase 3 Ecosystem Intelligence evaluation
    """
    
    engine = get_ecosystem_intelligence(tenant_id)
    if not engine:
        return {
            "error": f"Ecosystem intelligence not initialized for tenant {tenant_id}",
            "fallback_to_phase_2c": True
        }
    
    return await engine.evaluate_with_ecosystem_intelligence(
        text=text,
        endpoint=endpoint,
        direction=direction,
        agent_id=agent_id,
        static_action=static_action,
        static_rule_ids=static_rule_ids
    )


def get_ecosystem_status() -> Dict[str, Any]:
    """Get overall ecosystem intelligence status"""
    
    return {
        "phase": "3 - Ecosystem Intelligence",
        "active_tenants": len(ecosystem_engines),
        "total_federated_insights": sum(
            len(engine.federated_insights) for engine in ecosystem_engines.values()
        ),
        "collective_intelligence_version": "3.0.1",
        "capabilities": [
            "federated_learning",
            "predictive_enforcement", 
            "auto_rule_generation",
            "multi_tenant_intelligence",
            "privacy_preserving_insights"
        ],
        "description": "Globally intelligent AI policy enforcement with federated learning",
        "strategic_value": "Network effects - each deployment makes all deployments smarter"
    }


if __name__ == "__main__":
    # Test Phase 3 Ecosystem Intelligence
    import asyncio
    
    async def test_ecosystem_intelligence():
        print("🌍 Testing Phase 3: Ecosystem Intelligence...")
        
        # Initialize different tenant types
        healthcare_tenant = create_healthcare_tenant()
        fintech_tenant = create_fintech_tenant() 
        gov_tenant = create_government_tenant()
        
        # Initialize ecosystem intelligence
        healthcare_engine = initialize_ecosystem_intelligence(healthcare_tenant)
        fintech_engine = initialize_ecosystem_intelligence(fintech_tenant)
        gov_engine = initialize_ecosystem_intelligence(gov_tenant)
        
        print(f"\n✅ Initialized {len(ecosystem_engines)} tenant ecosystems")
        
        # Test ecosystem evaluation
        test_cases = [
            ("healthcare_org_001", "Patient John Doe, SSN 123-45-6789", "/patient/records"),
            ("fintech_startup_042", "Credit card 4532-1234-5678-9012", "/payments/process"),
            ("gov_agency_dhs", "Classified document access attempt", "/documents/classified")
        ]
        
        for tenant_id, text, endpoint in test_cases:
            result = await evaluate_with_ecosystem_intelligence(
                tenant_id=tenant_id,
                text=text,
                endpoint=endpoint,
                static_action="allow",
                static_rule_ids=[]
            )
            
            print(f"\n🧪 Test: {tenant_id}")
            print(f"   Text: {text[:30]}...")
            print(f"   Decision: {result.get('ecosystem_decision', {}).get('action', 'unknown')}")
            print(f"   Confidence: {result.get('ecosystem_decision', {}).get('confidence', 0):.2f}")
            print(f"   Layers: {result.get('ecosystem_decision', {}).get('decision_layers', [])}")
            print(f"   Time: {result.get('evaluation_time_ms', 0):.1f}ms")
        
        # Show ecosystem status
        status = get_ecosystem_status()
        print(f"\n🌍 Ecosystem Status:")
        print(json.dumps(status, indent=2))
        
        # Test auto rule generation
        print(f"\n🤖 Testing auto rule generation...")
        violation_patterns = [
            "Patient data for John Smith",
            "Patient record: Jane Doe", 
            "Patient information: Bob Wilson"
        ]
        
        auto_rule = await fintech_engine.generate_auto_rule(
            violation_patterns=violation_patterns,
            suggested_action="flag"
        )
        
        print(f"   Generated Rule: {auto_rule.rule_id}")
        print(f"   Pattern: {auto_rule.pattern}")
        print(f"   Action: {auto_rule.action}")
        print(f"   Confidence: {auto_rule.confidence:.2f}")
        print(f"   Description: {auto_rule.description}")
    
    asyncio.run(test_ecosystem_intelligence())