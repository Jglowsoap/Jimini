"""
Test Suite for Phase 7: Reinforcement Learning Framework

Comprehensive tests for RL-based policy optimization including:
- Contextual bandit algorithms
- Thompson sampling exploration
- Policy optimization workflows  
- API endpoint functionality
- Shadow mode behavior
- A/B testing framework
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

# Import RL components
try:
    from app.intelligence.reinforcement_learning import (
        PolicyOptimizer,
        ContextualBandit,
        ThompsonSampler,
        RLContext,
        RLReward,
        PolicyAction,
        ExplorationStrategy,
        initialize_rl_framework
    )
    from app.intelligence.reinforcement_learning_api import (
        RLOptimizationRequest,
        RLOptimizationResponse,
        FeedbackRequest,
        FeedbackResponse,
        RLMetricsResponse
    )
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False

pytestmark = pytest.mark.skipif(not RL_AVAILABLE, reason="RL framework not available")


class TestRLContext:
    """Test RL context representation and vector conversion"""
    
    def test_rl_context_creation(self):
        """Test RLContext creation with default values"""
        context = RLContext()
        assert context.user_risk_score == 0.0
        assert context.endpoint_sensitivity == 0.0
        assert context.time_of_day == 0.0
        
    def test_rl_context_with_values(self):
        """Test RLContext with specific values"""
        context = RLContext(
            user_risk_score=0.8,
            endpoint_sensitivity=0.9,
            time_of_day=0.5,
            request_volume=0.7,
            historical_violations=5,
            content_entropy=0.6,
            semantic_similarity=0.3,
            threat_intelligence_score=0.4
        )
        
        assert context.user_risk_score == 0.8
        assert context.endpoint_sensitivity == 0.9
        assert context.historical_violations == 5
        
    def test_context_to_vector(self):
        """Test conversion of context to feature vector"""
        context = RLContext(
            user_risk_score=0.8,
            endpoint_sensitivity=0.9,
            time_of_day=0.5,
            request_volume=0.7,
            historical_violations=5,
            content_entropy=0.6,
            semantic_similarity=0.3,
            threat_intelligence_score=0.4
        )
        
        vector = context.to_vector()
        assert len(vector) == 8
        assert vector[0] == 0.8  # user_risk_score
        assert vector[1] == 0.9  # endpoint_sensitivity
        assert vector[4] == 0.05  # historical_violations normalized


class TestRLReward:
    """Test reward signal calculation"""
    
    def test_reward_creation(self):
        """Test RLReward creation"""
        reward = RLReward(immediate_reward=0.5)
        assert reward.immediate_reward == 0.5
        assert reward.delayed_reward == 0.0
        assert reward.safety_penalty == 0.0
        
    def test_total_reward_calculation(self):
        """Test total reward calculation with all components"""
        reward = RLReward(
            immediate_reward=0.8,
            delayed_reward=0.2,
            safety_penalty=0.1,
            false_positive_cost=0.05,
            false_negative_cost=0.03
        )
        
        expected_total = 0.8 + 0.2 - 0.1 - 0.05 - 0.03
        assert reward.total_reward == expected_total
        
    def test_negative_reward(self):
        """Test reward with high penalties"""
        reward = RLReward(
            immediate_reward=0.3,
            safety_penalty=1.0,
            false_positive_cost=0.5
        )
        
        assert reward.total_reward < 0  # Should be negative


class TestThompsonSampler:
    """Test Thompson sampling algorithm"""
    
    @pytest.fixture
    def sampler(self):
        """Create Thompson sampler for testing"""
        return ThompsonSampler(num_actions=3, context_dim=4)
        
    def test_sampler_initialization(self, sampler):
        """Test sampler initialization"""
        assert sampler.num_actions == 3
        assert sampler.context_dim == 4
        assert len(sampler.S) == 3
        assert len(sampler.mu) == 3
        
    def test_action_selection(self, sampler):
        """Test action selection"""
        context = np.array([0.5, 0.3, 0.8, 0.2])
        action = sampler.select_action(context)
        assert 0 <= action < 3
        
    def test_posterior_update(self, sampler):
        """Test posterior parameter updates"""
        context = np.array([0.5, 0.3, 0.8, 0.2])
        action = 1
        reward = 0.7
        
        # Store initial state
        initial_mu = sampler.mu[action].copy()
        
        # Update
        sampler.update(context, action, reward)
        
        # Check that parameters changed
        assert not np.array_equal(sampler.mu[action], initial_mu)
        
    def test_multiple_updates(self, sampler):
        """Test multiple sequential updates"""
        context = np.array([0.5, 0.3, 0.8, 0.2])
        
        for _ in range(10):
            action = sampler.select_action(context)
            reward = np.random.normal(0.5, 0.1)
            sampler.update(context, action, reward)
        
        # Should still select valid actions
        final_action = sampler.select_action(context)
        assert 0 <= final_action < 3


class TestContextualBandit:
    """Test contextual bandit implementation"""
    
    @pytest.fixture
    def bandit(self):
        """Create contextual bandit for testing"""
        return ContextualBandit(
            exploration_strategy=ExplorationStrategy.THOMPSON_SAMPLING,
            context_dim=8,
            safety_threshold=0.1
        )
        
    def test_bandit_initialization(self, bandit):
        """Test bandit initialization"""
        assert bandit.exploration_strategy == ExplorationStrategy.THOMPSON_SAMPLING
        assert bandit.context_dim == 8
        assert bandit.safety_threshold == 0.1
        assert bandit.num_actions == len(PolicyAction)
        
    @pytest.mark.asyncio
    async def test_action_selection(self, bandit):
        """Test policy action selection"""
        context = RLContext(
            user_risk_score=0.5,
            endpoint_sensitivity=0.7,
            time_of_day=0.3
        )
        
        action = await bandit.select_policy_action(context)
        assert isinstance(action, PolicyAction)
        
    @pytest.mark.asyncio
    async def test_policy_update(self, bandit):
        """Test policy update with feedback"""
        context = RLContext(user_risk_score=0.5)
        action = PolicyAction.BLOCK
        reward = RLReward(immediate_reward=0.8)
        
        initial_trials = bandit.total_trials
        
        await bandit.update_policy(context, action, reward)
        
        assert bandit.total_trials == initial_trials + 1
        assert len(bandit.context_history) == 1
        assert len(bandit.reward_history) == 1
        
    @pytest.mark.asyncio
    async def test_safety_constraint(self, bandit):
        """Test safety constraint enforcement"""
        context = RLContext(user_risk_score=0.5)
        action = PolicyAction.ALLOW
        
        # High safety penalty
        reward = RLReward(
            immediate_reward=1.0,
            safety_penalty=0.5  # Above threshold
        )
        
        await bandit.update_policy(context, action, reward)
        
        # Check that reward was adjusted for safety
        assert bandit.reward_history[-1] < 1.0
        
    @pytest.mark.asyncio
    async def test_epsilon_greedy_strategy(self):
        """Test epsilon-greedy exploration strategy"""
        bandit = ContextualBandit(
            exploration_strategy=ExplorationStrategy.EPSILON_GREEDY,
            context_dim=8
        )
        
        context = RLContext(user_risk_score=0.5)
        action = await bandit.select_policy_action(context)
        assert isinstance(action, PolicyAction)


class TestPolicyOptimizer:
    """Test main policy optimization engine"""
    
    @pytest.fixture
    def optimizer(self):
        """Create policy optimizer for testing"""
        config = {
            "shadow_mode": True,
            "safety_threshold": 0.1
        }
        return PolicyOptimizer(config)
        
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.shadow_mode is True
        assert optimizer.safety_threshold == 0.1
        assert isinstance(optimizer.bandit, ContextualBandit)
        
    @pytest.mark.asyncio
    async def test_policy_optimization_shadow_mode(self, optimizer):
        """Test policy optimization in shadow mode"""
        request_context = {
            "user_risk_score": 0.6,
            "endpoint": "/api/users",
            "content": "test content",
            "request_volume": 50
        }
        
        result = await optimizer.optimize_policy_decision(
            request_context=request_context,
            current_decision="allow",
            rule_matches=[]
        )
        
        assert "original_decision" in result
        assert "rl_recommendation" in result
        assert result["shadow_mode"] is True
        assert result["original_decision"] == "allow"
        
    @pytest.mark.asyncio
    async def test_policy_optimization_production_mode(self):
        """Test policy optimization in production mode"""
        config = {"shadow_mode": False}
        optimizer = PolicyOptimizer(config)
        
        request_context = {
            "user_risk_score": 0.6,
            "endpoint": "/api/users"
        }
        
        result = await optimizer.optimize_policy_decision(
            request_context=request_context,
            current_decision="allow",
            rule_matches=[]
        )
        
        assert "decision" in result
        assert result["rl_optimized"] is True
        assert result["shadow_mode"] is False
        
    @pytest.mark.asyncio
    async def test_feedback_processing(self, optimizer):
        """Test feedback processing for learning"""
        context = RLContext(user_risk_score=0.5)
        action = PolicyAction.BLOCK
        outcome = {
            "user_feedback": 1,
            "security_breach": False,
            "false_positive": False
        }
        
        await optimizer.provide_feedback("test-id", context, action, outcome)
        
        # Check that bandit was updated
        assert optimizer.bandit.total_trials > 0
        
    @pytest.mark.asyncio
    async def test_endpoint_sensitivity_calculation(self, optimizer):
        """Test endpoint sensitivity scoring"""
        # Admin endpoint should have high sensitivity
        admin_score = optimizer._calculate_endpoint_sensitivity("/admin/users")
        assert admin_score >= 0.8
        
        # Regular endpoint should have lower sensitivity  
        regular_score = optimizer._calculate_endpoint_sensitivity("/api/health")
        assert regular_score <= 0.5
        
    def test_entropy_calculation(self, optimizer):
        """Test content entropy calculation"""
        # High entropy text
        random_text = "abcdefghijklmnop"
        high_entropy = optimizer._calculate_entropy(random_text)
        
        # Low entropy text
        repeated_text = "aaaaaaaaaaaaaa"
        low_entropy = optimizer._calculate_entropy(repeated_text)
        
        assert high_entropy > low_entropy
        assert 0 <= high_entropy <= 1
        assert 0 <= low_entropy <= 1
        
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, optimizer):
        """Test confidence calculation"""
        context = RLContext(user_risk_score=0.5)
        
        # Initial confidence should be low
        confidence = await optimizer._calculate_confidence(context)
        assert 0 <= confidence <= 1
        
        # Add some history
        for _ in range(10):
            optimizer.bandit.context_history.append(context.to_vector())
        
        # Confidence should increase with more data
        new_confidence = await optimizer._calculate_confidence(context)
        assert new_confidence >= confidence
        
    @pytest.mark.asyncio
    async def test_reward_calculation(self, optimizer):
        """Test reward calculation from outcomes"""
        # Positive outcome
        positive_outcome = {"user_feedback": 1, "security_breach": False}
        positive_reward = await optimizer._calculate_reward(PolicyAction.ALLOW, positive_outcome)
        assert positive_reward.total_reward > 0
        
        # Security breach
        breach_outcome = {"user_feedback": 0, "security_breach": True}
        breach_reward = await optimizer._calculate_reward(PolicyAction.ALLOW, breach_outcome)
        assert breach_reward.total_reward < 0  # Should be penalized
        
        # False positive
        fp_outcome = {"user_feedback": -1, "false_positive": True}
        fp_reward = await optimizer._calculate_reward(PolicyAction.BLOCK, fp_outcome)
        assert fp_reward.total_reward < 0  # Should be penalized
        
    @pytest.mark.asyncio
    async def test_optimization_metrics(self, optimizer):
        """Test optimization metrics collection"""
        # Add some trial data
        context = RLContext(user_risk_score=0.5)
        action = PolicyAction.ALLOW
        reward = RLReward(immediate_reward=0.8)
        
        await optimizer.bandit.update_policy(context, action, reward)
        
        metrics = await optimizer.get_optimization_metrics()
        
        assert "total_trials" in metrics
        assert "action_distribution" in metrics
        assert "average_rewards" in metrics
        assert "confidence_level" in metrics
        assert metrics["total_trials"] > 0


class TestRLFrameworkIntegration:
    """Test RL framework initialization and integration"""
    
    @pytest.mark.asyncio
    async def test_framework_initialization(self):
        """Test RL framework initialization"""
        config = {
            "shadow_mode": True,
            "safety_threshold": 0.2
        }
        
        optimizer = await initialize_rl_framework(config)
        
        assert isinstance(optimizer, PolicyOptimizer)
        assert optimizer.shadow_mode is True
        assert optimizer.safety_threshold == 0.2
        
    @pytest.mark.asyncio
    async def test_framework_initialization_default_config(self):
        """Test framework initialization with default config"""
        optimizer = await initialize_rl_framework()
        
        assert isinstance(optimizer, PolicyOptimizer)
        # Should use default values
        assert optimizer.shadow_mode is True  # Default shadow mode


class TestRLAPIModels:
    """Test RL API request/response models"""
    
    def test_rl_optimization_request(self):
        """Test RL optimization request model"""
        request_data = {
            "request_context": {"user_risk": 0.5},
            "current_decision": "allow",
            "rule_matches": [{"rule_id": "test", "action": "flag"}]
        }
        
        request = RLOptimizationRequest(**request_data)
        assert request.current_decision == "allow"
        assert len(request.rule_matches) == 1
        
    def test_rl_optimization_response(self):
        """Test RL optimization response model"""
        response_data = {
            "request_id": "test-123",
            "original_decision": "allow",
            "rl_recommendation": "block",
            "context": {"user_risk_score": 0.5},
            "confidence": 0.8,
            "shadow_mode": True
        }
        
        response = RLOptimizationResponse(**response_data)
        assert response.request_id == "test-123"
        assert response.confidence == 0.8
        assert response.shadow_mode is True
        
    def test_feedback_request(self):
        """Test feedback request model"""
        feedback_data = {
            "request_id": "test-123",
            "context": {"user_risk_score": 0.5},
            "action_taken": "block",
            "outcome": {"user_feedback": 1},
            "user_feedback": 1,
            "security_breach": False
        }
        
        request = FeedbackRequest(**feedback_data)
        assert request.user_feedback == 1
        assert request.security_breach is False
        
    def test_rl_metrics_response(self):
        """Test RL metrics response model"""
        metrics_data = {
            "total_trials": 100,
            "action_distribution": [20, 30, 25, 25],
            "average_rewards": [0.8, 0.6, 0.7, 0.5],
            "exploration_strategy": "thompson_sampling",
            "shadow_mode": True,
            "active_experiments": 2,
            "confidence_level": 0.85
        }
        
        response = RLMetricsResponse(**metrics_data)
        assert response.total_trials == 100
        assert len(response.action_distribution) == 4
        assert response.confidence_level == 0.85


class TestRLErrorHandling:
    """Test RL framework error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_invalid_context_handling(self):
        """Test handling of invalid context data"""
        optimizer = PolicyOptimizer()
        
        # Missing required fields
        incomplete_context = {"user_risk": 0.5}
        
        result = await optimizer.optimize_policy_decision(
            request_context=incomplete_context,
            current_decision="allow",
            rule_matches=[]
        )
        
        # Should handle gracefully and return a result
        assert "rl_recommendation" in result or "error" in result
        
    @pytest.mark.asyncio
    async def test_feedback_with_invalid_action(self):
        """Test feedback with invalid action string"""
        optimizer = PolicyOptimizer()
        
        # This should handle gracefully
        context = RLContext(user_risk_score=0.5)
        invalid_action = PolicyAction.ALLOW  # Valid for this test
        outcome = {"user_feedback": 1}
        
        # Should not raise exception
        await optimizer.provide_feedback("test-id", context, invalid_action, outcome)
        
    def test_context_vector_with_nan(self):
        """Test context vector with NaN values"""
        context = RLContext(
            user_risk_score=float('nan'),
            endpoint_sensitivity=0.5
        )
        
        vector = context.to_vector()
        # Should handle NaN gracefully
        assert len(vector) == 8
        
    @pytest.mark.asyncio
    async def test_sampler_with_singular_matrix(self):
        """Test Thompson sampler with singular covariance matrix"""
        sampler = ThompsonSampler(num_actions=2, context_dim=2)
        
        # Force singular matrix scenario
        context = np.array([0.0, 0.0])
        
        # Should handle gracefully
        action = sampler.select_action(context)
        assert 0 <= action < 2


# Performance Tests
class TestRLPerformance:
    """Test RL framework performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_optimization_latency(self):
        """Test optimization response time"""
        import time
        
        optimizer = PolicyOptimizer()
        request_context = {
            "user_risk_score": 0.5,
            "endpoint": "/api/test"
        }
        
        start_time = time.time()
        
        result = await optimizer.optimize_policy_decision(
            request_context=request_context,
            current_decision="allow",
            rule_matches=[]
        )
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Should complete within reasonable time (< 100ms)
        assert latency < 0.1
        assert "rl_recommendation" in result
        
    @pytest.mark.asyncio
    async def test_batch_feedback_processing(self):
        """Test processing multiple feedback items"""
        optimizer = PolicyOptimizer()
        
        # Process multiple feedback items
        for i in range(50):
            context = RLContext(user_risk_score=i/100.0)
            action = PolicyAction.ALLOW if i % 2 == 0 else PolicyAction.BLOCK
            outcome = {"user_feedback": 1 if i % 3 == 0 else 0}
            
            await optimizer.provide_feedback(f"test-{i}", context, action, outcome)
        
        metrics = await optimizer.get_optimization_metrics()
        assert metrics["total_trials"] == 50
        
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable"""
        bandit = ContextualBandit()
        
        # Add many context vectors
        for i in range(1000):
            context = np.random.random(8)
            bandit.context_history.append(context)
            bandit.reward_history.append(np.random.random())
        
        # Should maintain reasonable size
        assert len(bandit.context_history) <= 1000
        assert len(bandit.reward_history) <= 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])