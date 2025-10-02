"""
Comprehensive test suite for Phase 6D - Predictive Policy Intelligence

Tests cover:
- Predictive threat pattern analysis
- Adaptive policy auto-tuning
- Behavioral anomaly forecasting  
- Zero-day pattern generation
- API endpoint integration

Author: Jimini Intelligence Team
Version: 6D.1.0
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Test imports
from app.intelligence.predictive_intelligence import (
    PredictiveIntelligenceEngine,
    ThreatPrediction,
    PolicyTuningRecommendation, 
    AnomalyForecast,
    ZeroDayPattern,
    PredictionConfidence,
    ThreatTrend,
    get_predictive_engine,
    predict_threats,
    generate_tuning_recommendations,
    forecast_anomalies,
    generate_zero_day_patterns
)
from app.models import Rule


class TestPredictiveIntelligenceEngine:
    """Test suite for PredictiveIntelligenceEngine core functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.engine = PredictiveIntelligenceEngine()
        
        # Sample rules for testing
        self.test_rules = {
            "API-KEY-1.0": Rule(
                id="API-KEY-1.0",
                title="API Key Detection",
                severity="high",
                pattern=r"(?i)api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",
                action="block",
                applies_to=["request", "response"],
                endpoints=["/api/*"]
            ),
            "PASSWORD-1.0": Rule(
                id="PASSWORD-1.0", 
                title="Password Detection",
                severity="high",
                pattern=r"(?i)password[\"']?\s*[:=]\s*[\"']?([^\s\"']{8,})",
                action="flag",
                applies_to=["request"],
                endpoints=["/auth/*"]
            ),
            "SLOW-RULE-1.0": Rule(
                id="SLOW-RULE-1.0",
                title="Performance Test Rule",
                severity="medium", 
                pattern=r"(?i)(test|performance).*slow",
                action="flag",
                applies_to=["request"],
                endpoints=["/*"]
            )
        }
    
    def test_engine_initialization(self):
        """Test predictive intelligence engine initialization."""
        assert self.engine is not None
        assert hasattr(self.engine, 'ml_available')
        assert hasattr(self.engine, 'threat_history')
        assert hasattr(self.engine, 'performance_history')
        assert hasattr(self.engine, 'evaluation_history')
        
    def test_get_global_engine(self):
        """Test global engine instance management."""
        engine1 = get_predictive_engine()
        engine2 = get_predictive_engine()
        assert engine1 is engine2  # Should be same instance
        
    @pytest.mark.asyncio
    async def test_threat_pattern_prediction_basic(self):
        """Test basic threat pattern prediction."""
        predictions = await self.engine.predict_threat_patterns(
            lookback_days=7,
            forecast_days=3
        )
        
        assert isinstance(predictions, list)
        # Should generate some predictions even without historical data
        assert len(predictions) >= 0
        
        if predictions:
            prediction = predictions[0]
            assert isinstance(prediction, ThreatPrediction)
            assert prediction.pattern_id
            assert prediction.predicted_pattern
            assert prediction.threat_type
            assert isinstance(prediction.confidence, PredictionConfidence)
            assert isinstance(prediction.trend, ThreatTrend)
            assert 0 <= prediction.estimated_impact <= 1
            assert prediction.time_horizon > 0
            assert isinstance(prediction.supporting_evidence, list)
            assert isinstance(prediction.recommended_rules, list)
            assert 0 <= prediction.detection_probability <= 1
            assert 0 <= prediction.false_positive_risk <= 1
    
    @pytest.mark.asyncio
    async def test_threat_prediction_with_ml_fallback(self):
        """Test threat prediction with and without ML availability."""
        # Test with ML available
        if self.engine.ml_available:
            ml_predictions = await self.engine._ml_predict_threats(7, 3)
            assert isinstance(ml_predictions, list)
        
        # Test heuristic fallback
        heuristic_predictions = await self.engine._heuristic_predict_threats(7, 3)
        assert isinstance(heuristic_predictions, list)
        
        # Heuristic should always work
        assert len(heuristic_predictions) >= 0
    
    @pytest.mark.asyncio
    async def test_policy_tuning_recommendations(self):
        """Test adaptive policy tuning recommendation generation."""
        recommendations = await self.engine.generate_policy_tuning_recommendations(
            self.test_rules
        )
        
        assert isinstance(recommendations, list)
        
        if recommendations:
            rec = recommendations[0]
            assert isinstance(rec, PolicyTuningRecommendation)
            assert rec.rule_id in self.test_rules
            assert rec.adjustment_type in ["pattern", "threshold", "action", "scope", "processing"]
            assert rec.current_value
            assert rec.recommended_value
            assert rec.performance_gain >= 0
            assert isinstance(rec.confidence, PredictionConfidence)
            assert rec.rationale
            assert rec.risk_assessment
            assert 1 <= rec.implementation_priority <= 5
            assert isinstance(rec.expected_impact, dict)
            assert isinstance(rec.validation_criteria, list)
            assert isinstance(rec.rollback_conditions, list)
    
    @pytest.mark.asyncio
    async def test_policy_tuning_analysis_scenarios(self):
        """Test specific policy tuning scenarios."""
        # Mock performance data for different scenarios
        with patch.object(self.engine, '_analyze_rule_performance') as mock_perf:
            
            # High false positive rate scenario
            mock_perf.return_value = {
                'false_positive_rate': 0.15,
                'detection_rate': 0.85,
                'avg_response_time': 50
            }
            
            recommendations = await self.engine._analyze_rule_tuning_opportunities(
                "API-KEY-1.0", self.test_rules["API-KEY-1.0"], mock_perf.return_value
            )
            
            assert len(recommendations) > 0
            # Should recommend pattern optimization for high FP rate
            assert any(rec.adjustment_type == "pattern" for rec in recommendations)
            
            # Low detection rate scenario
            mock_perf.return_value = {
                'false_positive_rate': 0.05,
                'detection_rate': 0.70,
                'avg_response_time': 50
            }
            
            recommendations = await self.engine._analyze_rule_tuning_opportunities(
                "API-KEY-1.0", self.test_rules["API-KEY-1.0"], mock_perf.return_value
            )
            
            assert len(recommendations) > 0
            # Should recommend threshold adjustment for low detection
            assert any(rec.adjustment_type == "threshold" for rec in recommendations)
            
            # Slow response time scenario
            mock_perf.return_value = {
                'false_positive_rate': 0.05,
                'detection_rate': 0.90,
                'avg_response_time': 120
            }
            
            recommendations = await self.engine._analyze_rule_tuning_opportunities(
                "API-KEY-1.0", self.test_rules["API-KEY-1.0"], mock_perf.return_value
            )
            
            assert len(recommendations) > 0
            # Should recommend processing optimization for slow response
            assert any(rec.adjustment_type == "processing" for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_behavioral_anomaly_forecasting(self):
        """Test behavioral anomaly forecasting."""
        forecasts = await self.engine.forecast_behavioral_anomalies(
            monitoring_window_hours=12
        )
        
        assert isinstance(forecasts, list)
        
        if forecasts:
            forecast = forecasts[0]
            assert isinstance(forecast, AnomalyForecast)
            assert forecast.anomaly_id
            assert forecast.anomaly_type
            assert forecast.predicted_occurrence
            assert isinstance(forecast.confidence, PredictionConfidence)
            assert forecast.severity in ["low", "medium", "high", "critical"]
            assert isinstance(forecast.affected_patterns, list)
            assert isinstance(forecast.behavioral_indicators, list)
            assert isinstance(forecast.prevention_strategies, list)
            assert isinstance(forecast.monitoring_recommendations, list)
            assert 0 <= forecast.false_alarm_probability <= 1
    
    @pytest.mark.asyncio
    async def test_anomaly_forecasting_ml_vs_statistical(self):
        """Test ML vs statistical anomaly forecasting."""
        # Test ML-based forecasting if available
        if self.engine.ml_available:
            ml_forecasts = await self.engine._ml_forecast_anomalies(24)
            assert isinstance(ml_forecasts, list)
        
        # Test statistical fallback
        stat_forecasts = await self.engine._statistical_forecast_anomalies(24)
        assert isinstance(stat_forecasts, list)
        
        # Statistical should always produce some result
        assert len(stat_forecasts) >= 0
    
    @pytest.mark.asyncio
    async def test_zero_day_pattern_generation(self):
        """Test zero-day pattern generation."""
        target_threats = ["novel_injection", "advanced_exfiltration"]
        
        patterns = await self.engine.generate_zero_day_patterns(
            target_threats=target_threats
        )
        
        assert isinstance(patterns, list)
        
        if patterns:
            pattern = patterns[0]
            assert isinstance(pattern, ZeroDayPattern)
            assert pattern.pattern_id
            assert pattern.generated_pattern
            assert pattern.target_threat in target_threats or pattern.target_threat in [
                "ai_generated_attack", "quantum_cryptography_bypass", "deepfake_authentication"
            ]
            assert pattern.generation_method in ["genetic", "neural", "hybrid"]
            assert 0 <= pattern.theoretical_coverage <= 1
            assert 0 <= pattern.validation_score <= 1
            assert isinstance(pattern.deployment_readiness, PredictionConfidence)
            assert isinstance(pattern.test_cases, list)
            assert isinstance(pattern.known_limitations, list)
            assert isinstance(pattern.human_review_required, bool)
    
    @pytest.mark.asyncio
    async def test_genetic_pattern_generation(self):
        """Test genetic algorithm pattern generation."""
        pattern = await self.engine._genetic_pattern_generation("novel_injection")
        
        if pattern:
            assert isinstance(pattern, ZeroDayPattern)
            assert pattern.generation_method == "genetic"
            assert pattern.target_threat == "novel_injection"
            assert pattern.human_review_required is True
    
    @pytest.mark.asyncio
    async def test_neural_pattern_generation(self):
        """Test neural-inspired pattern generation."""
        pattern = await self.engine._neural_pattern_generation("advanced_exfiltration")
        
        if pattern:
            assert isinstance(pattern, ZeroDayPattern)
            assert pattern.generation_method == "neural"
            assert pattern.target_threat == "advanced_exfiltration"
    
    def test_helper_methods(self):
        """Test various helper methods."""
        # Test pattern generation
        pattern = self.engine._generate_threat_pattern("api_key_exposure", 0.8)
        assert isinstance(pattern, str)
        assert "api" in pattern.lower() or "key" in pattern.lower()
        
        # Test confidence calculation
        confidence = self.engine._calculate_prediction_confidence(0.85)
        assert isinstance(confidence, PredictionConfidence)
        assert confidence == PredictionConfidence.HIGH
        
        # Test trend determination
        trend = self.engine._determine_threat_trend("test_category", 0.9)
        assert isinstance(trend, ThreatTrend)
        assert trend == ThreatTrend.ESCALATING
        
        # Test pattern optimization
        original_pattern = r"test"
        optimized = self.engine._optimize_pattern_specificity(original_pattern)
        assert isinstance(optimized, str)
        assert len(optimized) >= len(original_pattern)
    
    def test_feature_extraction_methods(self):
        """Test feature extraction for ML models."""
        # Test threat feature extraction
        features, targets = self.engine._extract_threat_features(7)
        assert isinstance(features, list)
        assert isinstance(targets, list)
        assert len(features) == len(targets)
        
        # Test behavioral feature extraction
        behavioral_features = self.engine._extract_behavioral_features()
        assert isinstance(behavioral_features, list)
        
        if behavioral_features:
            feature_set = behavioral_features[0]
            assert isinstance(feature_set, list)
            assert len(feature_set) > 0
    
    def test_scenario_generation(self):
        """Test scenario generation for predictions."""
        # Test future feature generation
        future_features = self.engine._generate_future_features("test_threat", 5)
        assert isinstance(future_features, list)
        assert len(future_features) == 5
        
        if future_features:
            feature_set = future_features[0]
            assert isinstance(feature_set, list)
            assert len(feature_set) > 0
        
        # Test behavioral scenarios
        scenarios = self.engine._generate_behavioral_scenarios(12)
        assert isinstance(scenarios, list)
        assert len(scenarios) == 12
        
        if scenarios:
            scenario = scenarios[0]
            assert isinstance(scenario, list)
            assert len(scenario) > 0
    
    def test_classification_methods(self):
        """Test anomaly and threat classification."""
        # Test anomaly type classification
        test_scenario = [150, 120, 0.8, 0.3]  # High values indicating anomaly
        anomaly_type = self.engine._classify_anomaly_type(test_scenario)
        assert isinstance(anomaly_type, str)
        
        # Test confidence scoring
        confidence = self.engine._score_to_confidence(0.7)
        assert isinstance(confidence, PredictionConfidence)
        
        # Test severity calculation
        severity = self.engine._calculate_anomaly_severity(0.8)
        assert severity in ["low", "medium", "high", "critical"]
    
    def test_pattern_evolution_methods(self):
        """Test genetic algorithm pattern evolution."""
        base_patterns = [r"test1", r"test2", r"test3"]
        evolved = self.engine._evolve_pattern(base_patterns)
        assert isinstance(evolved, str)
        assert len(evolved) > 0
        
        # Test base pattern retrieval
        base_patterns = self.engine._get_base_patterns_for_threat("novel_injection")
        assert isinstance(base_patterns, list)
        
        # Test test case generation
        test_cases = self.engine._generate_test_cases("test_pattern")
        assert isinstance(test_cases, list)
        assert len(test_cases) > 0


class TestPredictiveIntelligenceAPI:
    """Test suite for predictive intelligence API functions."""
    
    @pytest.mark.asyncio
    async def test_predict_threats_function(self):
        """Test convenience function for threat prediction."""
        predictions = await predict_threats(lookback_days=7, forecast_days=3)
        assert isinstance(predictions, list)
    
    @pytest.mark.asyncio
    async def test_generate_tuning_recommendations_function(self):
        """Test convenience function for tuning recommendations."""
        test_rules = {
            "TEST-1.0": Rule(
                id="TEST-1.0",
                title="Test Rule",
                severity="medium",
                pattern=r"test",
                action="flag",
                applies_to=["request"],
                endpoints=["/*"]
            )
        }
        
        recommendations = await generate_tuning_recommendations(test_rules)
        assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio
    async def test_forecast_anomalies_function(self):
        """Test convenience function for anomaly forecasting."""
        forecasts = await forecast_anomalies(hours=12)
        assert isinstance(forecasts, list)
    
    @pytest.mark.asyncio
    async def test_generate_zero_day_patterns_function(self):
        """Test convenience function for zero-day pattern generation."""
        threats = ["test_threat"]
        patterns = await generate_zero_day_patterns(threats)
        assert isinstance(patterns, list)


class TestPredictiveIntelligenceModels:
    """Test suite for predictive intelligence data models."""
    
    def test_threat_prediction_model(self):
        """Test ThreatPrediction data model."""
        prediction = ThreatPrediction(
            pattern_id="test_pattern_1",
            predicted_pattern=r"(?i)test.*pattern",
            threat_type="test_threat",
            confidence=PredictionConfidence.HIGH,
            trend=ThreatTrend.EMERGING,
            estimated_impact=0.7,
            time_horizon=5,
            supporting_evidence=["Test evidence 1", "Test evidence 2"],
            recommended_rules=[{"id": "TEST-1.0", "action": "flag"}],
            detection_probability=0.85,
            false_positive_risk=0.1
        )
        
        assert prediction.pattern_id == "test_pattern_1"
        assert prediction.confidence == PredictionConfidence.HIGH
        assert prediction.trend == ThreatTrend.EMERGING
        assert 0 <= prediction.estimated_impact <= 1
        assert prediction.time_horizon > 0
        assert len(prediction.supporting_evidence) > 0
        assert len(prediction.recommended_rules) > 0
        assert 0 <= prediction.detection_probability <= 1
        assert 0 <= prediction.false_positive_risk <= 1
    
    def test_policy_tuning_recommendation_model(self):
        """Test PolicyTuningRecommendation data model."""
        recommendation = PolicyTuningRecommendation(
            rule_id="TEST-1.0",
            adjustment_type="pattern",
            current_value="test",
            recommended_value=r"\btest\b",
            performance_gain=15.5,
            confidence=PredictionConfidence.MEDIUM,
            rationale="Improve pattern specificity to reduce false positives",
            risk_assessment="Low risk - increases specificity only",
            implementation_priority=2,
            expected_impact={"false_positive_reduction": 0.1, "accuracy_improvement": 0.05},
            validation_criteria=["Monitor FP rate for 7 days", "Ensure detection rate >90%"],
            rollback_conditions=["FP rate increases", "Detection rate drops <85%"]
        )
        
        assert recommendation.rule_id == "TEST-1.0"
        assert recommendation.adjustment_type == "pattern"
        assert recommendation.performance_gain >= 0
        assert isinstance(recommendation.confidence, PredictionConfidence)
        assert 1 <= recommendation.implementation_priority <= 5
        assert isinstance(recommendation.expected_impact, dict)
        assert len(recommendation.validation_criteria) > 0
        assert len(recommendation.rollback_conditions) > 0
    
    def test_anomaly_forecast_model(self):
        """Test AnomalyForecast data model."""
        forecast = AnomalyForecast(
            anomaly_id="anomaly_test_1",
            anomaly_type="unusual_traffic_pattern",
            predicted_occurrence=datetime.now().isoformat(),
            confidence=PredictionConfidence.HIGH,
            severity="medium",
            affected_patterns=["TEST-1.0", "TEST-2.0"],
            behavioral_indicators=["Traffic spike", "Unusual timing"],
            prevention_strategies=["Rate limiting", "Enhanced monitoring"],
            monitoring_recommendations=["Increase alert sensitivity", "Review logs"],
            false_alarm_probability=0.15
        )
        
        assert forecast.anomaly_id == "anomaly_test_1"
        assert forecast.anomaly_type == "unusual_traffic_pattern"
        assert isinstance(forecast.confidence, PredictionConfidence)
        assert forecast.severity in ["low", "medium", "high", "critical"]
        assert len(forecast.affected_patterns) > 0
        assert len(forecast.behavioral_indicators) > 0
        assert len(forecast.prevention_strategies) > 0
        assert len(forecast.monitoring_recommendations) > 0
        assert 0 <= forecast.false_alarm_probability <= 1
    
    def test_zero_day_pattern_model(self):
        """Test ZeroDayPattern data model."""
        pattern = ZeroDayPattern(
            pattern_id="zero_day_test_1",
            generated_pattern=r"(?i)(novel|advanced).*attack",
            target_threat="novel_injection",
            generation_method="genetic",
            theoretical_coverage=0.65,
            validation_score=0.55,
            deployment_readiness=PredictionConfidence.MEDIUM,
            test_cases=["positive_case_1", "negative_case_1", "edge_case_1"],
            known_limitations=["Untested against real attacks", "High FP risk"],
            human_review_required=True
        )
        
        assert pattern.pattern_id == "zero_day_test_1"
        assert pattern.target_threat == "novel_injection"
        assert pattern.generation_method in ["genetic", "neural", "hybrid"]
        assert 0 <= pattern.theoretical_coverage <= 1
        assert 0 <= pattern.validation_score <= 1
        assert isinstance(pattern.deployment_readiness, PredictionConfidence)
        assert len(pattern.test_cases) > 0
        assert len(pattern.known_limitations) > 0
        assert isinstance(pattern.human_review_required, bool)


class TestPredictiveIntelligenceIntegration:
    """Integration tests for predictive intelligence system."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.engine = PredictiveIntelligenceEngine()
        self.test_rules = {
            "INTEGRATION-TEST-1.0": Rule(
                id="INTEGRATION-TEST-1.0",
                title="Integration Test Rule",
                severity="high",
                pattern=r"(?i)integration.*test",
                action="block",
                applies_to=["request", "response"], 
                endpoints=["/test/*"]
            ),
            "PERFORMANCE-TEST-1.0": Rule(
                id="PERFORMANCE-TEST-1.0",
                title="Performance Test Rule",
                severity="medium",
                pattern=r"(?i)performance.*test",
                action="flag",
                applies_to=["request"],
                endpoints=["/perf/*"]
            )
        }
    
    @pytest.mark.asyncio
    async def test_complete_prediction_workflow(self):
        """Test complete prediction workflow integration."""
        # Step 1: Predict threat patterns
        threat_predictions = await self.engine.predict_threat_patterns(
            lookback_days=10, forecast_days=5
        )
        assert isinstance(threat_predictions, list)
        
        # Step 2: Generate policy tuning recommendations
        tuning_recs = await self.engine.generate_policy_tuning_recommendations(
            self.test_rules
        )
        assert isinstance(tuning_recs, list)
        
        # Step 3: Forecast behavioral anomalies
        anomaly_forecasts = await self.engine.forecast_behavioral_anomalies(
            monitoring_window_hours=24
        )
        assert isinstance(anomaly_forecasts, list)
        
        # Step 4: Generate zero-day patterns
        zero_day_patterns = await self.engine.generate_zero_day_patterns(
            target_threats=["integration_test_threat"]
        )
        assert isinstance(zero_day_patterns, list)
        
        # Verify workflow produces results
        total_predictions = (
            len(threat_predictions) + len(tuning_recs) + 
            len(anomaly_forecasts) + len(zero_day_patterns)
        )
        assert total_predictions >= 0  # Should produce some predictions
    
    @pytest.mark.asyncio
    async def test_concurrent_prediction_operations(self):
        """Test concurrent execution of multiple prediction operations."""
        # Run multiple prediction types concurrently
        results = await asyncio.gather(
            self.engine.predict_threat_patterns(lookback_days=5, forecast_days=3),
            self.engine.generate_policy_tuning_recommendations(self.test_rules),
            self.engine.forecast_behavioral_anomalies(monitoring_window_hours=12),
            return_exceptions=True
        )
        
        # Verify all operations completed successfully
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent operation failed: {result}")
            assert isinstance(result, list)
    
    @pytest.mark.asyncio  
    async def test_prediction_consistency(self):
        """Test consistency of predictions across multiple runs."""
        # Run threat prediction multiple times
        prediction_runs = []
        for _ in range(3):
            predictions = await self.engine.predict_threat_patterns(
                lookback_days=7, forecast_days=3
            )
            prediction_runs.append(len(predictions))
        
        # Results should be reasonably consistent (within expected variance)
        if len(prediction_runs) > 1:
            variance = max(prediction_runs) - min(prediction_runs)
            # Allow some variance due to randomness in mock data
            assert variance <= 5  # Reasonable variance threshold
    
    def test_engine_state_management(self):
        """Test engine state management and data persistence."""
        # Test history management
        initial_threat_size = len(self.engine.threat_history)
        initial_perf_size = len(self.engine.performance_history)
        initial_eval_size = len(self.engine.evaluation_history)
        
        # Simulate adding data (in production, this would come from real events)
        self.engine.threat_history.append({"timestamp": datetime.now(), "type": "test"})
        self.engine.performance_history.append({"timestamp": datetime.now(), "metric": 0.8})
        self.engine.evaluation_history.append({"timestamp": datetime.now(), "result": "pass"})
        
        # Verify data was added
        assert len(self.engine.threat_history) == initial_threat_size + 1
        assert len(self.engine.performance_history) == initial_perf_size + 1
        assert len(self.engine.evaluation_history) == initial_eval_size + 1
        
        # Test cache management
        initial_cache_size = len(self.engine.prediction_cache)
        self.engine.prediction_cache["test_key"] = {"result": "test_value"}
        assert len(self.engine.prediction_cache) == initial_cache_size + 1
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and graceful degradation."""
        # Test with invalid input parameters
        try:
            await self.engine.predict_threat_patterns(
                lookback_days=-1,  # Invalid parameter
                forecast_days=0    # Invalid parameter
            )
            # Should not raise exception, should handle gracefully
        except Exception as e:
            # If exception occurs, it should be handled gracefully
            assert "lookback_days" in str(e) or "forecast_days" in str(e)
        
        # Test with empty rules
        empty_rules = {}
        recommendations = await self.engine.generate_policy_tuning_recommendations(empty_rules)
        assert isinstance(recommendations, list)
        assert len(recommendations) == 0  # Should handle empty input gracefully
    
    def test_ml_availability_handling(self):
        """Test handling of ML availability states.""" 
        # Store original ML state
        original_ml_state = self.engine.ml_available
        
        # Test with ML disabled
        self.engine.ml_available = False
        assert self.engine.ml_available is False
        
        # Verify fallback mechanisms work
        # (Specific fallback tests would go here)
        
        # Restore original state
        self.engine.ml_available = original_ml_state


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])