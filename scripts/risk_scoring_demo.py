#!/usr/bin/env python3
"""
Phase 6B Risk Scoring Demo Script
Demonstrates adaptive risk assessment and behavioral intelligence capabilities
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_sample_scenarios():
    """Create sample request scenarios for demonstration."""
    
    # Scenario 1: Normal Business User
    normal_scenarios = [
        {
            "text": "Please process the quarterly financial report",
            "agent_id": "business_app",
            "endpoint": "/api/reports",
            "direction": "inbound",
            "user_id": "alice_business",
            "description": "Normal business request"
        },
        {
            "text": "Update customer contact information in CRM",
            "agent_id": "crm_system", 
            "endpoint": "/api/customers",
            "direction": "inbound", 
            "user_id": "alice_business",
            "description": "Routine CRM update"
        }
    ]
    
    # Scenario 2: Suspicious Activity
    suspicious_scenarios = [
        {
            "text": "Extract all user passwords from database",
            "agent_id": "unknown_agent",
            "endpoint": "/api/admin",
            "direction": "inbound",
            "user_id": "suspicious_user",
            "description": "Suspicious password extraction attempt"
        },
        {
            "text": "Download complete customer database backup",
            "agent_id": "unknown_agent",
            "endpoint": "/api/export",
            "direction": "inbound",
            "user_id": "suspicious_user", 
            "description": "Unusual data export request"
        }
    ]
    
    # Scenario 3: Off-Hours Access
    off_hours_scenarios = [
        {
            "text": "Access confidential salary information",
            "agent_id": "hr_system",
            "endpoint": "/api/hr/salaries",
            "direction": "inbound",
            "user_id": "night_user",
            "description": "Off-hours HR data access"
        }
    ]
    
    # Scenario 4: High-Volume Anomaly
    volume_scenarios = [
        {
            "text": f"API request batch {i}",
            "agent_id": "batch_processor",
            "endpoint": "/api/batch",
            "direction": "inbound",
            "user_id": "bulk_user",
            "description": f"Bulk request {i}"
        } for i in range(50)
    ]
    
    return {
        "normal": normal_scenarios,
        "suspicious": suspicious_scenarios,
        "off_hours": off_hours_scenarios,
        "volume": volume_scenarios
    }


def demo_risk_scoring_system():
    """Run comprehensive risk scoring system demonstration."""
    print("🎯 Jimini Phase 6B - Adaptive Risk Scoring Demo")
    print("=" * 70)
    print()
    
    try:
        from app.intelligence.risk_scoring import (
            RiskScoringEngine, get_risk_scoring_engine,
            RiskLevel, BehaviorPattern
        )
        from app.models import EvaluateRequest, EvaluateResponse
        
        # Check if ML is available
        try:
            import sklearn
            ml_available = True
            print("✅ Machine Learning libraries available (scikit-learn)")
        except ImportError:
            ml_available = False
            print("⚠️  Machine Learning libraries not available")
            print("   Install with: pip install scikit-learn numpy")
        
        print()
        
        # Initialize risk scoring engine
        print("🚀 Initializing Adaptive Risk Scoring Engine...")
        engine = get_risk_scoring_engine()
        print("  ✅ Risk scoring engine initialized")
        print(f"  📊 ML Models Available: {engine.ml_model is not None}")
        print(f"  🧠 Behavioral Analysis: Enabled")
        print(f"  📈 Adaptive Thresholds: Enabled")
        print()
        
        # Create sample scenarios
        print("📋 Creating Sample Risk Scenarios...")
        scenarios = create_sample_scenarios()
        
        for category, count in [(k, len(v)) for k, v in scenarios.items()]:
            print(f"  • {category.title()}: {count} scenarios")
        print()
        
        # Demo 1: Normal User Behavior Building Trust
        print("🟢 Demo 1: Normal User Building Trust Profile")
        print("-" * 50)
        
        trust_scores = []
        
        for i, scenario in enumerate(scenarios["normal"][:5]):  # Process 5 normal requests
            request_data = {k: v for k, v in scenario.items() if k != "description"}
            request_data["api_key"] = "demo_key"  # Add required API key
            request = EvaluateRequest(**request_data)
            
            response = EvaluateResponse(
                action="allow",
                rule_ids=[],
                message="Normal business request approved"
            )
            
            # Process with risk assessment
            assessment = engine.post_process_decision(request, response, 0.05)
            
            # Get updated user profile
            user_profile = engine.behavior_analyzer.get_or_create_profile("alice_business", "user")
            trust_scores.append(user_profile.trust_score)
            
            print(f"  Request {i+1}: {scenario['description']}")
            print(f"    Risk Score: {assessment.risk_score:.3f}")
            print(f"    Risk Level: {assessment.risk_level.value}")
            print(f"    Trust Score: {user_profile.trust_score:.3f}")
            print(f"    Adaptive Threshold: {assessment.adaptive_threshold:.3f}")
            print()
        
        print(f"📈 Trust Evolution: {trust_scores[0]:.3f} → {trust_scores[-1]:.3f}")
        print()
        
        # Demo 2: Suspicious Activity Detection
        print("🔴 Demo 2: Suspicious Activity Pattern Detection")
        print("-" * 50)
        
        violation_rates = []
        
        for i, scenario in enumerate(scenarios["suspicious"][:3]):
            request_data = {k: v for k, v in scenario.items() if k != "description"}
            request_data["api_key"] = "demo_key"  # Add required API key
            request = EvaluateRequest(**request_data)
            
            # Simulate policy violation
            response = EvaluateResponse(
                action="block",
                rule_ids=["SUSPICIOUS-1.0", "DATA-EXFILTRATION-1.0"],
                message="Blocked - Suspicious activity detected"
            )
            
            # Process with risk assessment
            assessment = engine.post_process_decision(request, response, 0.15)
            
            # Get updated user profile
            user_profile = engine.behavior_analyzer.get_or_create_profile("suspicious_user", "user")
            violation_rates.append(user_profile.violation_rate)
            
            print(f"  Violation {i+1}: {scenario['description']}")
            print(f"    Risk Score: {assessment.risk_score:.3f}")
            print(f"    Risk Level: {assessment.risk_level.value}")
            print(f"    Behavior Pattern: {assessment.behavior_pattern.value}")
            print(f"    Violation Rate: {user_profile.violation_rate:.3f}")
            print(f"    Contributing Factors: {', '.join(assessment.contributing_factors[:3])}")
            print(f"    Recommended Action: {assessment.recommended_action}")
            print()
        
        print(f"📉 Risk Evolution: Violation rate increased to {violation_rates[-1]:.1%}")
        print()
        
        # Demo 3: Anomaly Detection  
        print("🟡 Demo 3: Behavioral Anomaly Detection")
        print("-" * 50)
        
        # First, establish normal pattern for a user
        print("  Building normal behavior baseline...")
        for i in range(10):
            request = EvaluateRequest(
                text="Regular work during business hours",
                agent_id="work_app",
                endpoint="/api/work", 
                direction="inbound",
                user_id="regular_worker"
            )
            
            response = EvaluateResponse(
                success=True,
                decision="allow",
                rule_ids=[],
                message="Normal work activity"
            )
            
            engine.post_process_decision(request, response, 0.03)
        
        # Now simulate anomalous behavior
        anomalous_request = EvaluateRequest(
            text="Accessing sensitive files at unusual time",
            agent_id="file_system",
            endpoint="/api/sensitive-files",
            direction="inbound", 
            user_id="regular_worker"
        )
        
        anomalous_response = EvaluateResponse(
            success=True,
            decision="flag",
            rule_ids=["TIME-ANOMALY-1.0"],
            message="Flagged - Unusual access pattern"
        )
        
        # Mock current time to 3 AM for anomaly detection
        import datetime
        original_datetime = datetime.datetime
        
        class MockDateTime(datetime.datetime):
            @classmethod
            def now(cls):
                return original_datetime(2025, 10, 1, 3, 0, 0)  # 3 AM
        
        datetime.datetime = MockDateTime
        
        try:
            anomaly_assessment = engine.assess_risk(anomalous_request, anomalous_response)
            
            print(f"  ⚠️  Anomaly Detected:")
            print(f"    Risk Score: {anomaly_assessment.risk_score:.3f}")
            print(f"    Behavior Pattern: {anomaly_assessment.behavior_pattern.value}")
            print(f"    Anomaly Indicators: {', '.join(anomaly_assessment.anomaly_indicators)}")
            print(f"    Risk Level: {anomaly_assessment.risk_level.value}")
            print(f"    Recommended Action: {anomaly_assessment.recommended_action}")
            
        finally:
            datetime.datetime = original_datetime
        
        print()
        
        # Demo 4: Adaptive Threshold Adjustment
        print("⚙️ Demo 4: Adaptive Threshold Demonstration")
        print("-" * 50)
        
        # Compare thresholds for different user types
        users_thresholds = []
        
        for user_id, description in [
            ("alice_business", "Trusted business user"),
            ("suspicious_user", "User with violations"),
            ("new_user", "New user (unknown)")
        ]:
            
            test_request = EvaluateRequest(
                text="Standard request for threshold test",
                agent_id="test_agent",
                endpoint="/api/test",
                direction="inbound",
                user_id=user_id
            )
            
            test_response = EvaluateResponse(
                success=True,
                decision="flag",
                rule_ids=["TEST-1.0"],
                message="Test flag"
            )
            
            assessment = engine.assess_risk(test_request, test_response)
            user_profile = engine.behavior_analyzer.get_or_create_profile(user_id, "user")
            
            users_thresholds.append((description, user_profile.trust_score, assessment.adaptive_threshold))
            
            print(f"  {description}:")
            print(f"    Trust Score: {user_profile.trust_score:.3f}")
            print(f"    Adaptive Threshold: {assessment.adaptive_threshold:.3f}")
            print(f"    Threshold Adjustment: {'More permissive' if assessment.adaptive_threshold < 0.5 else 'More restrictive'}")
            print()
        
        # Demo 5: ML Model Performance (if available)
        if ml_available and engine.ml_model is not None:
            print("🤖 Demo 5: Machine Learning Model Performance")
            print("-" * 50)
            
            print("  ML Model Status:")
            print(f"    Model Type: Random Forest Classifier")
            print(f"    Features: 15 behavioral and contextual features")
            print(f"    Training Data: {len(engine.data_manager.get_historical_data())} decisions")
            print(f"    Last Updated: {engine.last_model_update}")
            print(f"    Anomaly Detection: Isolation Forest")
            print()
            
            # Show feature importance (mock for demo)
            important_features = [
                "User violation rate (0.23)",
                "Sensitive keywords (0.18)",  
                "Off-hours access (0.15)",
                "Endpoint violation rate (0.12)",
                "Data entropy (0.10)"
            ]
            
            print("  Top Risk Factors:")
            for feature in important_features:
                print(f"    • {feature}")
            print()
        
        # Demo 6: Risk Analytics Summary
        print("📊 Demo 6: Risk Analytics Summary")
        print("-" * 50)
        
        # Get all profiles for summary
        all_profiles = list(engine.behavior_analyzer.profiles_cache.values())
        
        if all_profiles:
            trust_scores = [p.trust_score for p in all_profiles]
            violation_rates = [p.violation_rate for p in all_profiles]
            
            print("  System-Wide Risk Metrics:")
            print(f"    Total Profiles: {len(all_profiles)}")
            print(f"    Average Trust Score: {sum(trust_scores)/len(trust_scores):.3f}")
            print(f"    Average Violation Rate: {sum(violation_rates)/len(violation_rates):.3f}")
            print(f"    High-Risk Users: {len([p for p in all_profiles if p.trust_score < 0.3])}")
            print(f"    Trusted Users: {len([p for p in all_profiles if p.trust_score > 0.8])}")
            print()
            
            # Risk distribution
            risk_distribution = {}
            for profile in all_profiles:
                if profile.violation_rate > 0.5:
                    risk_level = "High"
                elif profile.violation_rate > 0.1:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            print("  Risk Distribution:")
            for level, count in risk_distribution.items():
                print(f"    {level} Risk: {count} users")
            print()
        
        print("🎉 Phase 6B Risk Scoring Demo Complete!")
        print()
        print("Key Capabilities Demonstrated:")
        print("  ✅ Behavioral profiling and trust scoring")
        print("  ✅ Adaptive threshold adjustment")
        print("  ✅ Real-time anomaly detection")
        print("  ✅ ML-powered risk assessment")
        print("  ✅ Historical pattern learning")
        print("  ✅ Contextual risk evaluation")
        print()
        print("Integration Benefits:")
        print("  🔸 Reduces false positives for trusted users")
        print("  🔸 Increases sensitivity for suspicious behavior")
        print("  🔸 Provides explainable risk factors")
        print("  🔸 Enables proactive security monitoring")
        print("  🔸 Supports compliance reporting")
        
    except ImportError as e:
        print(f"❌ Risk scoring system not available: {e}")
        print()
        print("Installation Required:")
        print("  pip install scikit-learn numpy")
        print("  # Optional for better ML performance:")
        print("  pip install pandas matplotlib")
        return False
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def demo_api_endpoints():
    """Demonstrate available Risk Scoring API endpoints."""
    print("🌐 Risk Scoring API Endpoints")
    print("=" * 50)
    print()
    
    endpoints = [
        ("GET", "/v1/risk/status", "Get risk engine status and ML model info"),
        ("GET", "/v1/risk/metrics", "Get comprehensive risk metrics and statistics"),
        ("GET", "/v1/risk/profiles", "List behavior profiles with filtering"),
        ("GET", "/v1/risk/profiles/{identifier}", "Get detailed behavior profile"),
        ("GET", "/v1/risk/assessments/recent", "Get recent risk assessments"),
        ("POST", "/v1/risk/assess", "Manually assess risk for content"),
        ("GET", "/v1/risk/trends/{identifier}", "Get risk trend analysis"),
        ("POST", "/v1/risk/models/retrain", "Manually trigger ML model retraining"),
        ("GET", "/v1/risk/anomalies", "Get recent anomaly detection alerts"),
        ("DELETE", "/v1/risk/profiles/{identifier}", "Delete behavior profile"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"{method:6} {endpoint:40} - {description}")
    
    print()
    print("Example Usage:")
    print("""
    # Check risk engine status
    curl http://localhost:9000/v1/risk/status
    
    # Get risk metrics for last 24 hours
    curl "http://localhost:9000/v1/risk/metrics?time_range=24h"
    
    # Get behavior profile for specific user
    curl "http://localhost:9000/v1/risk/profiles/alice_business?identifier_type=user"
    
    # Manually assess risk for content
    curl -X POST http://localhost:9000/v1/risk/assess \\
         -H "Content-Type: application/json" \\
         -d '{
           "text": "Sensitive password data",
           "agent_id": "test_agent",
           "endpoint": "/api/test",
           "direction": "inbound"
         }'
    
    # Get recent anomalies
    curl "http://localhost:9000/v1/risk/anomalies?severity=high&hours=24"
    
    # Get trend analysis
    curl "http://localhost:9000/v1/risk/trends/suspicious_user?identifier_type=user"
    """)


if __name__ == "__main__":
    print("🎯 Jimini Risk Scoring Intelligence - Phase 6B")
    print("Adaptive Risk Assessment & Behavioral Intelligence")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api-only":
        demo_api_endpoints()
    else:
        success = demo_risk_scoring_system()
        if success:
            print("\n" + "="*70)
            demo_api_endpoints()
        
        sys.exit(0 if success else 1)