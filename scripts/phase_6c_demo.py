#!/usr/bin/env python3
"""
Phase 6C - Intelligent Policy Recommendations Demo
Demonstrates smart policy optimization and conflict detection capabilities
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def phase_6c_demo():
    """Run Phase 6C intelligent policy recommendations demonstration."""
    print("🎯 Jimini Phase 6C - Intelligent Policy Recommendations Demo")
    print("=" * 70)
    print()
    
    try:
        from app.intelligence.policy_recommendations import (
            PolicyRecommendationEngine,
            RecommendationType,
            RecommendationPriority,
            ConflictType,
            get_policy_recommendation_engine
        )
        from app.models import Rule
        
        # Check ML availability
        try:
            import sklearn
            ml_available = True
            print("✅ Machine Learning libraries available (scikit-learn)")
            print("  📊 Advanced pattern analysis enabled")
            print("  🤖 ML-powered redundancy detection enabled")
        except ImportError:
            ml_available = False
            print("⚠️  Machine Learning libraries not available")
            print("  📊 Heuristic analysis mode enabled")
        
        print()
        
        # Initialize policy recommendation engine
        print("🚀 Initializing Intelligent Policy Recommendation Engine...")
        engine = get_policy_recommendation_engine()
        print("  ✅ Policy optimization engine initialized")
        print("  🔍 Conflict detection: Enabled")
        print("  📈 Smart recommendations: Enabled") 
        print("  🎯 Coverage analysis: Enabled")
        print("  🛡️  Security enhancement: Enabled")
        print()
        
        # Create comprehensive test policy set
        print("📋 Creating Comprehensive Test Policy Set...")
        
        test_policies = {
            # Normal policies
            "API-KEY-1.0": Rule(
                id="API-KEY-1.0",
                title="Detect API Keys",
                severity="critical",
                pattern=r"(?i)api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",
                action="block",
                applies_to=["request", "response"],
                endpoints=["/api/*"]
            ),
            
            # Duplicate rule (same pattern, same action)
            "API-KEY-DUPLICATE-1.0": Rule(
                id="API-KEY-DUPLICATE-1.0", 
                title="Duplicate API Key Detection",
                severity="critical",
                pattern=r"(?i)api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",
                action="block",
                applies_to=["request", "response"],
                endpoints=["/api/*"]
            ),
            
            # Conflicting rule (same pattern, different action)
            "API-KEY-CONFLICT-1.0": Rule(
                id="API-KEY-CONFLICT-1.0",
                title="Conflicting API Key Rule",
                severity="medium", 
                pattern=r"(?i)api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",
                action="allow",  # Conflicts with block above
                applies_to=["request"],
                endpoints=["/api/public/*"]
            ),
            
            # Good policy
            "PASSWORD-1.0": Rule(
                id="PASSWORD-1.0",
                title="Detect Passwords",
                severity="high",
                pattern=r"(?i)password[\"']?\s*[:=]\s*[\"']?([^\s\"']{8,})",
                action="flag",
                applies_to=["request"],
                endpoints=["/auth/*", "/login/*"]
            ),
            
            # Overly broad pattern
            "BROAD-PATTERN-1.0": Rule(
                id="BROAD-PATTERN-1.0", 
                title="Too Broad Pattern",
                severity="low",
                pattern=r"test",  # Very short pattern
                action="flag",
                applies_to=["request"],
                endpoints=["/*"]
            ),
            
            # Specific rule that should come before general one
            "SPECIFIC-DATA-1.0": Rule(
                id="SPECIFIC-DATA-1.0",
                title="Specific Sensitive Data",
                severity="high",
                pattern=r"(?i)sensitive_personal_data_export",
                action="block",
                min_count=2,
                endpoints=["/api/sensitive/*"],
                applies_to=["request", "response"]
            ),
            
            # General rule that might overshadow specific one
            "GENERAL-DATA-1.0": Rule(
                id="GENERAL-DATA-1.0",
                title="General Data Pattern", 
                severity="medium",
                pattern=r"(?i)data",
                action="allow",
                applies_to=["request", "response"],
                endpoints=["/api/*"]
            )
        }
        
        print(f"  📝 Created {len(test_policies)} test policies")
        print("  🔸 Normal policies: 2")
        print("  🔸 Duplicate policies: 1") 
        print("  🔸 Conflicting policies: 1")
        print("  🔸 Broad patterns: 1")
        print("  🔸 Precedence issues: 2")
        print()
        
        # Demo 1: Policy Conflict Detection
        print("🔴 Demo 1: Advanced Policy Conflict Detection")
        print("=" * 50)
        
        conflicts = engine.analyze_policy_conflicts(test_policies)
        
        print(f"  🔍 Analysis Complete: {len(conflicts)} conflicts detected")
        print()
        
        # Group conflicts by type
        conflicts_by_type = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type.value
            if conflict_type not in conflicts_by_type:
                conflicts_by_type[conflict_type] = []
            conflicts_by_type[conflict_type].append(conflict)
        
        # Display conflicts by category
        conflict_icons = {
            "overlapping_patterns": "🔄",
            "contradictory_actions": "⚔️",
            "scope_conflicts": "🎯", 
            "redundant_rules": "📋",
            "precedence_issues": "⏫"
        }
        
        for conflict_type, conflict_list in conflicts_by_type.items():
            icon = conflict_icons.get(conflict_type, "⚠️")
            print(f"  {icon} {conflict_type.replace('_', ' ').title()}: {len(conflict_list)} detected")
            
            for conflict in conflict_list[:2]:  # Show first 2 conflicts per type
                print(f"    • {conflict.description}")
                print(f"      Rules: {', '.join(conflict.rule_ids)}")
                print(f"      Confidence: {conflict.confidence_score:.1%}")
                print(f"      Resolution: {conflict.resolution_suggestions[0]}")
                print()
        
        # Demo 2: Intelligent Recommendations Generation
        print("💡 Demo 2: Smart Policy Optimization Recommendations")
        print("=" * 50)
        
        # Mock performance data to trigger performance recommendations
        mock_performance_data = {
            "BROAD-PATTERN-1.0": {
                "false_positive_rate": 0.7,  # High false positive rate
                "effectiveness_score": 0.3,   # Low effectiveness
                "total_evaluations": 1000
            },
            "API-KEY-1.0": {
                "false_positive_rate": 0.05, # Good performance
                "effectiveness_score": 0.95,
                "total_evaluations": 500
            }
        }
        
        recommendations = engine.generate_policy_recommendations(
            test_policies,
            performance_data=mock_performance_data,
            compliance_requirements=["PCI DSS", "HIPAA", "GDPR"]
        )
        
        print(f"  🧠 Analysis Complete: {len(recommendations)} recommendations generated")
        print()
        
        # Group recommendations by priority and type
        recommendations_by_priority = {}
        recommendations_by_type = {}
        
        for rec in recommendations:
            # By priority
            priority = rec.priority.value
            if priority not in recommendations_by_priority:
                recommendations_by_priority[priority] = []
            recommendations_by_priority[priority].append(rec)
            
            # By type
            rec_type = rec.recommendation_type.value
            if rec_type not in recommendations_by_type:
                recommendations_by_type[rec_type] = []
            recommendations_by_type[rec_type].append(rec)
        
        # Display by priority
        priority_icons = {
            "critical": "🚨",
            "high": "🔴",
            "medium": "🟡",
            "low": "🔵",
            "informational": "ℹ️"
        }
        
        print("  📊 Recommendations by Priority:")
        for priority, rec_list in recommendations_by_priority.items():
            icon = priority_icons.get(priority, "•")
            print(f"    {icon} {priority.title()}: {len(rec_list)} recommendations")
        print()
        
        # Show top recommendations
        print("  🎯 Top Recommendations:")
        for i, rec in enumerate(recommendations[:4], 1):
            print(f"    {i}. [{rec.priority.value.upper()}] {rec.title}")
            print(f"       Type: {rec.recommendation_type.value.replace('_', ' ').title()}")
            print(f"       Impact: {rec.expected_impact}")
            print(f"       Confidence: {rec.confidence_score:.1%}")
            
            if rec.affected_rules:
                print(f"       Affects: {', '.join(rec.affected_rules)}")
            
            if rec.implementation_steps:
                print(f"       Next Step: {rec.implementation_steps[0]}")
            print()
        
        # Demo 3: Coverage Gap Analysis
        print("📈 Demo 3: Policy Coverage Gap Analysis")
        print("=" * 50)
        
        # Mock evaluation history to simulate coverage analysis
        mock_evaluation_history = [
            {"endpoint": "/api/users/sensitive", "action": "allow", "timestamp": "2025-10-01T10:00:00Z"},
            {"endpoint": "/api/payment/process", "action": "allow", "timestamp": "2025-10-01T11:00:00Z"},
            {"endpoint": "/health/records", "action": "allow", "timestamp": "2025-10-01T12:00:00Z"}
        ]
        
        coverage_gaps = engine.identify_coverage_gaps(
            test_policies,
            evaluation_history=mock_evaluation_history,
            compliance_frameworks=["PCI DSS", "HIPAA"]
        )
        
        print(f"  🔍 Coverage Analysis Complete: {len(coverage_gaps)} gaps identified")
        print()
        
        if coverage_gaps:
            print("  📋 Identified Coverage Gaps:")
            for gap in coverage_gaps:
                print(f"    • {gap.description}")
                print(f"      Type: {gap.gap_type}")
                print(f"      Risk Level: {gap.risk_level}")
                if gap.compliance_implications:
                    print(f"      Compliance Impact: {', '.join(gap.compliance_implications)}")
                print()
        else:
            print("  ✅ No significant coverage gaps detected in current analysis")
            print("  💡 Note: Coverage analysis uses historical evaluation data")
            print("      In production, this would analyze actual traffic patterns")
            print()
        
        # Demo 4: Comprehensive Optimization Report
        print("📊 Demo 4: Comprehensive Policy Optimization Report")
        print("=" * 50)
        
        optimization_report = engine.get_policy_optimization_report()
        
        summary = optimization_report["summary"]
        print("  📋 Executive Summary:")
        print(f"    Total Conflicts: {summary['total_conflicts_detected']}")
        print(f"    Total Recommendations: {summary['total_recommendations']}")
        print(f"    Coverage Gaps: {summary['total_coverage_gaps']}")
        print(f"    Critical Issues: {summary['critical_issues']}")
        print()
        
        print("  🎯 Recommended Next Actions:")
        for i, action in enumerate(optimization_report["next_actions"], 1):
            print(f"    {i}. {action}")
        print()
        
        # Demo 5: Integration Benefits
        print("🔗 Demo 5: Integration with Jimini Policy Engine")
        print("=" * 50)
        
        print("  ✅ Seamless Integration Benefits:")
        print("    🔸 Real-time conflict detection during rule updates")
        print("    🔸 Automated performance monitoring and optimization")
        print("    🔸 Proactive security gap identification")
        print("    🔸 ML-powered pattern analysis and recommendations")
        print("    🔸 Compliance framework alignment suggestions")
        print("    🔸 Dynamic policy evolution based on usage patterns")
        print()
        
        print("  🌐 Available API Endpoints:")
        endpoints = [
            ("POST", "/v1/policy/conflicts/analyze", "Detect policy conflicts"),
            ("POST", "/v1/policy/recommendations/generate", "Generate optimization recommendations"),
            ("POST", "/v1/policy/coverage/analyze", "Analyze coverage gaps"),
            ("POST", "/v1/policy/optimize/complete", "Complete optimization analysis"),
            ("GET", "/v1/policy/recommendations/status", "Get engine status"),
            ("GET", "/v1/policy/recommendations/types", "Get available recommendation types")
        ]
        
        for method, endpoint, description in endpoints:
            print(f"    {method:4} {endpoint:40} - {description}")
        print()
        
        # Demo 6: Real-world Impact
        print("🏆 Demo 6: Real-World Impact Assessment")
        print("=" * 50)
        
        # Calculate potential improvements
        total_rules = len(test_policies)
        conflicting_rules = len(set(
            rule_id for conflict in conflicts 
            for rule_id in conflict.rule_ids
        ))
        
        high_priority_recs = len([
            r for r in recommendations 
            if r.priority in [RecommendationPriority.CRITICAL, RecommendationPriority.HIGH]
        ])
        
        security_recs = len([
            r for r in recommendations 
            if r.recommendation_type == RecommendationType.SECURITY_ENHANCEMENT
        ])
        
        performance_recs = len([
            r for r in recommendations 
            if r.recommendation_type == RecommendationType.PERFORMANCE_TUNING
        ])
        
        print("  📈 Policy Health Assessment:")
        print(f"    Policy Conflict Rate: {(conflicting_rules/total_rules)*100:.1f}%")
        print(f"    High-Priority Issues: {high_priority_recs}")
        print(f"    Security Enhancements: {security_recs}")
        print(f"    Performance Optimizations: {performance_recs}")
        print()
        
        print("  💼 Business Impact:")
        print("    🔸 Reduced false positives through pattern optimization")
        print("    🔸 Enhanced security posture via gap detection")
        print("    🔸 Improved compliance through systematic analysis")
        print("    🔸 Decreased maintenance overhead via conflict resolution")
        print("    🔸 Proactive policy evolution with ML insights")
        print()
        
        print("🎉 Phase 6C - Intelligent Policy Recommendations Complete!")
        print()
        print("🚀 Key Capabilities Demonstrated:")
        print("  ✅ Multi-dimensional Conflict Detection")
        print("     - Pattern overlap analysis")
        print("     - Action contradiction detection")  
        print("     - Scope conflict identification")
        print("     - Redundancy elimination")
        print("     - Precedence optimization")
        print()
        print("  ✅ Smart Optimization Recommendations")
        print("     - Performance-driven suggestions")
        print("     - Security enhancement proposals")
        print("     - Compliance alignment guidance")
        print("     - Pattern refinement recommendations")
        print()
        print("  ✅ Advanced Coverage Analysis")
        print("     - Policy gap identification")
        print("     - Compliance requirement mapping")
        print("     - Usage pattern analysis")
        print("     - Risk-based prioritization")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Policy recommendation system not available: {e}")
        print()
        print("Installation Required:")
        print("  # Install base dependencies")
        print("  pip install pydantic fastapi")
        print("  # Optional ML enhancement")  
        print("  pip install scikit-learn numpy")
        return False
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎯 Jimini Intelligence Evolution - Phase 6C")
    print("Smart Policy Optimization & Conflict Detection")
    print("Cross-Regulation Analysis with ML-Powered Recommendations")
    print()
    
    success = phase_6c_demo()
    
    if success:
        print("=" * 70)
        print("🔮 Next Evolution: Phase 6D - Predictive Policy Intelligence")
        print("  • Predictive threat pattern analysis")
        print("  • Adaptive policy auto-tuning")
        print("  • Behavioral anomaly forecasting")
        print("  • Zero-day pattern generation")
    
    sys.exit(0 if success else 1)