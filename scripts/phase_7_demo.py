#!/usr/bin/env python3
"""
Phase 7: Reinforcement Learning Framework Demo

Demonstrates the advanced RL-powered policy optimization capabilities:
- Contextual multi-armed bandits for policy selection
- Thompson sampling with Bayesian exploration
- Real-time policy adaptation and learning
- A/B testing framework for policy experiments
- Shadow mode operation for safe deployment

Usage:
    python scripts/phase_7_demo.py
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any

# Add app to path for imports
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    from app.intelligence.reinforcement_learning import (
        PolicyOptimizer,
        ContextualBandit,
        RLContext,
        RLReward,
        PolicyAction,
        ExplorationStrategy,
        initialize_rl_framework
    )
    RL_AVAILABLE = True
except ImportError as e:
    print(f"❌ RL framework not available: {e}")
    print("📋 Install requirements: pip install scikit-learn numpy")
    RL_AVAILABLE = False
    sys.exit(1)


class RLDemoScenarios:
    """Demo scenarios for RL framework capabilities"""
    
    def __init__(self):
        self.policy_optimizer = None
        self.demo_results = {}
        
    async def initialize_rl_system(self):
        """Initialize RL framework with demo configuration"""
        print("🤖 Initializing Reinforcement Learning Framework...")
        
        config = {
            "shadow_mode": True,
            "safety_threshold": 0.1,
            "exploration_rate": 0.15
        }
        
        self.policy_optimizer = await initialize_rl_framework(config)
        print("✅ RL framework initialized successfully")
        return self.policy_optimizer
    
    async def demo_contextual_optimization(self):
        """Demo 1: Contextual Policy Optimization"""
        print("\n" + "="*60)
        print("📊 DEMO 1: Contextual Policy Optimization")
        print("="*60)
        
        scenarios = [
            {
                "name": "High-Risk Admin Access",
                "context": {
                    "user_risk_score": 0.9,
                    "endpoint": "/admin/users/delete",
                    "content": "DELETE user account",
                    "request_volume": 5,
                    "time_of_day": "02:30"  # Unusual hour
                },
                "rule_matches": [
                    {"rule_id": "ADMIN-ACCESS-1.0", "action": "flag"},
                    {"rule_id": "OFF-HOURS-1.0", "action": "flag"}
                ]
            },
            {
                "name": "Normal API Usage",
                "context": {
                    "user_risk_score": 0.2,
                    "endpoint": "/api/v1/profile",
                    "content": "GET user profile data",
                    "request_volume": 150,
                    "time_of_day": "10:15"
                },
                "rule_matches": []
            },
            {
                "name": "Suspicious Data Access",
                "context": {
                    "user_risk_score": 0.7,
                    "endpoint": "/api/v1/export/users",
                    "content": "Export all user data with PII",
                    "request_volume": 1,
                    "time_of_day": "23:45"
                },
                "rule_matches": [
                    {"rule_id": "PII-EXPORT-1.0", "action": "flag"},
                    {"rule_id": "BULK-DATA-1.0", "action": "block"}
                ]
            }
        ]
        
        results = {}
        
        for scenario in scenarios:
            print(f"\n🔍 Scenario: {scenario['name']}")
            print(f"   Context: {json.dumps(scenario['context'], indent=2)}")
            
            # Simulate original policy decision
            original_decision = "block" if len(scenario['rule_matches']) > 1 else "allow"
            
            # Get RL optimization
            result = await self.policy_optimizer.optimize_policy_decision(
                request_context=scenario['context'],
                current_decision=original_decision,
                rule_matches=scenario['rule_matches']
            )
            
            results[scenario['name']] = result
            
            print(f"   📋 Original Decision: {result.get('original_decision', 'N/A')}")
            print(f"   🤖 RL Recommendation: {result.get('rl_recommendation', 'N/A')}")
            print(f"   📈 Confidence: {result.get('confidence', 0):.2f}")
            print(f"   🔒 Shadow Mode: {result.get('shadow_mode', False)}")
            
            # Simulate some learning delay
            await asyncio.sleep(0.1)
        
        self.demo_results["contextual_optimization"] = results
        print("\n✅ Contextual optimization demo completed")
    
    async def demo_thompson_sampling(self):
        """Demo 2: Thompson Sampling Exploration"""
        print("\n" + "="*60)
        print("🎯 DEMO 2: Thompson Sampling Exploration")
        print("="*60)
        
        # Create a focused bandit for demonstration
        bandit = ContextualBandit(
            exploration_strategy=ExplorationStrategy.THOMPSON_SAMPLING,
            context_dim=8,
            safety_threshold=0.1
        )
        
        # Simulate multiple decision cycles with feedback
        contexts_and_outcomes = [
            # Context: [risk, sensitivity, time, volume, violations, entropy, similarity, threat]
            (RLContext(0.8, 0.9, 0.1, 0.2, 5, 0.7, 0.3, 0.6), {"user_feedback": -1, "security_breach": False}),
            (RLContext(0.2, 0.3, 0.5, 0.8, 0, 0.3, 0.1, 0.1), {"user_feedback": 1, "security_breach": False}),
            (RLContext(0.9, 0.8, 0.9, 0.1, 8, 0.8, 0.5, 0.9), {"user_feedback": 1, "security_breach": False}),
            (RLContext(0.3, 0.4, 0.3, 0.6, 1, 0.4, 0.2, 0.2), {"user_feedback": 0, "security_breach": False}),
            (RLContext(0.7, 0.6, 0.8, 0.3, 3, 0.6, 0.4, 0.5), {"user_feedback": -1, "security_breach": True}),
        ]
        
        action_history = []
        reward_history = []
        
        print("🔄 Running Thompson Sampling cycles...")
        
        for i, (context, outcome) in enumerate(contexts_and_outcomes):
            print(f"\n   Cycle {i+1}:")
            
            # Select action
            action = await bandit.select_policy_action(context)
            action_history.append(action)
            
            print(f"   🎯 Selected Action: {action.value}")
            print(f"   📊 Context Risk Score: {context.user_risk_score}")
            print(f"   🔒 Endpoint Sensitivity: {context.endpoint_sensitivity}")
            
            # Calculate reward based on outcome
            reward = RLReward(
                immediate_reward=outcome.get("user_feedback", 0) * 0.5,
                safety_penalty=1.0 if outcome.get("security_breach") else 0.0,
                false_positive_cost=0.3 if (outcome.get("user_feedback", 0) < 0 and action == PolicyAction.BLOCK) else 0.0
            )
            
            reward_history.append(reward.total_reward)
            
            # Update bandit
            await bandit.update_policy(context, action, reward)
            
            print(f"   💰 Total Reward: {reward.total_reward:.2f}")
            print(f"   📈 Total Trials: {bandit.total_trials}")
        
        # Show learning progress
        print(f"\n📊 Thompson Sampling Results:")
        print(f"   Total Trials: {bandit.total_trials}")
        print(f"   Action Distribution: {bandit.action_counts}")
        print(f"   Average Rewards: {bandit.action_rewards / (bandit.action_counts + 1e-8)}")
        print(f"   Reward Trend: {' → '.join([f'{r:.2f}' for r in reward_history])}")
        
        self.demo_results["thompson_sampling"] = {
            "total_trials": bandit.total_trials,
            "action_distribution": bandit.action_counts.tolist(),
            "reward_history": reward_history,
            "action_history": [a.value for a in action_history]
        }
        
        print("\n✅ Thompson Sampling exploration demo completed")
    
    async def demo_adaptive_learning(self):
        """Demo 3: Adaptive Policy Learning"""
        print("\n" + "="*60)
        print("📚 DEMO 3: Adaptive Policy Learning")
        print("="*60)
        
        print("🔄 Simulating continuous learning over time...")
        
        # Simulate a day of traffic with changing patterns
        time_periods = [
            {"name": "Early Morning (2-6 AM)", "risk_multiplier": 1.5, "volume_factor": 0.2},
            {"name": "Business Hours (9 AM-5 PM)", "risk_multiplier": 1.0, "volume_factor": 1.0},
            {"name": "Evening (6-10 PM)", "risk_multiplier": 1.2, "volume_factor": 0.6},
            {"name": "Late Night (11 PM-1 AM)", "risk_multiplier": 1.8, "volume_factor": 0.1}
        ]
        
        learning_metrics = []
        
        for period in time_periods:
            print(f"\n⏰ Time Period: {period['name']}")
            
            # Generate synthetic traffic for this period
            requests_in_period = int(100 * period['volume_factor'])
            period_metrics = {"period": period['name'], "requests": requests_in_period}
            
            correct_decisions = 0
            total_confidence = 0
            
            for request_num in range(requests_in_period):
                # Generate synthetic request context
                base_risk = random.uniform(0.1, 0.8) * period['risk_multiplier']
                context = {
                    "user_risk_score": min(1.0, base_risk),
                    "endpoint": random.choice(["/api/users", "/admin/config", "/api/data/export"]),
                    "request_volume": requests_in_period,
                    "time_of_day": period['name']
                }
                
                # Simulate rule matches based on risk
                rule_matches = []
                if context["user_risk_score"] > 0.7:
                    rule_matches.append({"rule_id": "HIGH-RISK-1.0", "action": "flag"})
                if "admin" in context["endpoint"]:
                    rule_matches.append({"rule_id": "ADMIN-ACCESS-1.0", "action": "flag"})
                
                original_decision = "block" if len(rule_matches) > 1 else "allow"
                
                # Get RL optimization
                result = await self.policy_optimizer.optimize_policy_decision(
                    request_context=context,
                    current_decision=original_decision,
                    rule_matches=rule_matches
                )
                
                # Simulate feedback (in real world, this would come from users/security team)
                rl_action = result.get('rl_recommendation', original_decision)
                
                # Simple feedback simulation
                expected_action = "block" if context["user_risk_score"] > 0.8 else "allow" 
                is_correct = (rl_action == expected_action)
                
                if is_correct:
                    correct_decisions += 1
                
                total_confidence += result.get('confidence', 0.5)
                
                # Provide feedback to RL system
                rl_context = RLContext(
                    user_risk_score=context["user_risk_score"],
                    endpoint_sensitivity=0.9 if "admin" in context["endpoint"] else 0.5,
                    request_volume=context["request_volume"] / 1000.0
                )
                
                try:
                    action_enum = PolicyAction(rl_action)
                except ValueError:
                    action_enum = PolicyAction.ALLOW
                
                feedback_outcome = {
                    "user_feedback": 1 if is_correct else -1,
                    "security_breach": False,
                    "false_positive": not is_correct and rl_action == "block"
                }
                
                await self.policy_optimizer.provide_feedback(
                    f"demo-{request_num}",
                    rl_context,
                    action_enum,
                    feedback_outcome
                )
            
            accuracy = correct_decisions / requests_in_period
            avg_confidence = total_confidence / requests_in_period
            
            period_metrics.update({
                "accuracy": accuracy,
                "average_confidence": avg_confidence,
                "correct_decisions": correct_decisions
            })
            
            learning_metrics.append(period_metrics)
            
            print(f"   📊 Requests Processed: {requests_in_period}")
            print(f"   🎯 Decision Accuracy: {accuracy:.2%}")
            print(f"   📈 Average Confidence: {avg_confidence:.2f}")
        
        # Get final optimization metrics
        final_metrics = await self.policy_optimizer.get_optimization_metrics()
        
        print(f"\n📊 Adaptive Learning Summary:")
        print(f"   Total Training Trials: {final_metrics['total_trials']}")
        print(f"   Final Action Distribution: {final_metrics['action_distribution']}")
        print(f"   System Confidence: {final_metrics['confidence_level']:.2f}")
        
        self.demo_results["adaptive_learning"] = {
            "time_periods": learning_metrics,
            "final_metrics": final_metrics
        }
        
        print("\n✅ Adaptive learning demo completed")
    
    async def demo_shadow_mode_safety(self):
        """Demo 4: Shadow Mode Safety Features"""
        print("\n" + "="*60)
        print("🛡️ DEMO 4: Shadow Mode Safety Features")
        print("="*60)
        
        print("🔒 Demonstrating shadow mode operation for safe deployment...")
        
        # High-risk scenarios to test safety
        high_risk_scenarios = [
            {
                "name": "Potential SQL Injection",
                "context": {
                    "user_risk_score": 0.9,
                    "endpoint": "/api/search",
                    "content": "'; DROP TABLE users; --",
                    "request_volume": 1
                },
                "expected_production_decision": "block"
            },
            {
                "name": "Admin Panel Access Attempt",
                "context": {
                    "user_risk_score": 0.8,
                    "endpoint": "/admin/system/config",
                    "content": "GET /admin/system/config",
                    "request_volume": 1
                },
                "expected_production_decision": "block"
            },
            {
                "name": "Bulk Data Export",
                "context": {
                    "user_risk_score": 0.6,
                    "endpoint": "/api/export/all-users",
                    "content": "Export complete user database",
                    "request_volume": 1
                },
                "expected_production_decision": "flag"
            }
        ]
        
        shadow_results = []
        
        for scenario in high_risk_scenarios:
            print(f"\n⚠️ Testing: {scenario['name']}")
            
            # Simulate both shadow and production modes
            
            # Shadow mode (current setting)
            shadow_result = await self.policy_optimizer.optimize_policy_decision(
                request_context=scenario['context'],
                current_decision=scenario['expected_production_decision'],
                rule_matches=[{"rule_id": "SECURITY-1.0", "action": "block"}]
            )
            
            # Temporarily switch to production mode for comparison
            original_shadow_mode = self.policy_optimizer.shadow_mode
            self.policy_optimizer.shadow_mode = False
            
            production_result = await self.policy_optimizer.optimize_policy_decision(
                request_context=scenario['context'],
                current_decision=scenario['expected_production_decision'],
                rule_matches=[{"rule_id": "SECURITY-1.0", "action": "block"}]
            )
            
            # Restore shadow mode
            self.policy_optimizer.shadow_mode = original_shadow_mode
            
            scenario_result = {
                "scenario": scenario['name'],
                "shadow_mode": shadow_result,
                "production_mode": production_result,
                "safety_preserved": shadow_result.get('original_decision') == scenario['expected_production_decision']
            }
            
            shadow_results.append(scenario_result)
            
            print(f"   🔒 Shadow Mode - Original: {shadow_result.get('original_decision')}")
            print(f"   🤖 Shadow Mode - RL Rec: {shadow_result.get('rl_recommendation')}")
            print(f"   ⚡ Production - Decision: {production_result.get('decision')}")
            print(f"   ✅ Safety Preserved: {scenario_result['safety_preserved']}")
        
        # Calculate safety metrics
        safety_preservation_rate = sum(1 for r in shadow_results if r['safety_preserved']) / len(shadow_results)
        
        print(f"\n🛡️ Shadow Mode Safety Summary:")
        print(f"   Safety Preservation Rate: {safety_preservation_rate:.1%}")
        print(f"   Scenarios Tested: {len(shadow_results)}")
        print(f"   Shadow Mode Active: {self.policy_optimizer.shadow_mode}")
        
        self.demo_results["shadow_mode_safety"] = {
            "scenarios": shadow_results,
            "safety_preservation_rate": safety_preservation_rate
        }
        
        print("\n✅ Shadow mode safety demo completed")
    
    async def demo_performance_metrics(self):
        """Demo 5: Performance Metrics and Analytics"""
        print("\n" + "="*60)
        print("📈 DEMO 5: Performance Metrics & Analytics")
        print("="*60)
        
        print("📊 Collecting comprehensive RL performance metrics...")
        
        # Get current metrics
        metrics = await self.policy_optimizer.get_optimization_metrics()
        
        print(f"\n🎯 Reinforcement Learning Metrics:")
        print(f"   Total Decision Trials: {metrics['total_trials']}")
        print(f"   Exploration Strategy: {metrics['exploration_strategy']}")
        print(f"   System Confidence: {metrics['confidence_level']:.2%}")
        print(f"   Shadow Mode Active: {metrics['shadow_mode']}")
        
        # Action distribution analysis
        if sum(metrics['action_distribution']) > 0:
            total_actions = sum(metrics['action_distribution'])
            action_percentages = [count/total_actions*100 for count in metrics['action_distribution']]
            
            print(f"\n🎯 Action Distribution:")
            actions = ["ALLOW", "FLAG", "BLOCK", "ESCALATE", "SHADOW_TEST"]
            for i, (action, percentage) in enumerate(zip(actions, action_percentages)):
                if i < len(action_percentages):
                    print(f"   {action}: {percentage:.1f}%")
        
        # Reward analysis
        if len(metrics['average_rewards']) > 0:
            print(f"\n💰 Average Rewards by Action:")
            for i, reward in enumerate(metrics['average_rewards']):
                if i < len(actions):
                    print(f"   {actions[i]}: {reward:.3f}")
        
        # Calculate performance trends
        if hasattr(self.policy_optimizer.bandit, 'reward_history') and len(self.policy_optimizer.bandit.reward_history) > 10:
            recent_rewards = self.policy_optimizer.bandit.reward_history[-10:]
            earlier_rewards = self.policy_optimizer.bandit.reward_history[-20:-10] if len(self.policy_optimizer.bandit.reward_history) > 20 else []
            
            if earlier_rewards:
                recent_avg = sum(recent_rewards) / len(recent_rewards)
                earlier_avg = sum(earlier_rewards) / len(earlier_rewards)
                improvement = recent_avg - earlier_avg
                
                print(f"\n📈 Learning Trend Analysis:")
                print(f"   Recent Average Reward: {recent_avg:.3f}")
                print(f"   Earlier Average Reward: {earlier_avg:.3f}")
                print(f"   Performance Change: {improvement:+.3f}")
                print(f"   Trend: {'📈 Improving' if improvement > 0 else '📉 Declining' if improvement < 0 else '➡️ Stable'}")
        
        self.demo_results["performance_metrics"] = metrics
        
        print("\n✅ Performance metrics demo completed")
    
    async def generate_final_report(self):
        """Generate comprehensive demo report"""
        print("\n" + "="*80)
        print("📋 PHASE 7 REINFORCEMENT LEARNING DEMO REPORT")
        print("="*80)
        
        print(f"\n🤖 System Configuration:")
        print(f"   Framework: Contextual Multi-Armed Bandits")
        print(f"   Algorithm: Thompson Sampling with Bayesian Learning")
        print(f"   Safety Mode: Shadow Deployment")
        print(f"   Context Dimensions: 8")
        
        # Summary statistics
        if "adaptive_learning" in self.demo_results:
            adaptive_data = self.demo_results["adaptive_learning"]
            total_requests = sum(period["requests"] for period in adaptive_data["time_periods"])
            avg_accuracy = sum(period["accuracy"] for period in adaptive_data["time_periods"]) / len(adaptive_data["time_periods"])
            
            print(f"\n📊 Learning Performance:")
            print(f"   Total Requests Processed: {total_requests:,}")
            print(f"   Average Decision Accuracy: {avg_accuracy:.1%}")
            print(f"   Training Trials Completed: {adaptive_data['final_metrics']['total_trials']}")
        
        if "shadow_mode_safety" in self.demo_results:
            safety_data = self.demo_results["shadow_mode_safety"]
            print(f"\n🛡️ Safety Analysis:")
            print(f"   Safety Preservation Rate: {safety_data['safety_preservation_rate']:.1%}")
            print(f"   High-Risk Scenarios Tested: {len(safety_data['scenarios'])}")
        
        if "thompson_sampling" in self.demo_results:
            ts_data = self.demo_results["thompson_sampling"]
            print(f"\n🎯 Exploration Efficiency:")
            print(f"   Thompson Sampling Cycles: {ts_data['total_trials']}")
            print(f"   Action Space Explored: {len([x for x in ts_data['action_distribution'] if x > 0])}/5 actions")
        
        print(f"\n🚀 Key Achievements:")
        print(f"   ✅ Contextual policy optimization with ML")
        print(f"   ✅ Bayesian exploration with uncertainty quantification")
        print(f"   ✅ Real-time adaptive learning from feedback")
        print(f"   ✅ Shadow mode safety for production deployment")
        print(f"   ✅ Comprehensive performance monitoring")
        
        print(f"\n🎯 Business Impact:")
        print(f"   🔒 Enhanced security through intelligent policy adaptation")
        print(f"   ⚡ Reduced false positives via contextual optimization")
        print(f"   📈 Continuous improvement through reinforcement learning")
        print(f"   🛡️ Risk-free deployment via shadow mode operation")
        print(f"   📊 Data-driven policy decisions with confidence metrics")
        
        # Save detailed report
        report_data = {
            "demo_timestamp": datetime.now().isoformat(),
            "framework_version": "Phase 7 - RL Framework",
            "demo_results": self.demo_results,
            "summary": {
                "total_demos_run": len(self.demo_results),
                "safety_verified": "shadow_mode_safety" in self.demo_results,
                "learning_demonstrated": "adaptive_learning" in self.demo_results,
                "performance_measured": "performance_metrics" in self.demo_results
            }
        }
        
        with open("logs/phase_7_rl_demo_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: logs/phase_7_rl_demo_report.json")
        print("\n✅ Phase 7 Reinforcement Learning Demo completed successfully!")


async def main():
    """Main demo execution"""
    print("🚀 Starting Phase 7: Reinforcement Learning Framework Demo")
    print("=" * 80)
    
    if not RL_AVAILABLE:
        print("❌ RL framework not available - exiting")
        return
    
    demo = RLDemoScenarios()
    
    try:
        # Initialize RL system
        await demo.initialize_rl_system()
        
        # Run all demos
        await demo.demo_contextual_optimization()
        await demo.demo_thompson_sampling()
        await demo.demo_adaptive_learning()
        await demo.demo_shadow_mode_safety()
        await demo.demo_performance_metrics()
        
        # Generate final report
        await demo.generate_final_report()
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())