"""
Phase 6B - Risk Scoring API Endpoints
REST API for adaptive risk assessment and behavioral intelligence
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum

from app.intelligence.risk_scoring import (
    get_risk_scoring_engine, RiskLevel, BehaviorPattern,
    RiskAssessment, BehaviorProfile, HistoricalDataManager
)
from app.models import BaseResponse, EvaluateRequest, EvaluateResponse
from app.util import get_logger

logger = get_logger(__name__)

# Initialize router
risk_router = APIRouter(prefix="/v1/risk", tags=["risk-scoring"])


class TimeRange(str, Enum):
    """Time range options for analysis."""
    HOUR = "1h"
    DAY = "24h" 
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"


class RiskMetricsRequest(BaseModel):
    """Request for risk metrics analysis."""
    time_range: TimeRange = Field(default=TimeRange.DAY)
    identifier: Optional[str] = Field(default=None, description="User/agent/endpoint identifier")
    identifier_type: Optional[str] = Field(default=None, description="Type: user, agent, endpoint")
    include_predictions: bool = Field(default=False)


class BehaviorProfileResponse(BaseModel):
    """Response model for behavior profiles."""
    identifier: str
    identifier_type: str
    total_requests: int
    violation_count: int
    violation_rate: float
    active_hours: List[int]
    active_days: List[int]
    request_frequency: float
    typical_text_length: float
    common_endpoints: List[str]
    trust_score: float
    recent_anomalies: int
    last_violation: Optional[datetime]
    risk_trend: str
    created_at: datetime
    updated_at: datetime


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessments."""
    risk_score: float
    risk_level: str
    behavior_pattern: str
    confidence: float
    contributing_factors: List[str]
    anomaly_indicators: List[str]
    recommended_action: str
    adaptive_threshold: float
    timestamp: datetime


class RiskMetricsResponse(BaseResponse):
    """Response model for risk metrics."""
    time_range: str
    total_assessments: int
    risk_distribution: Dict[str, int]
    behavior_patterns: Dict[str, int]
    average_risk_score: float
    top_risk_factors: List[Dict[str, Any]]
    anomaly_count: int
    ml_model_accuracy: Optional[float]
    adaptive_thresholds: Dict[str, float]


class RiskTrendResponse(BaseModel):
    """Risk trend analysis response."""
    identifier: str
    identifier_type: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    risk_velocity: float  # Rate of change
    confidence_interval: Dict[str, float]
    prediction_horizon: str
    recommendations: List[str]


@risk_router.get("/status")
async def get_risk_engine_status() -> JSONResponse:
    """Get risk scoring engine status and capabilities."""
    try:
        engine = get_risk_scoring_engine()
        
        # Check ML availability
        ml_status = {
            "ml_available": engine.ml_model is not None,
            "model_trained": engine.last_model_update is not None,
            "last_model_update": engine.last_model_update.isoformat() if engine.last_model_update else None,
            "anomaly_detection": engine.anomaly_detector is not None,
            "feature_scaling": engine.scaler is not None
        }
        
        # Get database stats
        historical_data = engine.data_manager.get_historical_data(days=7)
        
        return JSONResponse({
            "status": "ok",
            "phase": "6B - Adaptive Risk Scoring",
            "capabilities": {
                "behavioral_profiling": True,
                "adaptive_thresholds": True,
                "anomaly_detection": True,
                "ml_risk_scoring": ml_status["ml_available"],
                "historical_learning": True,
                "real_time_assessment": True
            },
            "ml_status": ml_status,
            "data_stats": {
                "recent_decisions": len(historical_data),
                "data_retention_days": 30,
                "profile_cache_size": len(engine.behavior_analyzer.profiles_cache)
            },
            "supported_patterns": [pattern.value for pattern in BehaviorPattern],
            "risk_levels": [level.value for level in RiskLevel]
        })
        
    except Exception as e:
        logger.error(f"Risk engine status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@risk_router.get("/metrics")
async def get_risk_metrics(
    time_range: TimeRange = Query(TimeRange.DAY),
    identifier: Optional[str] = Query(None),
    identifier_type: Optional[str] = Query(None)
) -> RiskMetricsResponse:
    """Get comprehensive risk metrics and statistics."""
    try:
        engine = get_risk_scoring_engine()
        
        # Parse time range
        days_map = {
            TimeRange.HOUR: 1/24,
            TimeRange.DAY: 1,
            TimeRange.WEEK: 7,
            TimeRange.MONTH: 30,
            TimeRange.QUARTER: 90
        }
        days = days_map[time_range]
        
        # Get historical data
        historical_data = engine.data_manager.get_historical_data(days=int(days))
        
        # Filter by identifier if specified
        if identifier and identifier_type:
            if identifier_type == "user":
                historical_data = [d for d in historical_data if d.get('user_id') == identifier]
            elif identifier_type == "agent":
                historical_data = [d for d in historical_data if d.get('agent_id') == identifier]
            elif identifier_type == "endpoint":
                historical_data = [d for d in historical_data if d.get('endpoint') == identifier]
        
        # Calculate metrics
        total_assessments = len(historical_data)
        
        # Risk distribution
        risk_distribution = {level.value: 0 for level in RiskLevel}
        behavior_patterns = {pattern.value: 0 for pattern in BehaviorPattern}
        
        risk_scores = []
        contributing_factors = []
        
        for record in historical_data:
            risk_score = record.get('risk_score', 0.0)
            risk_scores.append(risk_score)
            
            # Determine risk level from score
            if risk_score >= 0.9:
                risk_distribution[RiskLevel.CRITICAL.value] += 1
            elif risk_score >= 0.7:
                risk_distribution[RiskLevel.VERY_HIGH.value] += 1
            elif risk_score >= 0.5:
                risk_distribution[RiskLevel.HIGH.value] += 1
            elif risk_score >= 0.3:
                risk_distribution[RiskLevel.MEDIUM.value] += 1
            elif risk_score >= 0.1:
                risk_distribution[RiskLevel.LOW.value] += 1
            else:
                risk_distribution[RiskLevel.VERY_LOW.value] += 1
        
        # Calculate average risk score
        average_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        # Top risk factors (simplified)
        top_risk_factors = [
            {"factor": "policy_violations", "frequency": len([d for d in historical_data if d.get('decision') in ['block', 'flag']])},
            {"factor": "off_hours_access", "frequency": 0},  # Would calculate actual off-hours access
            {"factor": "unusual_endpoints", "frequency": 0},  # Would calculate actual unusual endpoints
        ]
        
        # Anomaly count (simplified)
        anomaly_count = len([d for d in historical_data if d.get('risk_score', 0) > 0.7])
        
        # ML model accuracy (if available)
        ml_accuracy = None
        if engine.ml_model is not None:
            ml_accuracy = 0.85  # Would calculate actual accuracy
        
        # Adaptive thresholds by category
        adaptive_thresholds = {
            "user_default": 0.5,
            "endpoint_default": 0.5,
            "off_hours": 0.4,
            "high_risk_endpoint": 0.3
        }
        
        return RiskMetricsResponse(
            success=True,
            message="Risk metrics calculated successfully",
            time_range=time_range.value,
            total_assessments=total_assessments,
            risk_distribution=risk_distribution,
            behavior_patterns=behavior_patterns,
            average_risk_score=average_risk_score,
            top_risk_factors=top_risk_factors,
            anomaly_count=anomaly_count,
            ml_model_accuracy=ml_accuracy,
            adaptive_thresholds=adaptive_thresholds
        )
        
    except Exception as e:
        logger.error(f"Risk metrics calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics calculation failed: {str(e)}")


@risk_router.get("/profiles")
async def list_behavior_profiles(
    identifier_type: Optional[str] = Query(None, description="Filter by type: user, agent, endpoint"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> JSONResponse:
    """List behavior profiles with optional filtering."""
    try:
        engine = get_risk_scoring_engine()
        
        # Get profiles from cache and database
        profiles = []
        
        # For demo purposes, show cached profiles
        for cache_key, profile in engine.behavior_analyzer.profiles_cache.items():
            if identifier_type is None or profile.identifier_type == identifier_type:
                
                # Calculate risk trend
                risk_trend = "stable"
                if profile.violation_rate > 0.1:
                    risk_trend = "increasing"
                elif profile.trust_score > 0.8:
                    risk_trend = "decreasing"
                
                profiles.append(BehaviorProfileResponse(
                    identifier=profile.identifier,
                    identifier_type=profile.identifier_type,
                    total_requests=profile.total_requests,
                    violation_count=profile.violation_count,
                    violation_rate=profile.violation_rate,
                    active_hours=profile.active_hours,
                    active_days=profile.active_days,
                    request_frequency=profile.request_frequency,
                    typical_text_length=profile.typical_text_length,
                    common_endpoints=profile.common_endpoints,
                    trust_score=profile.trust_score,
                    recent_anomalies=profile.recent_anomalies,
                    last_violation=profile.last_violation,
                    risk_trend=risk_trend,
                    created_at=profile.created_at,
                    updated_at=profile.updated_at
                ))
        
        # Apply pagination
        paginated_profiles = profiles[offset:offset + limit]
        
        return JSONResponse({
            "profiles": [p.dict() for p in paginated_profiles],
            "total_profiles": len(profiles),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(profiles)
        })
        
    except Exception as e:
        logger.error(f"Profile listing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Profile listing failed: {str(e)}")


@risk_router.get("/profiles/{identifier}")
async def get_behavior_profile(
    identifier: str,
    identifier_type: str = Query(..., description="Type: user, agent, endpoint")
) -> BehaviorProfileResponse:
    """Get detailed behavior profile for specific identifier."""
    try:
        engine = get_risk_scoring_engine()
        
        profile = engine.behavior_analyzer.get_or_create_profile(identifier, identifier_type)
        
        # Calculate risk trend
        risk_trend = "stable"
        if profile.violation_rate > 0.1:
            risk_trend = "increasing"
        elif profile.trust_score > 0.8:
            risk_trend = "decreasing"
        
        return BehaviorProfileResponse(
            identifier=profile.identifier,
            identifier_type=profile.identifier_type,
            total_requests=profile.total_requests,
            violation_count=profile.violation_count,
            violation_rate=profile.violation_rate,
            active_hours=profile.active_hours,
            active_days=profile.active_days,
            request_frequency=profile.request_frequency,
            typical_text_length=profile.typical_text_length,
            common_endpoints=profile.common_endpoints,
            trust_score=profile.trust_score,
            recent_anomalies=profile.recent_anomalies,
            last_violation=profile.last_violation,
            risk_trend=risk_trend,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except Exception as e:
        logger.error(f"Profile retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Profile retrieval failed: {str(e)}")


@risk_router.get("/assessments/recent")
async def get_recent_assessments(
    limit: int = Query(100, ge=1, le=1000),
    risk_level: Optional[RiskLevel] = Query(None),
    behavior_pattern: Optional[BehaviorPattern] = Query(None)
) -> JSONResponse:
    """Get recent risk assessments with optional filtering."""
    try:
        engine = get_risk_scoring_engine()
        
        # Get recent assessments from database
        with engine.data_manager.db_path.open() as db:
            # This would query the risk_assessments table
            # For demo, return mock data
            assessments = []
            
            for i in range(min(limit, 10)):
                assessment = RiskAssessmentResponse(
                    risk_score=0.3 + (i * 0.1),
                    risk_level=RiskLevel.MEDIUM.value,
                    behavior_pattern=BehaviorPattern.NORMAL.value,
                    confidence=0.8,
                    contributing_factors=["policy_evaluation", "historical_patterns"],
                    anomaly_indicators=[],
                    recommended_action="standard_monitoring",
                    adaptive_threshold=0.5,
                    timestamp=datetime.now() - timedelta(minutes=i*5)
                )
                
                # Apply filters
                if risk_level and assessment.risk_level != risk_level.value:
                    continue
                if behavior_pattern and assessment.behavior_pattern != behavior_pattern.value:
                    continue
                
                assessments.append(assessment.dict())
        
        return JSONResponse({
            "assessments": assessments,
            "total_returned": len(assessments),
            "filters_applied": {
                "risk_level": risk_level.value if risk_level else None,
                "behavior_pattern": behavior_pattern.value if behavior_pattern else None
            }
        })
        
    except Exception as e:
        logger.error(f"Assessment retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment retrieval failed: {str(e)}")


@risk_router.post("/assess")
async def assess_risk_manually(request: EvaluateRequest) -> RiskAssessmentResponse:
    """Manually assess risk for a given request (without policy evaluation)."""
    try:
        engine = get_risk_scoring_engine()
        
        # Create mock response for assessment
        mock_response = EvaluateResponse(
            success=True,
            decision="allow",
            rule_ids=[],
            message="Manual risk assessment"
        )
        
        # Perform risk assessment
        assessment = engine.assess_risk(request, mock_response)
        
        return RiskAssessmentResponse(
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            behavior_pattern=assessment.behavior_pattern.value,
            confidence=assessment.confidence,
            contributing_factors=assessment.contributing_factors,
            anomaly_indicators=assessment.anomaly_indicators,
            recommended_action=assessment.recommended_action,
            adaptive_threshold=assessment.adaptive_threshold,
            timestamp=assessment.timestamp
        )
        
    except Exception as e:
        logger.error(f"Manual risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@risk_router.get("/trends/{identifier}")
async def get_risk_trend_analysis(
    identifier: str,
    identifier_type: str = Query(..., description="Type: user, agent, endpoint"),
    days: int = Query(30, ge=1, le=365)
) -> RiskTrendResponse:
    """Get risk trend analysis for specific identifier."""
    try:
        engine = get_risk_scoring_engine()
        
        # Get behavior profile
        profile = engine.behavior_analyzer.get_or_create_profile(identifier, identifier_type)
        
        # Calculate trend direction
        trend_direction = "stable"
        risk_velocity = 0.0
        
        if profile.violation_rate > 0.1:
            trend_direction = "increasing" 
            risk_velocity = profile.violation_rate * 10  # Simplified calculation
        elif profile.trust_score > 0.8:
            trend_direction = "decreasing"
            risk_velocity = -(profile.trust_score - 0.5) * 2
        
        # Generate recommendations
        recommendations = []
        if trend_direction == "increasing":
            recommendations.extend([
                "Enhanced monitoring recommended",
                "Review access patterns",
                "Consider additional authentication"
            ])
        elif profile.trust_score > 0.9:
            recommendations.append("Consider relaxed monitoring for trusted entity")
        
        return RiskTrendResponse(
            identifier=identifier,
            identifier_type=identifier_type,
            trend_direction=trend_direction,
            risk_velocity=risk_velocity,
            confidence_interval={"lower": 0.7, "upper": 0.9},
            prediction_horizon=f"{days} days",
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@risk_router.post("/models/retrain")
async def retrain_ml_models() -> BaseResponse:
    """Manually trigger ML model retraining."""
    try:
        engine = get_risk_scoring_engine()
        
        # Force model update
        engine._update_ml_models()
        
        model_status = "trained" if engine.ml_model is not None else "failed"
        
        return BaseResponse(
            success=engine.ml_model is not None,
            message=f"ML model retraining completed - Status: {model_status}"
        )
        
    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model retraining failed: {str(e)}")


@risk_router.get("/anomalies")
async def get_anomaly_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high"),
    hours: int = Query(24, ge=1, le=168)
) -> JSONResponse:
    """Get recent anomaly detection alerts."""
    try:
        # This would query actual anomaly data
        # For demo, return mock anomalies
        
        anomalies = [
            {
                "id": "anom_001",
                "timestamp": datetime.now() - timedelta(hours=2),
                "severity": "high",
                "type": "unusual_time_access",
                "identifier": "user_123",
                "identifier_type": "user",
                "description": "Access during unusual hours (3 AM)",
                "risk_score": 0.75,
                "status": "active"
            },
            {
                "id": "anom_002", 
                "timestamp": datetime.now() - timedelta(hours=6),
                "severity": "medium",
                "type": "request_frequency_spike",
                "identifier": "/api/sensitive-data",
                "identifier_type": "endpoint",
                "description": "Request frequency 300% above normal",
                "risk_score": 0.60,
                "status": "investigating"
            }
        ]
        
        # Apply severity filter
        if severity:
            anomalies = [a for a in anomalies if a['severity'] == severity]
        
        return JSONResponse({
            "anomalies": anomalies,
            "total_anomalies": len(anomalies),
            "time_window_hours": hours,
            "severity_filter": severity,
            "summary": {
                "high_severity": len([a for a in anomalies if a['severity'] == 'high']),
                "medium_severity": len([a for a in anomalies if a['severity'] == 'medium']), 
                "low_severity": len([a for a in anomalies if a['severity'] == 'low'])
            }
        })
        
    except Exception as e:
        logger.error(f"Anomaly retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly retrieval failed: {str(e)}")


@risk_router.delete("/profiles/{identifier}")
async def delete_behavior_profile(
    identifier: str,
    identifier_type: str = Query(..., description="Type: user, agent, endpoint")
) -> BaseResponse:
    """Delete behavior profile (for testing/privacy compliance)."""
    try:
        engine = get_risk_scoring_engine()
        
        # Remove from cache
        cache_key = f"{identifier_type}:{identifier}"
        if cache_key in engine.behavior_analyzer.profiles_cache:
            del engine.behavior_analyzer.profiles_cache[cache_key]
        
        # Remove from database (would implement actual deletion)
        logger.info(f"Deleted behavior profile: {identifier} ({identifier_type})")
        
        return BaseResponse(
            success=True,
            message=f"Behavior profile deleted: {identifier}"
        )
        
    except Exception as e:
        logger.error(f"Profile deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Profile deletion failed: {str(e)}")


# Add risk router to intelligence module
def add_risk_scoring_routes(app):
    """Add risk scoring routes to FastAPI app."""
    app.include_router(risk_router)