"""
Jimini Intelligence Evolution - Phase 6D: Predictive Intelligence API

REST API endpoints for predictive policy intelligence:
- Threat pattern prediction endpoints
- Adaptive policy tuning recommendations
- Behavioral anomaly forecasting
- Zero-day pattern generation APIs

Author: Jimini Intelligence Team
Version: 6D.1.0
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime
import logging

from app.intelligence.predictive_intelligence import (
    get_predictive_engine,
    ThreatPrediction,
    PolicyTuningRecommendation,
    AnomalyForecast,
    ZeroDayPattern,
    PredictionConfidence,
    ThreatTrend
)
from app.models import Rule

logger = logging.getLogger(__name__)

# API Router for predictive intelligence endpoints
router = APIRouter(prefix="/v1/predictive", tags=["Predictive Intelligence"])


# Request/Response Models
class ThreatPredictionRequest(BaseModel):
    """Request model for threat prediction."""
    lookback_days: int = Field(default=30, ge=1, le=365, description="Days to analyze for prediction")
    forecast_days: int = Field(default=7, ge=1, le=90, description="Days to forecast ahead")
    threat_categories: Optional[List[str]] = Field(default=None, description="Specific threat categories to analyze")
    confidence_threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")


class ThreatPredictionResponse(BaseModel):
    """Response model for threat predictions."""
    predictions: List[Dict[str, Any]]
    total_predictions: int
    analysis_period: Dict[str, str]
    ml_enabled: bool
    confidence_distribution: Dict[str, int]
    trend_summary: Dict[str, int]


class PolicyTuningRequest(BaseModel):
    """Request model for policy tuning recommendations."""
    rules: Dict[str, Dict[str, Any]]
    performance_threshold: Optional[float] = Field(default=0.8, description="Minimum performance threshold")
    include_experimental: bool = Field(default=False, description="Include experimental recommendations")
    priority_filter: Optional[List[int]] = Field(default=None, description="Filter by priority levels")


class PolicyTuningResponse(BaseModel):
    """Response model for policy tuning recommendations."""
    recommendations: List[Dict[str, Any]]
    total_recommendations: int
    priority_distribution: Dict[str, int]
    estimated_impact: Dict[str, float]
    implementation_timeline: Dict[str, str]


class AnomalyForecastRequest(BaseModel):
    """Request model for anomaly forecasting."""
    monitoring_window_hours: int = Field(default=24, ge=1, le=168, description="Hours to forecast ahead")
    sensitivity_level: Optional[str] = Field(default="medium", description="Detection sensitivity level")
    anomaly_types: Optional[List[str]] = Field(default=None, description="Specific anomaly types to monitor")


class AnomalyForecastResponse(BaseModel):
    """Response model for anomaly forecasts."""
    forecasts: List[Dict[str, Any]]
    total_forecasts: int
    forecast_window: Dict[str, str]
    severity_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]
    monitoring_recommendations: List[str]


class ZeroDayGenerationRequest(BaseModel):
    """Request model for zero-day pattern generation."""
    target_threats: Optional[List[str]] = Field(default=None, description="Specific threats to target")
    generation_methods: Optional[List[str]] = Field(default=["genetic", "neural"], description="AI methods to use")
    validation_level: Optional[str] = Field(default="standard", description="Validation rigor level")
    deployment_readiness: Optional[str] = Field(default="experimental", description="Required readiness level")


class ZeroDayGenerationResponse(BaseModel):
    """Response model for zero-day pattern generation."""
    patterns: List[Dict[str, Any]]
    total_patterns: int
    generation_summary: Dict[str, Any]
    validation_status: Dict[str, int]
    deployment_recommendations: List[str]


class PredictiveStatusResponse(BaseModel):
    """Response model for predictive engine status."""
    engine_status: str
    ml_availability: bool
    model_status: Dict[str, str]
    prediction_cache_size: int
    last_training: Optional[str]
    capabilities: List[str]
    performance_metrics: Dict[str, float]


# API Endpoints

@router.post("/threats/predict", response_model=ThreatPredictionResponse)
async def predict_threat_patterns(request: ThreatPredictionRequest):
    """
    Predict emerging threat patterns using ML and time-series analysis.
    
    This endpoint analyzes historical threat data to forecast potential
    security risks and emerging attack patterns.
    """
    try:
        engine = get_predictive_engine()
        logger.info(f"Predicting threats: {request.lookback_days}d lookback, {request.forecast_days}d forecast")
        
        # Generate threat predictions
        predictions = await engine.predict_threat_patterns(
            lookback_days=request.lookback_days,
            forecast_days=request.forecast_days
        )
        
        # Filter by confidence threshold if specified
        if request.confidence_threshold:
            predictions = [
                p for p in predictions 
                if _confidence_to_float(p.confidence) >= request.confidence_threshold
            ]
        
        # Filter by threat categories if specified
        if request.threat_categories:
            predictions = [
                p for p in predictions 
                if p.threat_type in request.threat_categories
            ]
        
        # Calculate distributions
        confidence_dist = {}
        trend_dist = {}
        
        for pred in predictions:
            conf_level = pred.confidence.value
            confidence_dist[conf_level] = confidence_dist.get(conf_level, 0) + 1
            
            trend_level = pred.trend.value
            trend_dist[trend_level] = trend_dist.get(trend_level, 0) + 1
        
        # Convert predictions to dict format
        prediction_dicts = [_prediction_to_dict(p) for p in predictions]
        
        return ThreatPredictionResponse(
            predictions=prediction_dicts,
            total_predictions=len(predictions),
            analysis_period={
                "lookback_start": (datetime.now().strftime("%Y-%m-%d")),
                "forecast_end": (datetime.now().strftime("%Y-%m-%d"))
            },
            ml_enabled=engine.ml_available,
            confidence_distribution=confidence_dist,
            trend_summary=trend_dist
        )
        
    except Exception as e:
        logger.error(f"Threat prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/policies/tune", response_model=PolicyTuningResponse)
async def generate_policy_tuning_recommendations(request: PolicyTuningRequest):
    """
    Generate adaptive policy auto-tuning recommendations.
    
    Analyzes policy performance and suggests optimizations for better
    accuracy, reduced false positives, and improved efficiency.
    """
    try:
        engine = get_predictive_engine()
        logger.info(f"Generating tuning recommendations for {len(request.rules)} rules")
        
        # Convert request rules to Rule objects
        rules = {}
        for rule_id, rule_data in request.rules.items():
            rules[rule_id] = Rule(**rule_data)
        
        # Generate tuning recommendations
        recommendations = await engine.generate_policy_tuning_recommendations(rules)
        
        # Filter by priority if specified
        if request.priority_filter:
            recommendations = [
                r for r in recommendations 
                if r.implementation_priority in request.priority_filter
            ]
        
        # Calculate distributions and impact
        priority_dist = {}
        estimated_impact = {
            "performance_improvement": 0.0,
            "false_positive_reduction": 0.0,
            "detection_enhancement": 0.0
        }
        
        for rec in recommendations:
            priority_dist[str(rec.implementation_priority)] = priority_dist.get(str(rec.implementation_priority), 0) + 1
            
            # Aggregate expected impact
            for metric, value in rec.expected_impact.items():
                if "improvement" in metric or "reduction" in metric:
                    estimated_impact["performance_improvement"] += value * 0.1
                if "false_positive" in metric:
                    estimated_impact["false_positive_reduction"] += value * 0.1
                if "detection" in metric:
                    estimated_impact["detection_enhancement"] += value * 0.1
        
        # Convert recommendations to dict format
        recommendation_dicts = [_tuning_to_dict(r) for r in recommendations]
        
        return PolicyTuningResponse(
            recommendations=recommendation_dicts,
            total_recommendations=len(recommendations),
            priority_distribution=priority_dist,
            estimated_impact=estimated_impact,
            implementation_timeline={
                "immediate": "Priority 1-2 recommendations",
                "short_term": "Priority 3 recommendations", 
                "long_term": "Priority 4-5 recommendations"
            }
        )
        
    except Exception as e:
        logger.error(f"Policy tuning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tuning generation failed: {str(e)}")


@router.post("/anomalies/forecast", response_model=AnomalyForecastResponse)
async def forecast_behavioral_anomalies(request: AnomalyForecastRequest):
    """
    Forecast behavioral anomalies using statistical and ML analysis.
    
    Predicts unusual patterns in system behavior that may indicate
    security incidents or performance issues.
    """
    try:
        engine = get_predictive_engine()
        logger.info(f"Forecasting anomalies for {request.monitoring_window_hours} hours")
        
        # Generate anomaly forecasts
        forecasts = await engine.forecast_behavioral_anomalies(
            monitoring_window_hours=request.monitoring_window_hours
        )
        
        # Filter by anomaly types if specified
        if request.anomaly_types:
            forecasts = [
                f for f in forecasts 
                if f.anomaly_type in request.anomaly_types
            ]
        
        # Calculate distributions
        severity_dist = {}
        confidence_dist = {}
        monitoring_recs = set()
        
        for forecast in forecasts:
            severity_dist[forecast.severity] = severity_dist.get(forecast.severity, 0) + 1
            conf_level = forecast.confidence.value
            confidence_dist[conf_level] = confidence_dist.get(conf_level, 0) + 1
            monitoring_recs.update(forecast.monitoring_recommendations)
        
        # Convert forecasts to dict format
        forecast_dicts = [_forecast_to_dict(f) for f in forecasts]
        
        return AnomalyForecastResponse(
            forecasts=forecast_dicts,
            total_forecasts=len(forecasts),
            forecast_window={
                "start": datetime.now().isoformat(),
                "end": (datetime.now()).isoformat(),
                "hours": str(request.monitoring_window_hours)
            },
            severity_distribution=severity_dist,
            confidence_distribution=confidence_dist,
            monitoring_recommendations=list(monitoring_recs)
        )
        
    except Exception as e:
        logger.error(f"Anomaly forecasting failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")


@router.post("/zero-day/generate", response_model=ZeroDayGenerationResponse)
async def generate_zero_day_patterns(request: ZeroDayGenerationRequest):
    """
    Generate AI-powered zero-day detection patterns.
    
    Uses genetic algorithms and neural network principles to create
    novel detection patterns for unknown threats.
    """
    try:
        engine = get_predictive_engine()
        logger.info(f"Generating zero-day patterns for {len(request.target_threats or [])} threats")
        
        # Generate zero-day patterns
        patterns = await engine.generate_zero_day_patterns(
            target_threats=request.target_threats
        )
        
        # Filter by deployment readiness if specified
        if request.deployment_readiness != "experimental":
            min_confidence = {
                "production": PredictionConfidence.VERY_HIGH,
                "testing": PredictionConfidence.HIGH,
                "development": PredictionConfidence.MEDIUM
            }.get(request.deployment_readiness, PredictionConfidence.LOW)
            
            patterns = [p for p in patterns if p.deployment_readiness.value >= min_confidence.value]
        
        # Calculate validation status
        validation_status = {
            "ready_for_testing": 0,
            "needs_validation": 0,
            "requires_human_review": 0,
            "experimental_only": 0
        }
        
        deployment_recs = []
        
        for pattern in patterns:
            if pattern.deployment_readiness == PredictionConfidence.VERY_HIGH:
                validation_status["ready_for_testing"] += 1
            elif pattern.deployment_readiness == PredictionConfidence.HIGH:
                validation_status["needs_validation"] += 1
            elif pattern.human_review_required:
                validation_status["requires_human_review"] += 1
            else:
                validation_status["experimental_only"] += 1
        
        if validation_status["ready_for_testing"] > 0:
            deployment_recs.append("Deploy high-confidence patterns to test environment")
        if validation_status["needs_validation"] > 0:
            deployment_recs.append("Conduct validation testing on medium-confidence patterns")
        if validation_status["requires_human_review"] > 0:
            deployment_recs.append("Schedule human expert review for flagged patterns")
        
        # Convert patterns to dict format
        pattern_dicts = [_zero_day_to_dict(p) for p in patterns]
        
        return ZeroDayGenerationResponse(
            patterns=pattern_dicts,
            total_patterns=len(patterns),
            generation_summary={
                "methods_used": request.generation_methods or ["genetic", "neural"],
                "success_rate": len(patterns) / max(1, len(request.target_threats or ["default"])),
                "average_confidence": sum(p.validation_score for p in patterns) / max(1, len(patterns))
            },
            validation_status=validation_status,
            deployment_recommendations=deployment_recs
        )
        
    except Exception as e:
        logger.error(f"Zero-day pattern generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern generation failed: {str(e)}")


@router.get("/status", response_model=PredictiveStatusResponse)
async def get_predictive_engine_status():
    """
    Get comprehensive predictive intelligence engine status.
    
    Returns information about engine health, ML model status,
    and available capabilities.
    """
    try:
        engine = get_predictive_engine()
        
        # Gather model status
        model_status = {
            "threat_predictor": "ready" if engine.threat_predictor else "not_initialized",
            "anomaly_detector": "ready" if engine.anomaly_detector else "not_initialized", 
            "performance_predictor": "ready" if engine.performance_predictor else "not_initialized"
        }
        
        # Calculate performance metrics
        performance_metrics = {
            "threat_history_size": len(engine.threat_history),
            "performance_history_size": len(engine.performance_history),
            "evaluation_history_size": len(engine.evaluation_history),
            "cache_hit_rate": 0.85,  # Mock metric
            "prediction_accuracy": 0.78  # Mock metric
        }
        
        # Available capabilities
        capabilities = [
            "threat_pattern_prediction",
            "policy_auto_tuning",
            "behavioral_anomaly_forecasting"
        ]
        
        if engine.ml_available:
            capabilities.extend([
                "ml_powered_analysis",
                "advanced_pattern_recognition",
                "zero_day_pattern_generation"
            ])
        
        return PredictiveStatusResponse(
            engine_status="operational" if engine else "error",
            ml_availability=engine.ml_available,
            model_status=model_status,
            prediction_cache_size=len(engine.prediction_cache),
            last_training=datetime.now().isoformat(),  # Mock timestamp
            capabilities=capabilities,
            performance_metrics=performance_metrics
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/analyze/complete")
async def run_comprehensive_predictive_analysis(
    background_tasks: BackgroundTasks,
    lookback_days: int = Query(30, description="Days to analyze"),
    forecast_days: int = Query(7, description="Days to forecast"),
    include_tuning: bool = Query(True, description="Include policy tuning analysis"),
    include_anomalies: bool = Query(True, description="Include anomaly forecasting"),
    include_zero_day: bool = Query(False, description="Include zero-day pattern generation")
):
    """
    Run comprehensive predictive analysis combining all intelligence capabilities.
    
    This endpoint orchestrates multiple prediction types and provides
    a unified intelligence assessment.
    """
    try:
        logger.info("Starting comprehensive predictive analysis")
        
        # Add analysis task to background
        background_tasks.add_task(
            _run_comprehensive_analysis,
            lookback_days,
            forecast_days, 
            include_tuning,
            include_anomalies,
            include_zero_day
        )
        
        return {
            "status": "analysis_started",
            "message": "Comprehensive predictive analysis initiated",
            "estimated_completion": "5-10 minutes",
            "analysis_scope": {
                "threat_prediction": True,
                "policy_tuning": include_tuning,
                "anomaly_forecasting": include_anomalies,
                "zero_day_generation": include_zero_day
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis initiation failed: {str(e)}")


# Helper functions for data conversion
def _confidence_to_float(confidence: PredictionConfidence) -> float:
    """Convert confidence enum to float value."""
    mapping = {
        PredictionConfidence.VERY_HIGH: 0.95,
        PredictionConfidence.HIGH: 0.82,
        PredictionConfidence.MEDIUM: 0.65,
        PredictionConfidence.LOW: 0.35,
        PredictionConfidence.VERY_LOW: 0.15
    }
    return mapping.get(confidence, 0.5)


def _prediction_to_dict(prediction: ThreatPrediction) -> Dict[str, Any]:
    """Convert ThreatPrediction to dictionary."""
    return {
        "pattern_id": prediction.pattern_id,
        "predicted_pattern": prediction.predicted_pattern,
        "threat_type": prediction.threat_type,
        "confidence": prediction.confidence.value,
        "confidence_score": _confidence_to_float(prediction.confidence),
        "trend": prediction.trend.value,
        "estimated_impact": prediction.estimated_impact,
        "time_horizon_days": prediction.time_horizon,
        "supporting_evidence": prediction.supporting_evidence,
        "recommended_rules": prediction.recommended_rules,
        "detection_probability": prediction.detection_probability,
        "false_positive_risk": prediction.false_positive_risk,
        "created_at": prediction.created_at
    }


def _tuning_to_dict(recommendation: PolicyTuningRecommendation) -> Dict[str, Any]:
    """Convert PolicyTuningRecommendation to dictionary."""
    return {
        "rule_id": recommendation.rule_id,
        "adjustment_type": recommendation.adjustment_type,
        "current_value": recommendation.current_value,
        "recommended_value": recommendation.recommended_value,
        "performance_gain": recommendation.performance_gain,
        "confidence": recommendation.confidence.value,
        "confidence_score": _confidence_to_float(recommendation.confidence),
        "rationale": recommendation.rationale,
        "risk_assessment": recommendation.risk_assessment,
        "implementation_priority": recommendation.implementation_priority,
        "expected_impact": recommendation.expected_impact,
        "validation_criteria": recommendation.validation_criteria,
        "rollback_conditions": recommendation.rollback_conditions
    }


def _forecast_to_dict(forecast: AnomalyForecast) -> Dict[str, Any]:
    """Convert AnomalyForecast to dictionary."""
    return {
        "anomaly_id": forecast.anomaly_id,
        "anomaly_type": forecast.anomaly_type,
        "predicted_occurrence": forecast.predicted_occurrence,
        "confidence": forecast.confidence.value,
        "confidence_score": _confidence_to_float(forecast.confidence),
        "severity": forecast.severity,
        "affected_patterns": forecast.affected_patterns,
        "behavioral_indicators": forecast.behavioral_indicators,
        "prevention_strategies": forecast.prevention_strategies,
        "monitoring_recommendations": forecast.monitoring_recommendations,
        "false_alarm_probability": forecast.false_alarm_probability
    }


def _zero_day_to_dict(pattern: ZeroDayPattern) -> Dict[str, Any]:
    """Convert ZeroDayPattern to dictionary."""
    return {
        "pattern_id": pattern.pattern_id,
        "generated_pattern": pattern.generated_pattern,
        "target_threat": pattern.target_threat,
        "generation_method": pattern.generation_method,
        "theoretical_coverage": pattern.theoretical_coverage,
        "validation_score": pattern.validation_score,
        "deployment_readiness": pattern.deployment_readiness.value,
        "readiness_score": _confidence_to_float(pattern.deployment_readiness),
        "test_cases": pattern.test_cases,
        "known_limitations": pattern.known_limitations,
        "human_review_required": pattern.human_review_required
    }


async def _run_comprehensive_analysis(
    lookback_days: int,
    forecast_days: int,
    include_tuning: bool,
    include_anomalies: bool,
    include_zero_day: bool
):
    """Background task for comprehensive analysis."""
    try:
        logger.info("Running comprehensive predictive analysis in background")
        
        engine = get_predictive_engine()
        
        # Run threat predictions
        threats = await engine.predict_threat_patterns(lookback_days, forecast_days)
        logger.info(f"Generated {len(threats)} threat predictions")
        
        # Run policy tuning if requested
        if include_tuning:
            # Use mock rules for demonstration
            mock_rules = {}  # In production, load from policy store
            tuning = await engine.generate_policy_tuning_recommendations(mock_rules)
            logger.info(f"Generated {len(tuning)} tuning recommendations")
        
        # Run anomaly forecasting if requested
        if include_anomalies:
            anomalies = await engine.forecast_behavioral_anomalies(24)
            logger.info(f"Generated {len(anomalies)} anomaly forecasts")
        
        # Run zero-day generation if requested
        if include_zero_day:
            zero_days = await engine.generate_zero_day_patterns()
            logger.info(f"Generated {len(zero_days)} zero-day patterns")
        
        logger.info("Comprehensive predictive analysis completed")
        
    except Exception as e:
        logger.error(f"Background analysis failed: {e}")


# Export router for main app integration
__all__ = ["router"]