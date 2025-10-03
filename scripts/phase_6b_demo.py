#!/usr/bin/env python3
"""
Phase 6B Risk Scoring Demo Script (Minimal Working Version)
Demonstrates core risk assessment capabilities without full ML integration
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def minimal_demo():
    """Run a minimal risk scoring demonstration."""
    print("🎯 Jimini Phase 6B - Risk Scoring Intelligence Demo")
    print("=" * 70)
    print()
    
    # Simple risk assessment logic for demo
    class SimpleRiskAssessment:
        def __init__(self):
            self.user_profiles = {}
            
        def assess_risk(self, request_data, response_action):
            """Simple risk assessment based on action and content."""
            user_id = request_data.get("user_id", "unknown")
            text = request_data.get("text", "")
            
            # Initialize user if new
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {
                    "trust_score": 0.7,
                    "total_requests": 0,
                    "violations": 0,
                    "violation_rate": 0.0
                }
            
            profile = self.user_profiles[user_id]
            profile["total_requests"] += 1
            
            # Calculate base risk score
            risk_score = 0.0
            
            if response_action == "block":
                risk_score += 0.8
                profile["violations"] += 1
                profile["trust_score"] = max(0.0, profile["trust_score"] - 0.05)
            elif response_action == "flag":
                risk_score += 0.4
                profile["violations"] += 1
                profile["trust_score"] = max(0.0, profile["trust_score"] - 0.02)
            elif response_action == "allow":
                risk_score += 0.05
                profile["trust_score"] = min(1.0, profile["trust_score"] + 0.01)
            
            # Add content-based risk
            suspicious_terms = ["password", "database", "extract", "download", "admin", "root"]
            for term in suspicious_terms:
                if term.lower() in text.lower():
                    risk_score += 0.1
            
            # Add historical behavior risk
            profile["violation_rate"] = profile["violations"] / profile["total_requests"]
            risk_score += profile["violation_rate"] * 0.3
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = "critical"
            elif risk_score >= 0.6:
                risk_level = "high"
            elif risk_score >= 0.4:
                risk_level = "medium"
            elif risk_score >= 0.2:
                risk_level = "low"
            else:
                risk_level = "very_low"
            
            # Adaptive threshold based on trust
            adaptive_threshold = 0.5 - (profile["trust_score"] - 0.5) * 0.2
            adaptive_threshold = max(0.1, min(0.9, adaptive_threshold))
            
            return {
                "risk_score": round(risk_score, 3),
                "risk_level": risk_level,
                "trust_score": round(profile["trust_score"], 3),
                "violation_rate": round(profile["violation_rate"], 3),
                "adaptive_threshold": round(adaptive_threshold, 3),
                "total_requests": profile["total_requests"],
                "behavior_pattern": "suspicious" if risk_score > 0.5 else "normal"
            }
    
    # Initialize risk assessor
    assessor = SimpleRiskAssessment()
    
    print("🚀 Initializing Risk Scoring Engine...")
    print("  ✅ Core risk assessment engine initialized")
    print("  📊 Behavioral profiling: Enabled")
    print("  📈 Adaptive thresholds: Enabled")
    print("  🤖 ML Models: Demonstration mode (simplified)")
    print()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Normal Business Request",
            "user_id": "alice_business",
            "text": "Please process the quarterly financial report",
            "action": "allow",
            "description": "Routine business operation",
            "emoji": "🟢"
        },
        {
            "name": "Suspicious Activity",
            "user_id": "suspicious_user", 
            "text": "Extract all user passwords from database",
            "action": "block",
            "description": "Potential security threat",
            "emoji": "🔴"
        },
        {
            "name": "Flagged Content",
            "user_id": "alice_business",
            "text": "Download customer database for backup",
            "action": "flag",
            "description": "Legitimate but sensitive operation",
            "emoji": "🟡"
        },
        {
            "name": "Another Normal Request",
            "user_id": "alice_business",
            "text": "Update customer contact information",
            "action": "allow",
            "description": "Building trust through normal behavior",
            "emoji": "🟢"
        },
        {
            "name": "Repeated Violation",
            "user_id": "suspicious_user",
            "text": "Access admin panel with root privileges",
            "action": "block", 
            "description": "Pattern of violations detected",
            "emoji": "🔴"
        }
    ]
    
    print("📋 Risk Assessment Scenarios")
    print("=" * 50)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{scenario['emoji']} Scenario {i}: {scenario['name']}")
        print(f"   User: {scenario['user_id']}")
        print(f"   Request: {scenario['text'][:50]}{'...' if len(scenario['text']) > 50 else ''}")
        print(f"   Action: {scenario['action']}")
        
        # Perform risk assessment
        assessment = assessor.assess_risk(
            {"user_id": scenario["user_id"], "text": scenario["text"]},
            scenario["action"]
        )
        
        print(f"   Risk Score: {assessment['risk_score']}")
        print(f"   Risk Level: {assessment['risk_level']}")
        print(f"   Trust Score: {assessment['trust_score']}")
        print(f"   Violation Rate: {assessment['violation_rate']:.1%}")
        print(f"   Adaptive Threshold: {assessment['adaptive_threshold']}")
        print(f"   Behavior Pattern: {assessment['behavior_pattern']}")
        print()
    
    # User profile summary
    print("👥 User Profile Summary")
    print("=" * 50)
    
    for user_id, profile in assessor.user_profiles.items():
        trust_emoji = "✅" if profile["trust_score"] > 0.7 else "⚠️" if profile["trust_score"] > 0.3 else "❌"
        
        print(f"{trust_emoji} User: {user_id}")
        print(f"   Trust Score: {profile['trust_score']:.3f}")
        print(f"   Total Requests: {profile['total_requests']}")
        print(f"   Violations: {profile['violations']}")
        print(f"   Violation Rate: {profile['violation_rate']:.1%}")
        
        # Risk classification
        if profile["violation_rate"] > 0.5:
            risk_class = "High Risk"
        elif profile["violation_rate"] > 0.1:
            risk_class = "Medium Risk"
        else:
            risk_class = "Low Risk"
        
        print(f"   Risk Classification: {risk_class}")
        print()
    
    # System metrics
    print("📊 System Risk Analytics")
    print("=" * 50)
    
    total_users = len(assessor.user_profiles)
    total_requests = sum(p["total_requests"] for p in assessor.user_profiles.values())
    total_violations = sum(p["violations"] for p in assessor.user_profiles.values())
    avg_trust = sum(p["trust_score"] for p in assessor.user_profiles.values()) / total_users
    
    high_risk_users = len([p for p in assessor.user_profiles.values() if p["violation_rate"] > 0.5])
    trusted_users = len([p for p in assessor.user_profiles.values() if p["trust_score"] > 0.7])
    
    print(f"  Total Users Profiled: {total_users}")
    print(f"  Total Requests Processed: {total_requests}")
    print(f"  Total Policy Violations: {total_violations}")
    print(f"  System Violation Rate: {(total_violations/total_requests)*100:.1f}%")
    print(f"  Average Trust Score: {avg_trust:.3f}")
    print(f"  High-Risk Users: {high_risk_users}")
    print(f"  Trusted Users: {trusted_users}")
    print()
    
    # Key capabilities
    print("🎉 Phase 6B Core Capabilities Demonstrated")
    print("=" * 50)
    print("  ✅ Behavioral Risk Profiling")
    print("     - User trust score tracking")
    print("     - Violation rate monitoring")
    print("     - Pattern recognition")
    print()
    print("  ✅ Adaptive Risk Assessment")  
    print("     - Content-based analysis")
    print("     - Historical behavior weighting")
    print("     - Dynamic threshold adjustment")
    print()
    print("  ✅ Real-time Intelligence")
    print("     - Immediate risk scoring")
    print("     - Trust score evolution")
    print("     - Behavioral classification")
    print()
    
    # Next steps info
    print("🚀 Production Implementation")
    print("=" * 50)
    print("  For full Phase 6B deployment:")
    print("  1. Install ML dependencies: pip install scikit-learn numpy")
    print("  2. Enable ML models for advanced pattern recognition")  
    print("  3. Configure SQLite persistence for behavioral profiles")
    print("  4. Deploy risk scoring API endpoints")
    print("  5. Integrate with policy evaluation pipeline")
    print()
    print("  API Endpoints (when fully deployed):")
    print("    GET  /v1/risk/status       - Engine status")
    print("    GET  /v1/risk/metrics      - Risk analytics")
    print("    GET  /v1/risk/profiles     - User profiles")
    print("    POST /v1/risk/assess       - Manual assessment")
    print("    GET  /v1/risk/anomalies    - Anomaly alerts")
    
    return True


if __name__ == "__main__":
    print("🎯 Jimini Risk Scoring Intelligence - Phase 6B")
    print("Adaptive Risk Assessment & Behavioral Intelligence")
    print("Demonstration Mode - Core Capabilities Preview")
    print()
    
    success = minimal_demo()
    sys.exit(0 if success else 1)