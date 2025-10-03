"""
Phase 6B - Risk Scoring Tests
Comprehensive test suite for adaptive risk assessment and behavioral intelligence
"""

import pytest
import tempfile
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.intelligence.risk_scoring import (
    RiskScoringEngine, BehaviorAnalyzer, HistoricalDataManager,
    RiskFeatures, RiskAssessment, BehaviorProfile,
    RiskLevel, BehaviorPattern, get_risk_scoring_engine
)
from app.models import EvaluateRequest, EvaluateResponse


class TestRiskFeatures:
    """Test risk feature extraction and processing."""
    
    def test_risk_features_creation(self):
        """Test creating risk features."""
        features = RiskFeatures(
            text_length=100,
            endpoint_frequency=0.5,
            time_of_day=14,
            day_of_week=1,
            user_violation_rate=0.1,
            endpoint_violation_rate=0.05,
            recent_violations=2,
            sensitive_keywords=1,
            data_entropy=0.7,
            pattern_matches=0,
            request_volume_spike=False,
            off_hours_access=False,
            geographic_anomaly=False,
            current_load=0.3,
            error_rate=0.0
        )
        
        assert features.text_length == 100
        assert features.user_violation_rate == 0.1
        assert not features.off_hours_access
    
    def test_features_to_array(self):
        """Test converting features to numpy array."""
        features = RiskFeatures(
            text_length=100, endpoint_frequency=0.5, time_of_day=14, day_of_week=1,
            user_violation_rate=0.1, endpoint_violation_rate=0.05, recent_violations=2,
            sensitive_keywords=1, data_entropy=0.7, pattern_matches=0,
            request_volume_spike=False, off_hours_access=False, geographic_anomaly=False,
            current_load=0.3, error_rate=0.0
        )
        
        array = features.to_array()
        assert len(array) == 15  # All features
        assert array[0] == 100  # text_length
        assert array[10] == 0   # request_volume_spike (False -> 0)


class TestHistoricalDataManager:
    """Test historical data management and storage."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        manager = HistoricalDataManager(db_path)
        yield manager
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_database_initialization(self, temp_db):
        """Test database initialization creates required tables."""
        # Check that database file exists
        assert Path(temp_db.db_path).exists()
        
        # Check tables exist
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('policy_decisions', 'behavior_profiles', 'risk_assessments')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
        assert 'policy_decisions' in tables
        assert 'behavior_profiles' in tables
        assert 'risk_assessments' in tables
    
    def test_store_and_retrieve_decision(self, temp_db):
        """Test storing and retrieving policy decisions."""
        # Create sample request and response
        request = EvaluateRequest(
            text="Test sensitive content with password",
            agent_id="test_agent",
            endpoint="/api/test",
            direction="inbound"
        )
        request.user_id = "user123"
        
        response = EvaluateResponse(
            success=True,
            decision="flag",
            rule_ids=["SENSITIVE-1.0"],
            message="Flagged for review"
        )
        
        features = RiskFeatures(
            text_length=len(request.text), endpoint_frequency=0.5, time_of_day=14, day_of_week=1,
            user_violation_rate=0.0, endpoint_violation_rate=0.0, recent_violations=0,
            sensitive_keywords=1, data_entropy=0.5, pattern_matches=1,
            request_volume_spike=False, off_hours_access=False, geographic_anomaly=False,
            current_load=0.3, error_rate=0.0
        )
        
        # Store decision
        temp_db.store_decision(request, response, features, 0.6, 0.1)
        
        # Retrieve historical data
        historical = temp_db.get_historical_data(days=1)
        
        assert len(historical) == 1
        record = historical[0]
        assert record['decision'] == 'flag'
        assert record['user_id'] == 'user123'
        assert record['endpoint'] == '/api/test'
        assert record['risk_score'] == 0.6
    
    def test_behavior_profile_storage(self, temp_db):
        """Test behavior profile storage and retrieval."""
        profile = BehaviorProfile(
            identifier="user123",
            identifier_type="user",
            total_requests=10,
            violation_count=1,
            violation_rate=0.1,
            active_hours=[9, 10, 11, 14, 15, 16],
            active_days=[0, 1, 2, 3, 4],
            request_frequency=2.5,
            typical_text_length=150.0,
            common_endpoints=["/api/data", "/api/test"],
            sensitive_content_frequency=0.05,
            recent_anomalies=0,
            escalation_count=0,
            last_violation=None,
            trust_score=0.8,
            learning_rate=0.1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store profile
        temp_db.store_behavior_profile(profile)
        
        # Retrieve profile
        retrieved = temp_db.get_behavior_profile("user123", "user")
        
        assert retrieved is not None
        assert retrieved.identifier == "user123"
        assert retrieved.violation_rate == 0.1
        assert retrieved.trust_score == 0.8
        assert len(retrieved.active_hours) == 6


class TestBehaviorAnalyzer:
    """Test behavioral pattern analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create behavior analyzer for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        data_manager = HistoricalDataManager(db_path)
        analyzer = BehaviorAnalyzer(data_manager)
        
        yield analyzer
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_create_new_profile(self, analyzer):
        """Test creating new behavior profile."""
        profile = analyzer.get_or_create_profile("new_user", "user")
        
        assert profile.identifier == "new_user"
        assert profile.identifier_type == "user"
        assert profile.total_requests == 0
        assert profile.trust_score == 0.5  # Default neutral trust
    
    def test_update_profile_with_request(self, analyzer):
        """Test updating profile based on request/response."""
        request = EvaluateRequest(
            text="Normal business request",
            agent_id="test_agent",
            endpoint="/api/business",
            direction="inbound"
        )
        
        response = EvaluateResponse(
            success=True,
            decision="allow",
            rule_ids=[],
            message="Allowed"
        )
        
        # Update profile
        analyzer.update_profile("user123", "user", request, response)
        
        # Get updated profile
        profile = analyzer.get_or_create_profile("user123", "user")
        
        assert profile.total_requests == 1
        assert profile.violation_count == 0
        assert profile.violation_rate == 0.0
        assert profile.trust_score > 0.5  # Should increase for allowed request
    
    def test_update_profile_with_violation(self, analyzer):
        """Test updating profile with policy violation."""
        request = EvaluateRequest(
            text="Sensitive data with password123",
            agent_id="test_agent", 
            endpoint="/api/sensitive",
            direction="inbound"
        )
        
        response = EvaluateResponse(
            success=True,
            decision="block",
            rule_ids=["SENSITIVE-1.0"],
            message="Blocked"
        )
        
        # Update profile
        analyzer.update_profile("user456", "user", request, response)
        
        # Get updated profile
        profile = analyzer.get_or_create_profile("user456", "user")
        
        assert profile.total_requests == 1
        assert profile.violation_count == 1
        assert profile.violation_rate == 1.0
        assert profile.trust_score < 0.5  # Should decrease for blocked request
        assert profile.last_violation is not None
    
    def test_anomaly_detection_insufficient_data(self, analyzer):
        """Test anomaly detection with insufficient historical data."""
        request = EvaluateRequest(
            text="Test request",
            agent_id="test_agent",
            endpoint="/api/test", 
            direction="inbound"
        )
        
        # Should return no anomalies with insufficient data
        anomalies = analyzer.detect_anomalies("new_user", "user", request)
        assert anomalies == []
    
    def test_anomaly_detection_with_history(self, analyzer):
        """Test anomaly detection with sufficient historical data."""
        # Build up some history first
        profile = analyzer.get_or_create_profile("established_user", "user")
        profile.total_requests = 50
        profile.active_hours = [9, 10, 11, 14, 15, 16]  # Normal business hours
        profile.active_days = [0, 1, 2, 3, 4]  # Weekdays
        profile.common_endpoints = ["/api/normal"]
        profile.typical_text_length = 100.0
        
        analyzer.data_manager.store_behavior_profile(profile)
        
        # Test request at unusual time
        request = EvaluateRequest(
            text="Test request at odd hour",
            agent_id="test_agent",
            endpoint="/api/unusual",
            direction="inbound"
        )
        
        # Mock the current time to be 3 AM (unusual hour)
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2025, 10, 1, 3, 0, 0)  # 3 AM Tuesday
            anomalies = analyzer.detect_anomalies("established_user", "user", request)
        
        # Should detect time and endpoint anomalies
        assert "unusual_time_access" in anomalies
        assert "unusual_endpoint" in anomalies


class TestRiskScoringEngine:
    """Test the main risk scoring engine."""
    
    @pytest.fixture
    def engine(self):
        """Create risk scoring engine for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        data_manager = HistoricalDataManager(db_path)
        engine = RiskScoringEngine(data_manager)
        
        yield engine
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_feature_extraction(self, engine):
        """Test extracting risk features from request."""
        request = EvaluateRequest(
            text="This contains sensitive password information",
            agent_id="test_agent",
            endpoint="/api/sensitive",
            direction="inbound"
        )
        request.user_id = "user123"
        
        features = engine.extract_features(request)
        
        assert features.text_length == len(request.text)
        assert features.sensitive_keywords > 0  # Should detect 'password'
        assert 0.0 <= features.data_entropy <= 1.0
        assert features.time_of_day >= 0 and features.time_of_day <= 23
    
    def test_base_risk_calculation(self, engine):
        """Test base risk score calculation."""
        features = RiskFeatures(
            text_length=100, endpoint_frequency=0.5, time_of_day=14, day_of_week=1,
            user_violation_rate=0.2, endpoint_violation_rate=0.1, recent_violations=1,
            sensitive_keywords=2, data_entropy=0.9, pattern_matches=1,
            request_volume_spike=False, off_hours_access=True, geographic_anomaly=False,
            current_load=0.3, error_rate=0.0
        )
        
        response = EvaluateResponse(
            success=True,
            decision="flag",
            rule_ids=["SENSITIVE-1.0"],
            message="Flagged"
        )
        
        base_risk = engine._calculate_base_risk(features, response)
        
        assert 0.0 <= base_risk <= 1.0
        assert base_risk > 0.5  # Should be high risk due to flag decision and other factors
    
    def test_risk_level_determination(self, engine):
        """Test risk level classification."""
        assert engine._determine_risk_level(0.95) == RiskLevel.CRITICAL
        assert engine._determine_risk_level(0.75) == RiskLevel.VERY_HIGH
        assert engine._determine_risk_level(0.55) == RiskLevel.HIGH
        assert engine._determine_risk_level(0.35) == RiskLevel.MEDIUM
        assert engine._determine_risk_level(0.15) == RiskLevel.LOW
        assert engine._determine_risk_level(0.05) == RiskLevel.VERY_LOW
    
    def test_behavior_pattern_determination(self, engine):
        """Test behavior pattern classification."""
        # Normal behavior
        assert engine._determine_behavior_pattern(0.2, []) == BehaviorPattern.NORMAL
        
        # Suspicious behavior
        assert engine._determine_behavior_pattern(0.7, []) == BehaviorPattern.SUSPICIOUS
        
        # Anomalous behavior
        anomalies = ["unusual_time", "unusual_endpoint"]
        assert engine._determine_behavior_pattern(0.4, anomalies) == BehaviorPattern.ANOMALOUS
        
        # Malicious behavior
        many_anomalies = ["anom1", "anom2", "anom3"]
        assert engine._determine_behavior_pattern(0.8, many_anomalies) == BehaviorPattern.MALICIOUS
    
    def test_adaptive_threshold_calculation(self, engine):
        """Test adaptive threshold calculation."""
        request = EvaluateRequest(
            text="Test request",
            agent_id="test_agent",
            endpoint="/api/test",
            direction="inbound"
        )
        request.user_id = "trusted_user"
        
        features = RiskFeatures(
            text_length=100, endpoint_frequency=0.5, time_of_day=14, day_of_week=1,
            user_violation_rate=0.0, endpoint_violation_rate=0.0, recent_violations=0,
            sensitive_keywords=0, data_entropy=0.5, pattern_matches=0,
            request_volume_spike=False, off_hours_access=False, geographic_anomaly=False,
            current_load=0.3, error_rate=0.0
        )
        
        # Create trusted user profile
        user_profile = BehaviorProfile(
            identifier="trusted_user", identifier_type="user",
            total_requests=100, violation_count=0, violation_rate=0.0,
            active_hours=[], active_days=[], request_frequency=0.0,
            typical_text_length=0.0, common_endpoints=[], sensitive_content_frequency=0.0,
            recent_anomalies=0, escalation_count=0, last_violation=None,
            trust_score=0.9, learning_rate=0.1,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        engine.behavior_analyzer.data_manager.store_behavior_profile(user_profile)
        
        threshold = engine._calculate_adaptive_threshold(request, features, 0.3)
        
        # Should be lower (more permissive) for trusted user
        assert threshold < 0.5
    
    def test_complete_risk_assessment(self, engine):
        """Test complete risk assessment workflow."""
        request = EvaluateRequest(
            text="Sensitive business data with confidential information",
            agent_id="test_agent",
            endpoint="/api/confidential",
            direction="inbound"
        )
        request.user_id = "user123"
        
        response = EvaluateResponse(
            success=True,
            decision="flag",
            rule_ids=["CONFIDENTIAL-1.0"],
            message="Flagged for review"
        )
        
        assessment = engine.assess_risk(request, response)
        
        assert isinstance(assessment, RiskAssessment)
        assert 0.0 <= assessment.risk_score <= 1.0
        assert assessment.risk_level in RiskLevel
        assert assessment.behavior_pattern in BehaviorPattern
        assert 0.0 <= assessment.confidence <= 1.0
        assert isinstance(assessment.contributing_factors, list)
        assert isinstance(assessment.anomaly_indicators, list)
        assert assessment.recommended_action is not None
        assert 0.0 <= assessment.adaptive_threshold <= 1.0
    
    @patch('app.intelligence.risk_scoring.ML_AVAILABLE', False)
    def test_assessment_without_ml(self, engine):
        """Test risk assessment when ML is not available."""
        request = EvaluateRequest(
            text="Test request",
            agent_id="test_agent",
            endpoint="/api/test",
            direction="inbound"
        )
        
        response = EvaluateResponse(
            success=True,
            decision="allow",
            rule_ids=[],
            message="Allowed"
        )
        
        assessment = engine.assess_risk(request, response)
        
        # Should still work without ML
        assert isinstance(assessment, RiskAssessment)
        assert assessment.confidence <= 0.8  # Lower confidence without ML
    
    def test_post_process_decision(self, engine):
        """Test complete post-processing workflow."""
        request = EvaluateRequest(
            text="Business request with normal content",
            agent_id="test_agent",
            endpoint="/api/business",
            direction="inbound"
        )
        request.user_id = "user123"
        
        response = EvaluateResponse(
            success=True,
            decision="allow",
            rule_ids=[],
            message="Allowed"
        )
        
        assessment = engine.post_process_decision(request, response, 0.1)
        
        # Check assessment
        assert isinstance(assessment, RiskAssessment)
        
        # Check that behavior profiles were updated
        user_profile = engine.behavior_analyzer.get_or_create_profile("user123", "user")
        assert user_profile.total_requests >= 1
        
        endpoint_profile = engine.behavior_analyzer.get_or_create_profile("/api/business", "endpoint")
        assert endpoint_profile.total_requests >= 1


class TestIntegrationScenarios:
    """Integration tests for risk scoring scenarios."""
    
    def test_high_risk_user_scenario(self):
        """Test scenario with high-risk user behavior."""
        engine = get_risk_scoring_engine()
        
        # Simulate multiple violations from the same user
        for i in range(5):
            request = EvaluateRequest(
                text=f"Violation attempt {i} with sensitive data",
                agent_id="malicious_agent",
                endpoint="/api/sensitive",
                direction="inbound"
            )
            request.user_id = "suspicious_user"
            
            response = EvaluateResponse(
                success=True,
                decision="block" if i % 2 == 0 else "flag",
                rule_ids=["SENSITIVE-1.0"],
                message="Policy violation"
            )
            
            assessment = engine.post_process_decision(request, response, 0.1)
        
        # Final assessment should show high risk
        final_request = EvaluateRequest(
            text="Another attempt from the same user",
            agent_id="malicious_agent", 
            endpoint="/api/sensitive",
            direction="inbound"
        )
        final_request.user_id = "suspicious_user"
        
        final_response = EvaluateResponse(
            success=True,
            decision="allow",  # Even an allow should be high risk
            rule_ids=[],
            message="Allowed"
        )
        
        final_assessment = engine.assess_risk(final_request, final_response)
        
        # User should now have high violation rate and low trust
        user_profile = engine.behavior_analyzer.get_or_create_profile("suspicious_user", "user")
        assert user_profile.violation_rate > 0.5
        assert user_profile.trust_score < 0.5
        
        # Risk score should be elevated even for allowed content
        assert final_assessment.risk_score > 0.3
    
    def test_trusted_user_scenario(self):
        """Test scenario with trusted user behavior."""
        engine = get_risk_scoring_engine()
        
        # Simulate many clean requests from the same user
        for i in range(20):
            request = EvaluateRequest(
                text=f"Normal business request {i}",
                agent_id="business_agent",
                endpoint="/api/business",
                direction="inbound"
            )
            request.user_id = "trusted_user"
            
            response = EvaluateResponse(
                success=True,
                decision="allow",
                rule_ids=[],
                message="Allowed"
            )
            
            assessment = engine.post_process_decision(request, response, 0.05)
        
        # User should have high trust and low risk
        user_profile = engine.behavior_analyzer.get_or_create_profile("trusted_user", "user")
        assert user_profile.violation_rate == 0.0
        assert user_profile.trust_score > 0.7
        
        # Even a flagged request should have adjusted threshold
        flagged_request = EvaluateRequest(
            text="Business request with minor flag trigger",
            agent_id="business_agent",
            endpoint="/api/business", 
            direction="inbound"
        )
        flagged_request.user_id = "trusted_user"
        
        flagged_response = EvaluateResponse(
            success=True,
            decision="flag",
            rule_ids=["MINOR-1.0"],
            message="Minor flag"
        )
        
        assessment = engine.assess_risk(flagged_request, flagged_response)
        
        # Adaptive threshold should be lower (more permissive) for trusted user
        assert assessment.adaptive_threshold < 0.5


def test_global_risk_engine_singleton():
    """Test global risk engine singleton pattern."""
    engine1 = get_risk_scoring_engine()
    engine2 = get_risk_scoring_engine()
    
    # Should be the same instance
    assert engine1 is engine2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])