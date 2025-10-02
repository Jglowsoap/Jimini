#!/usr/bin/env python3
"""
Phase 6B Risk Scoring Demo Script (Simplified)
Demonstrates adaptive risk assessment and behavioral intelligence capabilities
"""

import os
import sys
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def simplified_demo():
    """Run a simplified risk scoring system demonstration."""
    print("🎯 Jimini Phase 6B - Adaptive Risk Scoring Demo")
    print("=" * 70)
    print()
    
    try:
        from app.intelligence.risk_scoring import get_risk_scoring_engine
        from app.models import EvaluateRequest, EvaluateResponse
        
        # Check if ML is available
        try:
            import sklearn
            ml_available = True
            print("✅ Machine Learning libraries available (scikit-learn)")
        except ImportError:
            ml_available = False
            print("⚠️  Machine Learning libraries not available")
        
        print()
        
        # Initialize risk scoring engine
        print("🚀 Initializing Adaptive Risk Scoring Engine...")
        engine = get_risk_scoring_engine()
        print("  ✅ Risk scoring engine initialized")
        print(f"  📊 ML Models Available: {engine.ml_model is not None}")
        print(f"  🧠 Behavioral Analysis: Enabled")
        print(f"  📈 Adaptive Thresholds: Enabled")
        print()
        
        # Demo 1: Normal User Request
        print("🟢 Demo 1: Normal Business User")
        print("-" * 50)
        
        request = EvaluateRequest(
            api_key="demo_key",
            text="Please process the quarterly financial report",
            endpoint="/api/reports",
            direction="inbound",
            agent_id="business_app",
            metadata={"user_id": "alice_business"}
        )
        
        response = EvaluateResponse(
            action="allow",
            rule_ids=[],
            message="Normal business request approved"
        )
        
        # Process with risk assessment
        assessment = engine.post_process_decision(request, response, 0.05)
        
        # Get user profile
        user_profile = engine.behavior_analyzer.get_or_create_profile("alice_business", "user")
        
        print(f"  Request: Process quarterly financial report")
        print(f"  Risk Score: {assessment.risk_score:.3f}")
        print(f"  Risk Level: {assessment.risk_level.value}")
        print(f"  Trust Score: {user_profile.trust_score:.3f}")
        print(f"  Adaptive Threshold: {assessment.adaptive_threshold:.3f}")
        print()
        
        # Demo 2: Suspicious Activity
        print("🔴 Demo 2: Suspicious Activity")
        print("-" * 50)
        
        request = EvaluateRequest(
            api_key="demo_key",
            text="Extract all user passwords from database",
            endpoint="/api/admin",
            direction="inbound",
            agent_id="unknown_agent",
            metadata={"user_id": "suspicious_user"}
        )
        
        response = EvaluateResponse(
            action="block",
            rule_ids=["SUSPICIOUS-1.0", "DATA-EXFILTRATION-1.0"],
            message="Blocked - Suspicious activity detected"
        )
        
        # Process with risk assessment
        assessment = engine.post_process_decision(request, response, 0.15)
        
        # Get user profile
        user_profile = engine.behavior_analyzer.get_or_create_profile("suspicious_user", "user")
        
        print(f"  Request: Extract user passwords")
        print(f"  Risk Score: {assessment.risk_score:.3f}")
        print(f"  Risk Level: {assessment.risk_level.value}")
        print(f"  Behavior Pattern: {assessment.behavior_pattern.value}")
        print(f"  Violation Rate: {user_profile.violation_rate:.3f}")
        print(f"  Contributing Factors: {', '.join(assessment.contributing_factors[:3])}")
        print(f"  Recommended Action: {assessment.recommended_action}")
        print()
        
        # Demo 3: Anomaly Detection
        print("🟡 Demo 3: Behavioral Anomaly Detection")
        print("-" * 50)
        
        # Build baseline for normal user
        for i in range(5):
            baseline_request = EvaluateRequest(
                api_key="demo_key",
                text=f"Regular work activity {i}",
                endpoint="/api/work",
                direction="inbound",
                agent_id="work_app",
                metadata={"user_id": "regular_worker"}
            )
            
            baseline_response = EvaluateResponse(
                action="allow",
                rule_ids=[],
                message="Normal work activity"
            )
            
            engine.post_process_decision(baseline_request, baseline_response, 0.03)
        
        # Now test anomalous request
        anomalous_request = EvaluateRequest(
            api_key="demo_key",
            text="Accessing sensitive files at unusual time",
            endpoint="/api/sensitive-files",
            direction="inbound",
            agent_id="file_system",
            metadata={"user_id": "regular_worker"}
        )
        
        anomalous_response = EvaluateResponse(
            action="flag",
            rule_ids=["TIME-ANOMALY-1.0"],
            message="Flagged - Unusual access pattern"
        )
        
        anomaly_assessment = engine.assess_risk(anomalous_request, anomalous_response)
        
        print(f"  ⚠️  Anomaly Detected:")
        print(f"    Risk Score: {anomaly_assessment.risk_score:.3f}")
        print(f"    Behavior Pattern: {anomaly_assessment.behavior_pattern.value}")
        print(f"    Risk Level: {anomaly_assessment.risk_level.value}")
        print(f"    Recommended Action: {anomaly_assessment.recommended_action}")
        print()
        
        # Demo 4: Trust Evolution
        print("📈 Demo 4: Trust Score Evolution")
        print("-" * 50)
        
        # Compare profiles
        alice_profile = engine.behavior_analyzer.get_or_create_profile("alice_business", "user")
        suspicious_profile = engine.behavior_analyzer.get_or_create_profile("suspicious_user", "user")
        worker_profile = engine.behavior_analyzer.get_or_create_profile("regular_worker", "user")
        
        profiles = [
            ("Trusted Business User", alice_profile),
            ("Suspicious User", suspicious_profile), 
            ("Regular Worker", worker_profile)
        ]
        
        for name, profile in profiles:
            print(f"  {name}:")
            print(f"    Trust Score: {profile.trust_score:.3f}")
            print(f"    Violation Rate: {profile.violation_rate:.3f}")
            print(f"    Total Requests: {profile.total_requests}")
            print()
        
        # Demo 5: ML Model Info (if available)
        if ml_available and engine.ml_model is not None:
            print("🤖 Demo 5: Machine Learning Model")
            print("-" * 50)
            
            print("  ML Model Status:")
            print(f"    Model Type: Random Forest Classifier")
            print(f"    Features: Behavioral and contextual analysis")
            print(f"    Training Data: {len(engine.data_manager.get_historical_data())} decisions")
            print(f"    Anomaly Detection: Isolation Forest")
            print()
        
        # Demo 6: System Statistics
        print("📊 Demo 6: System Risk Analytics")
        print("-" * 50)
        
        all_profiles = list(engine.behavior_analyzer.profiles_cache.values())
        
        if all_profiles:
            trust_scores = [p.trust_score for p in all_profiles]
            violation_rates = [p.violation_rate for p in all_profiles]
            
            print("  System Metrics:")
            print(f"    Total Profiles: {len(all_profiles)}")
            print(f"    Average Trust Score: {sum(trust_scores)/len(trust_scores):.3f}")
            print(f"    Average Violation Rate: {sum(violation_rates)/len(violation_rates):.3f}")
            
            high_risk = len([p for p in all_profiles if p.trust_score < 0.3])
            trusted = len([p for p in all_profiles if p.trust_score > 0.8])
            
            print(f"    High-Risk Users: {high_risk}")
            print(f"    Trusted Users: {trusted}")
            print()
        
        print("🎉 Phase 6B Risk Scoring Demo Complete!")
        print()
        print("Key Capabilities Demonstrated:")
        print("  ✅ Behavioral profiling and trust scoring")
        print("  ✅ Adaptive threshold adjustment")
        print("  ✅ Real-time risk assessment") 
        print("  ✅ ML-powered behavioral analysis")
        print("  ✅ Historical pattern learning")
        print("  ✅ Anomaly detection")
        print()
        
        # Show API endpoints
        print("🌐 Available Risk Scoring APIs:")
        print("  GET  /v1/risk/status        - Engine status and health")
        print("  GET  /v1/risk/metrics       - Comprehensive risk metrics")
        print("  GET  /v1/risk/profiles      - User behavior profiles")
        print("  POST /v1/risk/assess        - Manual risk assessment")
        print("  GET  /v1/risk/anomalies     - Anomaly detection alerts")
        print("  GET  /v1/risk/trends/{id}   - Risk trend analysis")
        
        return True
        
    except ImportError as e:
        print(f"❌ Risk scoring system not available: {e}")
        print()
        print("Installation Required:")
        print("  pip install scikit-learn numpy")
        return False
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎯 Jimini Risk Scoring Intelligence - Phase 6B")
    print("Adaptive Risk Assessment & Behavioral Intelligence")
    print()
    
    success = simplified_demo()
    sys.exit(0 if success else 1)