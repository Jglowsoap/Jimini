"""
Phase 6C - Policy Recommendations API
REST endpoints for intelligent policy optimization and conflict detection
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from app.models import Rule
from app.intelligence.policy_recommendations import (
    PolicyRecommendationEngine, 
    get_policy_recommendation_engine,
    PolicyConflict,
    PolicyRecommendation, 
    CoverageGap,
    RecommendationType,
    RecommendationPriority,
    ConflictType
)
from app.util import get_logger

logger = get_logger(__name__)

# Request/Response models for API
class ConflictAnalysisRequest(BaseModel):
    """Request model for policy conflict analysis."""
    rules: Dict[str, Dict[str, Any]]  # Rules in dict format
    include_ml_analysis: bool = True
    confidence_threshold: float = 0.5


class RecommendationGenerationRequest(BaseModel):
    """Request model for policy recommendations."""
    rules: Dict[str, Dict[str, Any]]
    performance_data: Optional[Dict[str, Any]] = None
    compliance_requirements: Optional[List[str]] = None
    focus_areas: Optional[List[RecommendationType]] = None


class CoverageAnalysisRequest(BaseModel):
    """Request model for coverage gap analysis."""
    rules: Dict[str, Dict[str, Any]]
    evaluation_history: Optional[List[Dict[str, Any]]] = None
    compliance_frameworks: Optional[List[str]] = None
    time_range_days: Optional[int] = 30


class PolicyOptimizationResponse(BaseModel):
    """Response model for policy optimization analysis."""
    analysis_id: str
    timestamp: str
    summary: Dict[str, Any]
    conflicts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    coverage_gaps: List[Dict[str, Any]]
    next_actions: List[str]
    ml_analysis_enabled: bool


def create_policy_recommendations_router() -> APIRouter:
    """Create and configure the policy recommendations API router."""
    router = APIRouter(prefix="/v1/policy", tags=["Policy Intelligence"])
    
    @router.get("/recommendations/status")
    async def get_recommendations_status():
        """Get policy recommendation engine status and capabilities."""
        try:
            engine = get_policy_recommendation_engine()
            
            # Check ML availability
            try:
                import sklearn
                ml_available = True
                ml_version = sklearn.__version__
            except ImportError:
                ml_available = False
                ml_version = None
            
            return {
                "status": "active",
                "timestamp": "2025-10-01T22:20:00Z",
                "capabilities": {
                    "conflict_detection": True,
                    "ml_analysis": ml_available,
                    "recommendation_generation": True,
                    "coverage_analysis": True,
                    "performance_optimization": True
                },
                "ml_info": {
                    "available": ml_available,
                    "version": ml_version,
                    "models": ["TfidfVectorizer", "KMeans", "CosineSimilarity"] if ml_available else []
                },
                "statistics": {
                    "rules_cached": len(engine.rules_cache),
                    "conflicts_detected": len(engine.conflicts_detected),
                    "recommendations_generated": len(engine.recommendations_generated),
                    "coverage_gaps_identified": len(engine.coverage_gaps_identified)
                },
                "supported_analyses": [
                    "pattern_overlap_detection",
                    "action_contradiction_detection", 
                    "scope_conflict_detection",
                    "redundancy_detection",
                    "precedence_analysis",
                    "performance_optimization",
                    "security_enhancement",
                    "compliance_alignment"
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get recommendation engine status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get engine status")
    
    @router.post("/conflicts/analyze")
    async def analyze_policy_conflicts(request: ConflictAnalysisRequest):
        """Analyze policies for conflicts and inconsistencies."""
        try:
            engine = get_policy_recommendation_engine()
            
            # Convert dict rules to Rule objects
            rules = {}
            for rule_id, rule_data in request.rules.items():
                try:
                    rules[rule_id] = Rule(**rule_data)
                except Exception as e:
                    logger.warning(f"Failed to parse rule {rule_id}: {e}")
                    continue
            
            # Perform conflict analysis
            conflicts = engine.analyze_policy_conflicts(rules)
            
            # Filter by confidence threshold
            filtered_conflicts = [
                conflict for conflict in conflicts 
                if conflict.confidence_score >= request.confidence_threshold
            ]
            
            # Group conflicts by type
            conflicts_by_type = {}
            for conflict in filtered_conflicts:
                conflict_type = conflict.conflict_type.value
                if conflict_type not in conflicts_by_type:
                    conflicts_by_type[conflict_type] = []
                conflicts_by_type[conflict_type].append(conflict)
            
            return {
                "analysis_id": f"conflict_analysis_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "total_rules_analyzed": len(rules),
                "conflicts_detected": len(filtered_conflicts),
                "conflicts_by_type": {
                    conflict_type: len(conflicts) 
                    for conflict_type, conflicts in conflicts_by_type.items()
                },
                "confidence_threshold": request.confidence_threshold,
                "ml_analysis_used": request.include_ml_analysis,
                "conflicts": [
                    {
                        "conflict_id": conflict.conflict_id,
                        "type": conflict.conflict_type.value,
                        "rule_ids": conflict.rule_ids,
                        "description": conflict.description,
                        "impact": conflict.impact_assessment,
                        "confidence": conflict.confidence_score,
                        "resolutions": conflict.resolution_suggestions,
                        "detected_at": conflict.detected_at
                    }
                    for conflict in filtered_conflicts
                ],
                "summary": {
                    "critical_conflicts": len([c for c in filtered_conflicts if c.confidence_score > 0.8]),
                    "high_confidence_conflicts": len([c for c in filtered_conflicts if c.confidence_score > 0.7]),
                    "most_common_type": max(conflicts_by_type.keys(), key=lambda k: len(conflicts_by_type[k])) if conflicts_by_type else None,
                    "rules_with_conflicts": len(set(rule_id for conflict in filtered_conflicts for rule_id in conflict.rule_ids))
                }
            }
            
        except Exception as e:
            logger.error(f"Policy conflict analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    @router.post("/recommendations/generate")
    async def generate_policy_recommendations(request: RecommendationGenerationRequest):
        """Generate intelligent policy optimization recommendations."""
        try:
            engine = get_policy_recommendation_engine()
            
            # Convert dict rules to Rule objects
            rules = {}
            for rule_id, rule_data in request.rules.items():
                try:
                    rules[rule_id] = Rule(**rule_data)
                except Exception as e:
                    logger.warning(f"Failed to parse rule {rule_id}: {e}")
                    continue
            
            # Generate recommendations
            recommendations = engine.generate_policy_recommendations(
                rules=rules,
                performance_data=request.performance_data,
                compliance_requirements=request.compliance_requirements
            )
            
            # Filter by focus areas if specified
            if request.focus_areas:
                recommendations = [
                    rec for rec in recommendations 
                    if rec.recommendation_type in request.focus_areas
                ]
            
            # Group recommendations by priority and type
            recommendations_by_priority = {}
            recommendations_by_type = {}
            
            for rec in recommendations:
                # By priority
                priority = rec.priority.value
                if priority not in recommendations_by_priority:
                    recommendations_by_priority[priority] = []
                recommendations_by_priority[priority].append(rec)
                
                # By type
                rec_type = rec.recommendation_type.value
                if rec_type not in recommendations_by_type:
                    recommendations_by_type[rec_type] = []
                recommendations_by_type[rec_type].append(rec)
            
            return {
                "analysis_id": f"recommendations_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "total_rules_analyzed": len(rules),
                "recommendations_generated": len(recommendations),
                "recommendations_by_priority": {
                    priority: len(recs) 
                    for priority, recs in recommendations_by_priority.items()
                },
                "recommendations_by_type": {
                    rec_type: len(recs) 
                    for rec_type, recs in recommendations_by_type.items()
                },
                "focus_areas": request.focus_areas,
                "recommendations": [
                    {
                        "recommendation_id": rec.recommendation_id,
                        "type": rec.recommendation_type.value,
                        "priority": rec.priority.value,
                        "title": rec.title,
                        "description": rec.description,
                        "affected_rules": rec.affected_rules,
                        "suggested_changes": rec.suggested_changes,
                        "rationale": rec.rationale,
                        "expected_impact": rec.expected_impact,
                        "confidence": rec.confidence_score,
                        "implementation_steps": rec.implementation_steps,
                        "created_at": rec.created_at
                    }
                    for rec in recommendations
                ],
                "summary": {
                    "critical_recommendations": len([r for r in recommendations if r.priority == RecommendationPriority.CRITICAL]),
                    "high_priority_recommendations": len([r for r in recommendations if r.priority == RecommendationPriority.HIGH]),
                    "security_recommendations": len([r for r in recommendations if r.recommendation_type == RecommendationType.SECURITY_ENHANCEMENT]),
                    "performance_recommendations": len([r for r in recommendations if r.recommendation_type == RecommendationType.PERFORMANCE_TUNING]),
                    "total_affected_rules": len(set(rule_id for rec in recommendations for rule_id in rec.affected_rules))
                }
            }
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    @router.post("/coverage/analyze") 
    async def analyze_coverage_gaps(request: CoverageAnalysisRequest):
        """Analyze policy coverage gaps and missing protection areas."""
        try:
            engine = get_policy_recommendation_engine()
            
            # Convert dict rules to Rule objects
            rules = {}
            for rule_id, rule_data in request.rules.items():
                try:
                    rules[rule_id] = Rule(**rule_data)
                except Exception as e:
                    logger.warning(f"Failed to parse rule {rule_id}: {e}")
                    continue
            
            # Perform coverage analysis
            coverage_gaps = engine.identify_coverage_gaps(
                rules=rules,
                evaluation_history=request.evaluation_history,
                compliance_frameworks=request.compliance_frameworks
            )
            
            # Group gaps by type and risk level
            gaps_by_type = {}
            gaps_by_risk = {}
            
            for gap in coverage_gaps:
                # By type
                gap_type = gap.gap_type
                if gap_type not in gaps_by_type:
                    gaps_by_type[gap_type] = []
                gaps_by_type[gap_type].append(gap)
                
                # By risk level
                risk_level = gap.risk_level
                if risk_level not in gaps_by_risk:
                    gaps_by_risk[risk_level] = []
                gaps_by_risk[risk_level].append(gap)
            
            return {
                "analysis_id": f"coverage_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "total_rules_analyzed": len(rules),
                "coverage_gaps_identified": len(coverage_gaps),
                "gaps_by_type": {
                    gap_type: len(gaps) 
                    for gap_type, gaps in gaps_by_type.items()
                },
                "gaps_by_risk_level": {
                    risk_level: len(gaps) 
                    for risk_level, gaps in gaps_by_risk.items()
                },
                "analysis_parameters": {
                    "time_range_days": request.time_range_days,
                    "compliance_frameworks": request.compliance_frameworks,
                    "evaluation_history_entries": len(request.evaluation_history or [])
                },
                "coverage_gaps": [
                    {
                        "gap_id": gap.gap_id,
                        "type": gap.gap_type,
                        "description": gap.description,
                        "uncovered_scenarios": gap.uncovered_scenarios,
                        "suggested_rules": gap.suggested_rules,
                        "risk_level": gap.risk_level,
                        "compliance_implications": gap.compliance_implications,
                        "identified_at": gap.identified_at
                    }
                    for gap in coverage_gaps
                ],
                "summary": {
                    "high_risk_gaps": len([g for g in coverage_gaps if g.risk_level == "high"]),
                    "compliance_gaps": len([g for g in coverage_gaps if g.compliance_implications]),
                    "endpoint_gaps": len([g for g in coverage_gaps if g.gap_type == "endpoint"]),
                    "content_pattern_gaps": len([g for g in coverage_gaps if g.gap_type == "content_pattern"])
                }
            }
            
        except Exception as e:
            logger.error(f"Coverage analysis failed: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    @router.post("/optimize/complete")
    async def complete_policy_optimization(
        rules: Dict[str, Dict[str, Any]] = Body(...),
        performance_data: Optional[Dict[str, Any]] = Body(None),
        compliance_requirements: Optional[List[str]] = Body(None),
        evaluation_history: Optional[List[Dict[str, Any]]] = Body(None),
        include_ml_analysis: bool = Body(True)
    ):
        """Perform complete policy optimization analysis."""
        try:
            engine = get_policy_recommendation_engine()
            
            # Convert dict rules to Rule objects
            parsed_rules = {}
            for rule_id, rule_data in rules.items():
                try:
                    parsed_rules[rule_id] = Rule(**rule_data)
                except Exception as e:
                    logger.warning(f"Failed to parse rule {rule_id}: {e}")
                    continue
            
            # Perform all analyses
            conflicts = engine.analyze_policy_conflicts(parsed_rules)
            recommendations = engine.generate_policy_recommendations(
                parsed_rules, performance_data, compliance_requirements
            )
            coverage_gaps = engine.identify_coverage_gaps(
                parsed_rules, evaluation_history, compliance_requirements
            )
            
            # Generate comprehensive report
            report = engine.get_policy_optimization_report()
            
            return PolicyOptimizationResponse(
                analysis_id=f"complete_optimization_{int(time.time())}",
                timestamp=report["report_generated_at"],
                summary=report["summary"],
                conflicts=report["conflicts"],
                recommendations=report["recommendations"], 
                coverage_gaps=report["coverage_gaps"],
                next_actions=report["next_actions"],
                ml_analysis_enabled=include_ml_analysis
            )
            
        except Exception as e:
            logger.error(f"Complete optimization failed: {e}")
            raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
    
    @router.get("/recommendations/types")
    async def get_recommendation_types():
        """Get available recommendation types and priorities."""
        return {
            "recommendation_types": [
                {
                    "type": rec_type.value,
                    "description": {
                        "conflict_resolution": "Resolve policy conflicts and inconsistencies",
                        "optimization": "Optimize policy performance and effectiveness",
                        "coverage_gap": "Fill policy coverage gaps",
                        "performance_tuning": "Improve policy performance metrics",
                        "security_enhancement": "Enhance security posture",
                        "compliance_alignment": "Align with compliance requirements"
                    }.get(rec_type.value, "Policy improvement recommendation")
                }
                for rec_type in RecommendationType
            ],
            "priority_levels": [
                {
                    "priority": priority.value,
                    "description": {
                        "critical": "Immediate attention required - security/compliance risk",
                        "high": "Important optimization opportunity",
                        "medium": "Beneficial improvement", 
                        "low": "Minor enhancement",
                        "informational": "Awareness and monitoring"
                    }.get(priority.value, "Standard priority level")
                }
                for priority in RecommendationPriority
            ],
            "conflict_types": [
                {
                    "type": conflict_type.value,
                    "description": {
                        "overlapping_patterns": "Rules with overlapping detection patterns",
                        "contradictory_actions": "Rules with conflicting actions for similar content",
                        "scope_conflicts": "Rules with overlapping but conflicting scopes",
                        "redundant_rules": "Duplicate or unnecessary rules",
                        "precedence_issues": "Rule ordering and precedence problems"
                    }.get(conflict_type.value, "Policy conflict type")
                }
                for conflict_type in ConflictType
            ]
        }
    
    return router


# Add missing imports
import time
from datetime import datetime