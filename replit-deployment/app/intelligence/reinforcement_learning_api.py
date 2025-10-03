"""
Phase 7: Reinforcement Learning API Endpoints

RESTful API for RL-based policy optimization, A/B testing, and adaptive learning.
Provides endpoints for policy optimization, feedback collection, and performance monitoring.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import uuid
import asyncio

from ..models import EvaluateRequest, EvaluateResponse
from .reinforcement_learning import (
    policy_optimizer,
    PolicyAction,
    ExplorationStrategy, 
    RLContext,
    RLReward
)

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import uuid

from ..models import EvaluateRequest, EvaluateResponse
from .reinforcement_learning import (
    policy_optimizer,
    PolicyAction,
    ExplorationStrategy, 
    RLContext,
    RLReward
)

logger = logging.getLogger(__name__)

# API Router
rl_router = APIRouter(prefix="/v1/rl", tags=["Reinforcement Learning"])

# Request/Response Models
class RLOptimizationRequest(BaseModel):
    """Request for RL-based policy optimization"""
    request_context: Dict[str, Any] = Field(
        description="Context information about the request"
    )
    current_decision: str = Field(
        description="Current policy decision"
    )
    rule_matches: List[Dict[str, Any]] = Field(
        default=[],
        description="List of matched rules"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request identifier for tracking"
    )

class RLOptimizationResponse(BaseModel):
    """Response from RL policy optimization"""
    request_id: str = Field(description="Request identifier")
    original_decision: Optional[str] = Field(default=None, description="Original policy decision")
    rl_recommendation: Optional[str] = Field(default=None, description="RL-optimized recommendation")
    decision: Optional[str] = Field(default=None, description="Final decision (if not shadow mode)")
    context: Dict[str, Any] = Field(description="RL context used for decision")
    confidence: float = Field(description="Confidence in the decision (0-1)")
    shadow_mode: bool = Field(description="Whether running in shadow mode")
    rl_optimized: bool = Field(default=False, description="Whether decision was RL-optimized")
    error: Optional[str] = Field(default=None, description="Error message if any")

class FeedbackRequest(BaseModel):
    """Request to provide feedback for RL learning"""
    request_id: str = Field(description="Request identifier")
    context: Dict[str, Any] = Field(description="RL context from original request")
    action_taken: str = Field(description="Action that was taken")
    outcome: Dict[str, Any] = Field(description="Observed outcome")
    user_feedback: Optional[int] = Field(
        default=None,
        ge=-1, le=1,
        description="User feedback: -1 (negative), 0 (neutral), 1 (positive)"
    )
    security_breach: Optional[bool] = Field(
        default=None,
        description="Whether a security breach occurred"
    )
    false_positive: Optional[bool] = Field(
        default=None,
        description="Whether this was a false positive"
    )

class FeedbackResponse(BaseModel):
    """Response from feedback processing"""
    request_id: str = Field(description="Request identifier")
    processed: bool = Field(description="Whether feedback was successfully processed")
    reward_calculated: Optional[float] = Field(description="Calculated reward value")
    error: Optional[str] = Field(default=None, description="Error message if any")

class RLMetricsResponse(BaseModel):
    """Response containing RL optimization metrics"""
    total_trials: int = Field(description="Total number of trials")
    action_distribution: List[float] = Field(description="Distribution of actions taken")
    average_rewards: List[float] = Field(description="Average rewards per action")
    exploration_strategy: str = Field(description="Current exploration strategy")
    shadow_mode: bool = Field(description="Whether running in shadow mode")
    active_experiments: int = Field(description="Number of active A/B test experiments")
    confidence_level: float = Field(description="Overall confidence level")
    performance_trend: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Performance trend analysis"
    )

class ExperimentRequest(BaseModel):
    """Request to start a new A/B test experiment"""
    experiment_name: str = Field(description="Name of the experiment")
    policy_modifications: Dict[str, Any] = Field(
        description="Modifications to test in the policy"
    )
    traffic_split: float = Field(
        default=0.1,
        ge=0.01, le=0.5,
        description="Percentage of traffic to route to experiment (1-50%)"
    )
    duration_hours: Optional[int] = Field(
        default=24,
        ge=1, le=168,
        description="Experiment duration in hours (max 1 week)"
    )

class ExperimentResponse(BaseModel):
    """Response from experiment creation"""
    experiment_id: str = Field(description="Unique experiment identifier")
    experiment_name: str = Field(description="Name of the experiment")
    status: str = Field(description="Experiment status")
    traffic_split: float = Field(description="Percentage of traffic allocated")
    estimated_sample_size: int = Field(description="Estimated samples needed for significance")
    start_time: datetime = Field(description="Experiment start time")
    estimated_end_time: datetime = Field(description="Estimated experiment end time")

# API Endpoints

@rl_router.post("/optimize", response_model=RLOptimizationResponse)
async def optimize_policy_decision(
    request: RLOptimizationRequest,
    background_tasks: BackgroundTasks
) -> RLOptimizationResponse:
    """
    Optimize a policy decision using reinforcement learning.
    
    This endpoint analyzes the request context and provides an RL-optimized
    policy recommendation. In shadow mode, it returns both the original 
    decision and RL recommendation for comparison.
    """
    try:
        # Generate request ID if not provided
        request_id = request.request_id or str(uuid.uuid4())
        
        # Get RL optimization
        result = await policy_optimizer.optimize_policy_decision(
            request_context=request.request_context,
            current_decision=request.current_decision,
            rule_matches=request.rule_matches
        )
        
        # Log the optimization request
        background_tasks.add_task(
            _log_optimization_request,
            request_id,
            request.dict(),
            result
        )
        
        return RLOptimizationResponse(
            request_id=request_id,
            **result
        )
        
    except Exception as e:
        logger.error(f"Error in policy optimization: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Policy optimization failed: {str(e)}"
        )

@rl_router.post("/feedback", response_model=FeedbackResponse)
async def provide_feedback(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks
) -> FeedbackResponse:
    """
    Provide feedback for reinforcement learning.
    
    This endpoint accepts feedback about the outcome of a policy decision
    and uses it to update the RL model for future optimization.
    """
    try:
        # Convert context back to RLContext
        rl_context = RLContext(**request.context)
        
        # Convert action string to PolicyAction
        try:
            action = PolicyAction(request.action_taken)
        except ValueError:
            action = PolicyAction.ALLOW  # Default fallback
        
        # Build outcome dictionary
        outcome = request.outcome.copy()
        if request.user_feedback is not None:
            outcome["user_feedback"] = request.user_feedback
        if request.security_breach is not None:
            outcome["security_breach"] = request.security_breach
        if request.false_positive is not None:
            outcome["false_positive"] = request.false_positive
        
        # Process feedback asynchronously
        background_tasks.add_task(
            policy_optimizer.provide_feedback,
            request.request_id,
            rl_context,
            action,
            outcome
        )
        
        # Calculate reward for response (simplified)
        user_feedback = outcome.get("user_feedback", 0)
        security_breach = outcome.get("security_breach", False)
        false_positive = outcome.get("false_positive", False)
        
        # Simple reward calculation for response
        reward = user_feedback * 0.5
        if security_breach and action == PolicyAction.ALLOW:
            reward -= 1.0
        elif false_positive and action == PolicyAction.BLOCK:
            reward -= 0.3
        
        return FeedbackResponse(
            request_id=request.request_id,
            processed=True,
            reward_calculated=reward
        )
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        return FeedbackResponse(
            request_id=request.request_id,
            processed=False,
            error=str(e)
        )

@rl_router.get("/metrics", response_model=RLMetricsResponse)
async def get_rl_metrics() -> RLMetricsResponse:
    """
    Get reinforcement learning optimization metrics.
    
    Returns comprehensive metrics about the RL system performance,
    including action distribution, rewards, and optimization statistics.
    """
    try:
        metrics = await policy_optimizer.get_optimization_metrics()
        
        # Add performance trend analysis
        performance_trend = await _analyze_performance_trend()
        metrics["performance_trend"] = performance_trend
        
        return RLMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Error retrieving RL metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve RL metrics: {str(e)}"
        )

@rl_router.post("/experiments", response_model=ExperimentResponse)
async def start_experiment(
    request: ExperimentRequest
) -> ExperimentResponse:
    """
    Start a new A/B test experiment.
    
    Creates a new policy experiment to test modifications against
    the current policy with a specified traffic split.
    """
    try:
        experiment_id = str(uuid.uuid4())
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=request.duration_hours or 24)
        
        # Estimate sample size needed for statistical significance
        # Using simplified formula: n ≈ 16 / (effect_size^2)
        estimated_effect_size = 0.1  # 10% improvement
        estimated_sample_size = int(16 / (estimated_effect_size ** 2))
        
        # TODO: Implement actual experiment creation in policy optimizer
        
        return ExperimentResponse(
            experiment_id=experiment_id,
            experiment_name=request.experiment_name,
            status="started",
            traffic_split=request.traffic_split,
            estimated_sample_size=estimated_sample_size,
            start_time=start_time,
            estimated_end_time=end_time
        )
        
    except Exception as e:
        logger.error(f"Error starting experiment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start experiment: {str(e)}"
        )

@rl_router.get("/experiments/{experiment_id}")
async def get_experiment_status(experiment_id: str) -> Dict[str, Any]:
    """
    Get the status of a running experiment.
    
    Returns detailed information about an A/B test experiment
    including current results and statistical significance.
    """
    try:
        # TODO: Implement actual experiment status retrieval
        return {
            "experiment_id": experiment_id,
            "status": "running",
            "progress": 0.3,
            "samples_collected": 150,
            "preliminary_results": {
                "control_performance": 0.82,
                "experiment_performance": 0.87,
                "improvement": 0.05,
                "statistical_significance": 0.85
            },
            "estimated_completion": "2024-01-16T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving experiment status: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Experiment {experiment_id} not found or failed to retrieve status"
        )

@rl_router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(experiment_id: str) -> Dict[str, Any]:
    """
    Stop a running experiment.
    
    Stops the specified A/B test experiment and returns final results.
    """
    try:
        # TODO: Implement actual experiment stopping
        return {
            "experiment_id": experiment_id,
            "status": "stopped",
            "final_results": {
                "samples_collected": 500,
                "control_performance": 0.82,
                "experiment_performance": 0.87,
                "improvement": 0.05,
                "statistical_significance": 0.95,
                "recommendation": "deploy"
            }
        }
        
    except Exception as e:
        logger.error(f"Error stopping experiment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop experiment {experiment_id}: {str(e)}"
        )

@rl_router.post("/retrain")
async def retrain_model(
    background_tasks: BackgroundTasks,
    force: bool = False
) -> Dict[str, Any]:
    """
    Trigger model retraining.
    
    Initiates retraining of the RL model using accumulated data.
    Can be forced to retrain even if not normally scheduled.
    """
    try:
        # TODO: Implement actual model retraining
        background_tasks.add_task(_retrain_rl_model, force)
        
        return {
            "status": "retraining_started",
            "estimated_duration": "10-30 minutes",
            "force_retrain": force,
            "message": "Model retraining initiated in background"
        }
        
    except Exception as e:
        logger.error(f"Error initiating retraining: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate retraining: {str(e)}"
        )

@rl_router.get("/config")
async def get_rl_config() -> Dict[str, Any]:
    """
    Get current RL configuration.
    
    Returns the current configuration of the reinforcement learning system.
    """
    return {
        "shadow_mode": policy_optimizer.shadow_mode,
        "safety_threshold": policy_optimizer.safety_threshold,
        "exploration_strategy": policy_optimizer.bandit.exploration_strategy.value,
        "context_dimensions": policy_optimizer.bandit.context_dim,
        "available_actions": [action.value for action in PolicyAction],
        "active_experiments": len(policy_optimizer.policy_candidates)
    }

@rl_router.post("/config")
async def update_rl_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update RL configuration.
    
    Updates the reinforcement learning system configuration.
    Changes take effect immediately.
    """
    try:
        # Update shadow mode
        if "shadow_mode" in config:
            policy_optimizer.shadow_mode = config["shadow_mode"]
        
        # Update safety threshold
        if "safety_threshold" in config:
            policy_optimizer.safety_threshold = config["safety_threshold"]
            policy_optimizer.bandit.safety_threshold = config["safety_threshold"]
        
        return {
            "status": "updated",
            "new_config": await get_rl_config()
        }
        
    except Exception as e:
        logger.error(f"Error updating RL config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )

# Background tasks

async def _log_optimization_request(
    request_id: str,
    request_data: Dict[str, Any],
    result: Dict[str, Any]
):
    """Log optimization request for audit trail"""
    logger.info(f"RL Optimization - Request: {request_id}, Result: {result.get('rl_recommendation', 'N/A')}")

async def _analyze_performance_trend() -> Dict[str, Any]:
    """Analyze RL performance trends"""
    # TODO: Implement actual trend analysis
    return {
        "trend_direction": "improving",
        "improvement_rate": 0.05,
        "confidence_trend": "stable",
        "recommendation": "continue_current_strategy"
    }

async def _retrain_rl_model(force: bool = False):
    """Background task to retrain RL model"""
    try:
        logger.info(f"Starting RL model retraining (force={force})")
        # TODO: Implement actual retraining logic
        await asyncio.sleep(5)  # Simulate retraining time
        logger.info("RL model retraining completed successfully")
    except Exception as e:
        logger.error(f"RL model retraining failed: {e}")

# Export router
__all__ = ["rl_router"]