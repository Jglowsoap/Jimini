"""
Jimini Intelligence Module - Advanced AI-Powered Policy Intelligence

Core intelligence capabilities for Jimini policy gateway:
- Phase 6C: Intelligent Policy Recommendations (ML-powered conflict detection & optimization)
- Phase 6D: Predictive Policy Intelligence (threat forecasting & adaptive tuning)
- Phase 7: Reinforcement Learning Framework (contextual bandits & adaptive optimization)

Export structure provides clean access to intelligence capabilities while maintaining
modular architecture for future enhancements.
"""

# Phase 6C - Policy Recommendations (core implementation)
from .policy_recommendations import (
    PolicyRecommendationEngine, PolicyConflict, PolicyRecommendation, 
    CoverageGap, RecommendationType, RecommendationPriority, ConflictType,
    get_policy_recommendation_engine
)
from .policy_recommendations_api import create_policy_recommendations_router

# Phase 6D - Predictive Policy Intelligence (advanced forecasting)
from .predictive_intelligence import (
    PredictiveIntelligenceEngine,
    get_predictive_engine,
    ThreatPrediction,
    PolicyTuningRecommendation,
    AnomalyForecast,
    ZeroDayPattern,
    PredictionConfidence,
    ThreatTrend,
    predict_threats,
    generate_tuning_recommendations,
    forecast_anomalies,
    generate_zero_day_patterns
)
from .predictive_intelligence_api import router as predictive_intelligence_router

# Phase 7 - Reinforcement Learning Framework (contextual optimization)
from .reinforcement_learning import (
    PolicyOptimizer,
    ContextualBandit,
    ThompsonSampler,
    RLContext,
    RLReward,
    PolicyAction,
    ExplorationStrategy,
    policy_optimizer,
    initialize_rl_framework
)
from .reinforcement_learning_api import rl_router

__all__ = [
    # Phase 6C - Policy Recommendations
    'PolicyRecommendationEngine',
    'PolicyConflict',
    'PolicyRecommendation',
    'CoverageGap',
    'RecommendationType',
    'RecommendationPriority', 
    'ConflictType',
    'get_policy_recommendation_engine',
    'create_policy_recommendations_router',
    
    # Phase 6D - Predictive Intelligence
    'PredictiveIntelligenceEngine',
    'get_predictive_engine',
    'ThreatPrediction',
    'PolicyTuningRecommendation',
    'AnomalyForecast',
    'ZeroDayPattern',
    'PredictionConfidence',
    'ThreatTrend',
    'predict_threats',
    'generate_tuning_recommendations',
    'forecast_anomalies',
    'generate_zero_day_patterns',
    'predictive_intelligence_router',
    
    # Phase 7 - Reinforcement Learning
    'PolicyOptimizer',
    'ContextualBandit',
    'ThompsonSampler',
    'RLContext',
    'RLReward',
    'PolicyAction',
    'ExplorationStrategy',
    'policy_optimizer',
    'initialize_rl_framework',
    'rl_router'
]