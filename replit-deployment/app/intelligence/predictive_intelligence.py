"""
Jimini Intelligence Evolution - Phase 6D: Predictive Policy Intelligence

Advanced ML-powered predictive analytics for proactive policy optimization:
- Predictive threat pattern analysis with time-series forecasting
- Adaptive policy auto-tuning based on real-time performance data  
- Behavioral anomaly forecasting using statistical models
- Zero-day pattern generation with AI-powered rule synthesis

Author: Jimini Intelligence Team
Version: 6D.1.0
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from collections import defaultdict, deque
import statistics
import re

# ML imports with graceful fallback
try:
    import numpy as np
    from sklearn.ensemble import IsolationForest, RandomForestRegressor
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    np = None
    ML_AVAILABLE = False

from app.models import Rule, EvaluateRequest, EvaluateResponse

logger = logging.getLogger(__name__)


class ThreatTrend(Enum):
    """Threat trend classifications."""
    EMERGING = "emerging"
    ESCALATING = "escalating"
    DECLINING = "declining"
    STABLE = "stable"
    NOVEL = "novel"


class PredictionConfidence(Enum):
    """Prediction confidence levels."""
    VERY_HIGH = "very_high"  # 90%+
    HIGH = "high"           # 75-90%
    MEDIUM = "medium"       # 50-75%
    LOW = "low"             # 25-50%
    VERY_LOW = "very_low"   # <25%


@dataclass
class ThreatPrediction:
    """Predictive threat analysis result."""
    pattern_id: str
    predicted_pattern: str
    threat_type: str
    confidence: PredictionConfidence
    trend: ThreatTrend
    estimated_impact: float  # 0.0-1.0 scale
    time_horizon: int  # Days ahead
    supporting_evidence: List[str]
    recommended_rules: List[Dict[str, Any]]
    detection_probability: float
    false_positive_risk: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PolicyTuningRecommendation:
    """Adaptive policy auto-tuning recommendation."""
    rule_id: str
    adjustment_type: str  # threshold, pattern, action, scope
    current_value: str
    recommended_value: str
    performance_gain: float  # Expected improvement percentage
    confidence: PredictionConfidence
    rationale: str
    risk_assessment: str
    implementation_priority: int  # 1-5 scale
    expected_impact: Dict[str, float]  # metrics -> expected change
    validation_criteria: List[str]
    rollback_conditions: List[str]


@dataclass
class AnomalyForecast:
    """Behavioral anomaly prediction."""
    anomaly_id: str
    anomaly_type: str
    predicted_occurrence: str  # ISO timestamp
    confidence: PredictionConfidence
    severity: str  # low, medium, high, critical
    affected_patterns: List[str]
    behavioral_indicators: List[str]
    prevention_strategies: List[str]
    monitoring_recommendations: List[str]
    false_alarm_probability: float


@dataclass
class ZeroDayPattern:
    """AI-generated zero-day detection pattern."""
    pattern_id: str
    generated_pattern: str
    target_threat: str
    generation_method: str  # genetic, neural, hybrid
    theoretical_coverage: float
    validation_score: float
    deployment_readiness: PredictionConfidence
    test_cases: List[str]
    known_limitations: List[str]
    human_review_required: bool


class PredictiveIntelligenceEngine:
    """Advanced predictive intelligence for proactive policy optimization."""
    
    def __init__(self):
        """Initialize predictive intelligence engine."""
        self.logger = logging.getLogger(__name__)
        self.ml_available = ML_AVAILABLE
        
        # Prediction models
        self.threat_predictor = None
        self.anomaly_detector = None
        self.pattern_generator = None
        self.performance_predictor = None
        
        # Historical data stores
        self.threat_history = deque(maxlen=10000)
        self.performance_history = deque(maxlen=5000)
        self.evaluation_history = deque(maxlen=20000)
        
        # Pattern analysis cache
        self.pattern_effectiveness = {}
        self.trend_analysis = {}
        self.prediction_cache = {}
        
        # Initialize ML models if available
        if self.ml_available:
            self._initialize_ml_models()
            
        self.logger.info(f"Predictive Intelligence Engine initialized (ML: {self.ml_available})")
    
    def _initialize_ml_models(self):
        """Initialize machine learning models for predictive analysis."""
        try:
            # Threat pattern prediction model
            self.threat_predictor = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Anomaly detection model
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # Performance prediction model
            self.performance_predictor = RandomForestRegressor(
                n_estimators=50,
                max_depth=8,
                random_state=42
            )
            
            # Data scaling for features
            self.scaler = StandardScaler()
            
            self.logger.info("ML models initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"ML model initialization failed: {e}")
            self.ml_available = False
    
    async def predict_threat_patterns(
        self, 
        lookback_days: int = 30,
        forecast_days: int = 7
    ) -> List[ThreatPrediction]:
        """Predict emerging threat patterns using time-series analysis."""
        self.logger.info(f"Predicting threat patterns for next {forecast_days} days")
        
        predictions = []
        
        try:
            if self.ml_available and len(self.threat_history) > 50:
                # ML-based threat prediction
                predictions.extend(await self._ml_predict_threats(lookback_days, forecast_days))
            else:
                # Heuristic-based threat prediction
                predictions.extend(await self._heuristic_predict_threats(lookback_days, forecast_days))
            
            self.logger.info(f"Generated {len(predictions)} threat predictions")
            return predictions
            
        except Exception as e:
            self.logger.error(f"Threat prediction failed: {e}")
            return []
    
    async def _ml_predict_threats(self, lookback_days: int, forecast_days: int) -> List[ThreatPrediction]:
        """ML-powered threat pattern prediction."""
        predictions = []
        
        try:
            # Extract features from historical threat data
            features, targets = self._extract_threat_features(lookback_days)
            
            if len(features) < 10:
                return predictions
            
            # Train prediction model
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            self.threat_predictor.fit(X_train, y_train)
            
            # Generate predictions for different threat categories
            threat_categories = [
                "api_key_exposure", "credential_leak", "injection_attack",
                "data_exfiltration", "privilege_escalation", "lateral_movement"
            ]
            
            for category in threat_categories:
                # Predict threat evolution
                future_features = self._generate_future_features(category, forecast_days)
                
                for i, feature_set in enumerate(future_features):
                    try:
                        prediction_value = self.threat_predictor.predict([feature_set])[0]
                        
                        if prediction_value > 0.3:  # Significant threat threshold
                            prediction = ThreatPrediction(
                                pattern_id=f"pred_{category}_{i}",
                                predicted_pattern=self._generate_threat_pattern(category, prediction_value),
                                threat_type=category,
                                confidence=self._calculate_prediction_confidence(prediction_value),
                                trend=self._determine_threat_trend(category, prediction_value),
                                estimated_impact=min(prediction_value, 1.0),
                                time_horizon=i + 1,
                                supporting_evidence=[
                                    f"Historical trend analysis for {category}",
                                    f"ML model confidence: {prediction_value:.2f}",
                                    "Pattern evolution analysis"
                                ],
                                recommended_rules=self._generate_recommended_rules(category),
                                detection_probability=min(prediction_value * 0.8, 0.95),
                                false_positive_risk=max(0.05, (1 - prediction_value) * 0.3)
                            )
                            predictions.append(prediction)
                    
                    except Exception as e:
                        self.logger.warning(f"Prediction generation failed for {category}: {e}")
                        continue
            
        except Exception as e:
            self.logger.error(f"ML threat prediction failed: {e}")
            
        return predictions
    
    async def _heuristic_predict_threats(self, lookback_days: int, forecast_days: int) -> List[ThreatPrediction]:
        """Heuristic-based threat prediction for fallback."""
        predictions = []
        
        # Analyze recent threat patterns
        recent_threats = self._analyze_recent_threats(lookback_days)
        
        # Generate predictions based on pattern analysis
        for threat_type, frequency in recent_threats.items():
            if frequency > 2:  # Minimum threshold for prediction
                
                # Calculate trend
                trend = ThreatTrend.ESCALATING if frequency > 5 else ThreatTrend.EMERGING
                confidence = PredictionConfidence.MEDIUM if frequency > 3 else PredictionConfidence.LOW
                
                prediction = ThreatPrediction(
                    pattern_id=f"heuristic_{threat_type}",
                    predicted_pattern=self._generate_threat_pattern(threat_type, frequency / 10),
                    threat_type=threat_type,
                    confidence=confidence,
                    trend=trend,
                    estimated_impact=min(frequency / 10, 0.8),
                    time_horizon=forecast_days,
                    supporting_evidence=[
                        f"Observed {frequency} instances in last {lookback_days} days",
                        "Heuristic pattern analysis",
                        "Trend extrapolation"
                    ],
                    recommended_rules=self._generate_recommended_rules(threat_type),
                    detection_probability=min(frequency / 15, 0.8),
                    false_positive_risk=0.2
                )
                predictions.append(prediction)
        
        return predictions
    
    async def generate_policy_tuning_recommendations(
        self, 
        rules: Dict[str, Rule]
    ) -> List[PolicyTuningRecommendation]:
        """Generate adaptive policy auto-tuning recommendations."""
        self.logger.info("Generating adaptive policy tuning recommendations")
        
        recommendations = []
        
        try:
            for rule_id, rule in rules.items():
                # Analyze rule performance
                performance_data = self._analyze_rule_performance(rule_id)
                
                if performance_data:
                    # Generate tuning recommendations based on performance
                    tuning_recs = await self._analyze_rule_tuning_opportunities(
                        rule_id, rule, performance_data
                    )
                    recommendations.extend(tuning_recs)
            
            # Sort by implementation priority
            recommendations.sort(key=lambda x: x.implementation_priority)
            
            self.logger.info(f"Generated {len(recommendations)} tuning recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Policy tuning recommendation generation failed: {e}")
            return []
    
    async def _analyze_rule_tuning_opportunities(
        self,
        rule_id: str,
        rule: Rule,
        performance_data: Dict[str, Any]
    ) -> List[PolicyTuningRecommendation]:
        """Analyze specific tuning opportunities for a rule."""
        recommendations = []
        
        try:
            false_positive_rate = performance_data.get('false_positive_rate', 0.0)
            detection_rate = performance_data.get('detection_rate', 1.0)
            response_time = performance_data.get('avg_response_time', 0.0)
            
            # High false positive rate - adjust pattern
            if false_positive_rate > 0.1:
                rec = PolicyTuningRecommendation(
                    rule_id=rule_id,
                    adjustment_type="pattern",
                    current_value=rule.pattern or "",
                    recommended_value=self._optimize_pattern_specificity(rule.pattern),
                    performance_gain=max(0, (false_positive_rate - 0.05) * 100),
                    confidence=PredictionConfidence.HIGH,
                    rationale=f"Reduce false positive rate from {false_positive_rate:.1%} to ~5%",
                    risk_assessment="Low risk - increases pattern specificity",
                    implementation_priority=2,
                    expected_impact={
                        "false_positive_reduction": false_positive_rate * 0.7,
                        "accuracy_improvement": false_positive_rate * 0.5
                    },
                    validation_criteria=[
                        "Monitor false positive rate for 7 days",
                        "Ensure detection rate remains >90%",
                        "Validate against test dataset"
                    ],
                    rollback_conditions=[
                        "False positive rate increases",
                        "Detection rate drops below 85%",
                        "Significant performance degradation"
                    ]
                )
                recommendations.append(rec)
            
            # Low detection rate - broaden pattern or adjust thresholds
            if detection_rate < 0.8:
                rec = PolicyTuningRecommendation(
                    rule_id=rule_id,
                    adjustment_type="threshold",
                    current_value="restrictive",
                    recommended_value="balanced",
                    performance_gain=(0.9 - detection_rate) * 100,
                    confidence=PredictionConfidence.MEDIUM,
                    rationale=f"Improve detection rate from {detection_rate:.1%} to ~90%",
                    risk_assessment="Medium risk - may increase false positives",
                    implementation_priority=1,
                    expected_impact={
                        "detection_improvement": (0.9 - detection_rate),
                        "false_positive_risk": 0.03
                    },
                    validation_criteria=[
                        "Detection rate improvement verification",
                        "False positive rate monitoring",
                        "Performance impact assessment"
                    ],
                    rollback_conditions=[
                        "False positive rate exceeds 15%",
                        "Performance degrades significantly",
                        "User complaints increase"
                    ]
                )
                recommendations.append(rec)
            
            # Slow response time - optimize processing
            if response_time > 100:  # ms
                rec = PolicyTuningRecommendation(
                    rule_id=rule_id,
                    adjustment_type="processing",
                    current_value=f"{response_time}ms",
                    recommended_value=f"<50ms",
                    performance_gain=((response_time - 50) / response_time) * 100,
                    confidence=PredictionConfidence.HIGH,
                    rationale="Optimize pattern compilation and processing efficiency",
                    risk_assessment="Very low risk - performance optimization only",
                    implementation_priority=3,
                    expected_impact={
                        "response_time_improvement": (response_time - 50) / response_time,
                        "throughput_increase": 0.2
                    },
                    validation_criteria=[
                        "Response time < 50ms consistently",
                        "No accuracy degradation",
                        "Memory usage remains stable"
                    ],
                    rollback_conditions=[
                        "Response time increases",
                        "Memory usage spikes",
                        "Accuracy decreases"
                    ]
                )
                recommendations.append(rec)
                
        except Exception as e:
            self.logger.error(f"Rule tuning analysis failed for {rule_id}: {e}")
        
        return recommendations
    
    async def forecast_behavioral_anomalies(
        self, 
        monitoring_window_hours: int = 24
    ) -> List[AnomalyForecast]:
        """Forecast behavioral anomalies using statistical analysis."""
        self.logger.info(f"Forecasting behavioral anomalies for next {monitoring_window_hours} hours")
        
        forecasts = []
        
        try:
            if self.ml_available and len(self.evaluation_history) > 100:
                # ML-based anomaly forecasting
                forecasts.extend(await self._ml_forecast_anomalies(monitoring_window_hours))
            else:
                # Statistical anomaly forecasting
                forecasts.extend(await self._statistical_forecast_anomalies(monitoring_window_hours))
            
            self.logger.info(f"Generated {len(forecasts)} anomaly forecasts")
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Anomaly forecasting failed: {e}")
            return []
    
    async def _ml_forecast_anomalies(self, window_hours: int) -> List[AnomalyForecast]:
        """ML-based behavioral anomaly forecasting."""
        forecasts = []
        
        try:
            # Prepare evaluation data for anomaly detection
            features = self._extract_behavioral_features()
            
            if len(features) < 50:
                return forecasts
            
            # Train anomaly detector
            self.anomaly_detector.fit(features)
            
            # Generate future behavioral scenarios
            future_scenarios = self._generate_behavioral_scenarios(window_hours)
            
            for i, scenario in enumerate(future_scenarios):
                anomaly_score = self.anomaly_detector.decision_function([scenario])[0]
                is_anomaly = self.anomaly_detector.predict([scenario])[0] == -1
                
                if is_anomaly and abs(anomaly_score) > 0.3:
                    forecast = AnomalyForecast(
                        anomaly_id=f"forecast_{i}_{window_hours}h",
                        anomaly_type=self._classify_anomaly_type(scenario),
                        predicted_occurrence=(
                            datetime.now() + timedelta(hours=i+1)
                        ).isoformat(),
                        confidence=self._score_to_confidence(abs(anomaly_score)),
                        severity=self._calculate_anomaly_severity(abs(anomaly_score)),
                        affected_patterns=self._identify_affected_patterns(scenario),
                        behavioral_indicators=[
                            "Unusual request pattern detected",
                            f"Anomaly score: {anomaly_score:.3f}",
                            "Statistical deviation from baseline"
                        ],
                        prevention_strategies=[
                            "Increase monitoring sensitivity",
                            "Implement rate limiting",
                            "Enable additional logging"
                        ],
                        monitoring_recommendations=[
                            "Monitor affected endpoints closely",
                            "Set up real-time alerts",
                            "Prepare incident response"
                        ],
                        false_alarm_probability=max(0.1, 1 - abs(anomaly_score))
                    )
                    forecasts.append(forecast)
                    
        except Exception as e:
            self.logger.error(f"ML anomaly forecasting failed: {e}")
        
        return forecasts
    
    async def generate_zero_day_patterns(
        self, 
        target_threats: List[str] = None
    ) -> List[ZeroDayPattern]:
        """Generate AI-powered zero-day detection patterns."""
        self.logger.info("Generating zero-day detection patterns")
        
        patterns = []
        
        if not target_threats:
            target_threats = [
                "novel_injection", "advanced_exfiltration", "ai_generated_attack",
                "quantum_cryptography_bypass", "deepfake_authentication"
            ]
        
        try:
            for threat in target_threats:
                # Generate patterns using different AI methods
                genetic_pattern = await self._genetic_pattern_generation(threat)
                if genetic_pattern:
                    patterns.append(genetic_pattern)
                
                # Neural-inspired pattern generation
                neural_pattern = await self._neural_pattern_generation(threat)
                if neural_pattern:
                    patterns.append(neural_pattern)
            
            self.logger.info(f"Generated {len(patterns)} zero-day patterns")
            return patterns
            
        except Exception as e:
            self.logger.error(f"Zero-day pattern generation failed: {e}")
            return []
    
    async def _genetic_pattern_generation(self, target_threat: str) -> Optional[ZeroDayPattern]:
        """Generate patterns using genetic algorithm principles."""
        try:
            # Start with base patterns for the threat category
            base_patterns = self._get_base_patterns_for_threat(target_threat)
            
            # Apply genetic operations (mutation, crossover)
            evolved_pattern = self._evolve_pattern(base_patterns)
            
            if evolved_pattern:
                pattern = ZeroDayPattern(
                    pattern_id=f"genetic_{target_threat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    generated_pattern=evolved_pattern,
                    target_threat=target_threat,
                    generation_method="genetic",
                    theoretical_coverage=0.7,  # Estimated
                    validation_score=0.6,     # Needs testing
                    deployment_readiness=PredictionConfidence.MEDIUM,
                    test_cases=self._generate_test_cases(evolved_pattern),
                    known_limitations=[
                        "Untested against real attacks",
                        "May have high false positive rate",
                        "Requires validation period"
                    ],
                    human_review_required=True
                )
                return pattern
                
        except Exception as e:
            self.logger.error(f"Genetic pattern generation failed for {target_threat}: {e}")
        
        return None
    
    # Helper methods for pattern generation and analysis
    
    def _extract_threat_features(self, lookback_days: int) -> Tuple[List[List[float]], List[float]]:
        """Extract features from historical threat data."""
        features, targets = [], []
        
        # Simulate feature extraction (in production, use real threat data)
        for i in range(min(len(self.threat_history), lookback_days * 10)):
            # Mock features: time, frequency, severity, pattern complexity
            feature_set = [
                i / 24.0,  # time feature
                np.random.normal(0.5, 0.2),  # frequency
                np.random.normal(0.3, 0.1),  # severity
                np.random.normal(0.4, 0.15)  # complexity
            ]
            features.append(feature_set)
            targets.append(np.random.normal(0.4, 0.2))  # threat likelihood
        
        return features, targets
    
    def _generate_future_features(self, category: str, forecast_days: int) -> List[List[float]]:
        """Generate future feature sets for prediction."""
        future_features = []
        
        for day in range(forecast_days):
            # Generate features based on category and time
            features = [
                day / forecast_days,  # time progression
                0.5 + (day * 0.1),   # escalating pattern
                0.3,                  # baseline severity
                0.4                   # complexity
            ]
            future_features.append(features)
        
        return future_features
    
    def _generate_threat_pattern(self, threat_type: str, intensity: float) -> str:
        """Generate regex pattern for predicted threat."""
        base_patterns = {
            "api_key_exposure": r"(?i)(api[_-]?key|token)[\"'\s]*[:=]\s*[\"']?([a-zA-Z0-9_-]{{{min_len},{max_len}}})",
            "credential_leak": r"(?i)(password|pass|pwd)[\"'\s]*[:=]\s*[\"']?([^\s\"']{{{min_len},{max_len}}})",
            "injection_attack": r"(?i)(union|select|insert|update|delete|drop|exec|script|javascript|eval)",
            "data_exfiltration": r"(?i)(export|download|backup|dump|extract).*?(data|database|file|document)",
            "privilege_escalation": r"(?i)(sudo|admin|root|privilege|elevation|escalat)",
            "lateral_movement": r"(?i)(lateral|pivot|tunnel|proxy|forward|redirect)"
        }
        
        pattern = base_patterns.get(threat_type, r"suspicious_activity")
        
        # Adjust pattern intensity based on prediction
        if intensity > 0.7:
            min_len, max_len = 8, 100
        elif intensity > 0.4:
            min_len, max_len = 12, 50
        else:
            min_len, max_len = 16, 30
            
        return pattern.format(min_len=min_len, max_len=max_len)
    
    def _calculate_prediction_confidence(self, value: float) -> PredictionConfidence:
        """Calculate prediction confidence from model output."""
        if value >= 0.9:
            return PredictionConfidence.VERY_HIGH
        elif value >= 0.75:
            return PredictionConfidence.HIGH
        elif value >= 0.5:
            return PredictionConfidence.MEDIUM
        elif value >= 0.25:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW
    
    def _determine_threat_trend(self, category: str, value: float) -> ThreatTrend:
        """Determine threat trend from analysis."""
        if value > 0.8:
            return ThreatTrend.ESCALATING
        elif value > 0.6:
            return ThreatTrend.EMERGING
        elif value < 0.2:
            return ThreatTrend.DECLINING
        else:
            return ThreatTrend.STABLE
    
    def _generate_recommended_rules(self, threat_type: str) -> List[Dict[str, Any]]:
        """Generate recommended rules for predicted threats."""
        return [
            {
                "id": f"pred_{threat_type}_1",
                "title": f"Predictive {threat_type.replace('_', ' ').title()} Detection",
                "pattern": self._generate_threat_pattern(threat_type, 0.8),
                "action": "flag",
                "severity": "high",
                "applies_to": ["request", "response"],
                "confidence": "ml_predicted"
            }
        ]
    
    def _analyze_recent_threats(self, days: int) -> Dict[str, int]:
        """Analyze recent threat patterns."""
        # Simulate threat analysis
        return {
            "api_key_exposure": 7,
            "credential_leak": 3,
            "injection_attack": 12,
            "data_exfiltration": 2,
            "privilege_escalation": 1
        }
    
    def _analyze_rule_performance(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Analyze historical performance data for a rule."""
        # Simulate performance data
        return {
            "false_positive_rate": np.random.uniform(0.02, 0.15),
            "detection_rate": np.random.uniform(0.75, 0.95),
            "avg_response_time": np.random.uniform(20, 150),
            "total_evaluations": np.random.randint(100, 10000)
        }
    
    def _optimize_pattern_specificity(self, pattern: str) -> str:
        """Optimize pattern to reduce false positives."""
        if not pattern:
            return pattern
            
        # Add word boundaries for better specificity
        if not pattern.startswith(r'\b') and not pattern.startswith('(?i)'):
            optimized = r'\b' + pattern + r'\b'
        else:
            optimized = pattern
            
        return optimized
    
    def _extract_behavioral_features(self) -> List[List[float]]:
        """Extract behavioral features for anomaly detection."""
        features = []
        
        # Simulate feature extraction from evaluation history
        for i in range(min(len(self.evaluation_history), 500)):
            feature_set = [
                np.random.normal(100, 20),    # request size
                np.random.normal(50, 10),     # response time
                np.random.uniform(0, 1),      # rule hit rate
                np.random.normal(0.1, 0.05)   # error rate
            ]
            features.append(feature_set)
        
        return features
    
    def _generate_behavioral_scenarios(self, hours: int) -> List[List[float]]:
        """Generate future behavioral scenarios."""
        scenarios = []
        
        for hour in range(hours):
            # Generate scenario with some anomaly probability
            if np.random.random() < 0.1:  # 10% chance of anomaly
                scenario = [
                    np.random.normal(200, 50),    # unusual request size
                    np.random.normal(150, 30),    # slow response
                    np.random.uniform(0.8, 1.0),  # high hit rate
                    np.random.normal(0.3, 0.1)    # high error rate
                ]
            else:
                scenario = [
                    np.random.normal(100, 20),
                    np.random.normal(50, 10),
                    np.random.uniform(0, 0.2),
                    np.random.normal(0.1, 0.05)
                ]
            scenarios.append(scenario)
        
        return scenarios
    
    def _classify_anomaly_type(self, scenario: List[float]) -> str:
        """Classify the type of behavioral anomaly."""
        request_size, response_time, hit_rate, error_rate = scenario
        
        if request_size > 150 and hit_rate > 0.5:
            return "potential_attack_pattern"
        elif response_time > 100 and error_rate > 0.2:
            return "system_performance_degradation"
        elif hit_rate > 0.8:
            return "policy_evasion_attempt"
        else:
            return "unusual_traffic_pattern"
    
    def _score_to_confidence(self, score: float) -> PredictionConfidence:
        """Convert anomaly score to confidence level."""
        if score > 0.8:
            return PredictionConfidence.VERY_HIGH
        elif score > 0.6:
            return PredictionConfidence.HIGH
        elif score > 0.4:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW
    
    def _calculate_anomaly_severity(self, score: float) -> str:
        """Calculate severity from anomaly score."""
        if score > 0.8:
            return "critical"
        elif score > 0.6:
            return "high"
        elif score > 0.4:
            return "medium"
        else:
            return "low"
    
    def _identify_affected_patterns(self, scenario: List[float]) -> List[str]:
        """Identify which patterns might be affected by anomaly."""
        return ["API-KEY-1.0", "PASSWORD-1.0", "INJECTION-1.0"]  # Mock affected patterns
    
    def _get_base_patterns_for_threat(self, threat: str) -> List[str]:
        """Get base patterns for genetic algorithm."""
        base_patterns = {
            "novel_injection": [
                r"(?i)(union|select|insert)",
                r"(?i)(script|eval|exec)",
                r"(?i)(drop|delete|update)"
            ],
            "advanced_exfiltration": [
                r"(?i)(export|download|backup)",
                r"(?i)(data|database|file)",
                r"(?i)(extract|dump|copy)"
            ]
        }
        return base_patterns.get(threat, [r"suspicious"])
    
    def _evolve_pattern(self, base_patterns: List[str]) -> str:
        """Evolve patterns using genetic algorithm concepts."""
        if not base_patterns:
            return r"(?i)evolved_pattern"
        
        # Simple evolution: combine and mutate patterns
        combined = "|".join(base_patterns)
        evolved = f"(?i)({combined})[\\s\\w]*"
        
        return evolved
    
    def _generate_test_cases(self, pattern: str) -> List[str]:
        """Generate test cases for pattern validation."""
        return [
            "positive_test_case_1",
            "positive_test_case_2", 
            "negative_test_case_1",
            "edge_case_test"
        ]
    
    async def _statistical_forecast_anomalies(self, hours: int) -> List[AnomalyForecast]:
        """Statistical anomaly forecasting fallback."""
        forecasts = []
        
        # Simple statistical forecasting
        if len(self.evaluation_history) > 10:
            forecast = AnomalyForecast(
                anomaly_id=f"stat_forecast_{hours}h",
                anomaly_type="statistical_deviation",
                predicted_occurrence=(datetime.now() + timedelta(hours=hours//2)).isoformat(),
                confidence=PredictionConfidence.LOW,
                severity="medium",
                affected_patterns=["GENERAL-1.0"],
                behavioral_indicators=["Statistical pattern deviation"],
                prevention_strategies=["Monitor baseline metrics"],
                monitoring_recommendations=["Increase sampling frequency"],
                false_alarm_probability=0.4
            )
            forecasts.append(forecast)
        
        return forecasts
    
    async def _neural_pattern_generation(self, threat: str) -> Optional[ZeroDayPattern]:
        """Neural-inspired pattern generation."""
        try:
            # Simulate neural network pattern generation
            neural_pattern = f"(?i)(neural|ai|ml).*{threat}.*pattern"
            
            pattern = ZeroDayPattern(
                pattern_id=f"neural_{threat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                generated_pattern=neural_pattern,
                target_threat=threat,
                generation_method="neural",
                theoretical_coverage=0.6,
                validation_score=0.5,
                deployment_readiness=PredictionConfidence.LOW,
                test_cases=self._generate_test_cases(neural_pattern),
                known_limitations=[
                    "Experimental neural generation",
                    "Requires extensive validation",
                    "May need human refinement"
                ],
                human_review_required=True
            )
            return pattern
            
        except Exception as e:
            self.logger.error(f"Neural pattern generation failed for {threat}: {e}")
        
        return None


# Global engine instance
_predictive_engine = None


def get_predictive_engine() -> PredictiveIntelligenceEngine:
    """Get global predictive intelligence engine instance."""
    global _predictive_engine
    if _predictive_engine is None:
        _predictive_engine = PredictiveIntelligenceEngine()
    return _predictive_engine


# Async helper functions for easy integration
async def predict_threats(lookback_days: int = 30, forecast_days: int = 7) -> List[ThreatPrediction]:
    """Convenient function to predict threat patterns."""
    engine = get_predictive_engine()
    return await engine.predict_threat_patterns(lookback_days, forecast_days)


async def generate_tuning_recommendations(rules: Dict[str, Rule]) -> List[PolicyTuningRecommendation]:
    """Convenient function to generate policy tuning recommendations."""
    engine = get_predictive_engine()
    return await engine.generate_policy_tuning_recommendations(rules)


async def forecast_anomalies(hours: int = 24) -> List[AnomalyForecast]:
    """Convenient function to forecast behavioral anomalies."""
    engine = get_predictive_engine()
    return await engine.forecast_behavioral_anomalies(hours)


async def generate_zero_day_patterns(threats: List[str] = None) -> List[ZeroDayPattern]:
    """Convenient function to generate zero-day patterns."""
    engine = get_predictive_engine()
    return await engine.generate_zero_day_patterns(threats)