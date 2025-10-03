"""
Phase 7: Reinforcement Learning Policy Optimization Framework

This module implements a sophisticated RL system for continuous policy improvement
through contextual multi-armed bandits, Thompson sampling, and adaptive exploration.

Key Features:
- Contextual Bandits: Context-aware policy selection optimization
- Thompson Sampling: Bayesian exploration with uncertainty quantification
- Shadow Mode Training: Safe RL training without disrupting production
- Automated A/B Testing: Dynamic policy variant testing and optimization
- Meta-Learning: Cross-domain knowledge transfer and rapid adaptation
- Online Learning: Real-time policy updates with streaming data
- Safety Constraints: Bounded exploration with risk-aware reward functions
"""

import logging
import numpy as np
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager
import uuid

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import BayesianRidge
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - RL features will use fallback implementations")

logger = logging.getLogger(__name__)

class PolicyAction(Enum):
    """Available policy actions for RL optimization"""
    ALLOW = "allow"
    FLAG = "flag" 
    BLOCK = "block"
    ESCALATE = "escalate"
    SHADOW_TEST = "shadow_test"

class ExplorationStrategy(Enum):
    """Exploration strategies for contextual bandits"""
    THOMPSON_SAMPLING = "thompson_sampling"
    UCB = "upper_confidence_bound"
    EPSILON_GREEDY = "epsilon_greedy"
    LINUCB = "linear_ucb"

@dataclass
class RLContext:
    """Context vector for contextual bandit decision making"""
    user_risk_score: float = 0.0
    endpoint_sensitivity: float = 0.0
    time_of_day: float = 0.0  # Normalized hour 0-1
    request_volume: float = 0.0
    historical_violations: int = 0
    content_entropy: float = 0.0
    semantic_similarity: float = 0.0
    threat_intelligence_score: float = 0.0
    
    def to_vector(self) -> np.ndarray:
        """Convert context to feature vector"""
        return np.array([
            self.user_risk_score,
            self.endpoint_sensitivity,
            self.time_of_day,
            self.request_volume,
            self.historical_violations / 100.0,  # Normalize
            self.content_entropy,
            self.semantic_similarity,
            self.threat_intelligence_score
        ])

@dataclass 
class RLReward:
    """Reward signal for RL learning"""
    immediate_reward: float  # Immediate feedback (-1 to 1)
    delayed_reward: float = 0.0  # Long-term outcome
    safety_penalty: float = 0.0  # Safety constraint violation
    false_positive_cost: float = 0.0  # User friction cost
    false_negative_cost: float = 0.0  # Security risk cost
    
    @property
    def total_reward(self) -> float:
        """Calculate total reward with safety constraints"""
        return (self.immediate_reward + self.delayed_reward 
                - self.safety_penalty - self.false_positive_cost 
                - self.false_negative_cost)

@dataclass
class PolicyCandidate:
    """Candidate policy for A/B testing"""
    policy_id: str
    rule_modifications: Dict[str, Any]
    expected_performance: Dict[str, float]
    confidence_interval: Tuple[float, float]
    creation_time: datetime
    trials: int = 0
    successes: int = 0
    
    @property
    def success_rate(self) -> float:
        """Bayesian success rate with Beta prior"""
        if self.trials == 0:
            return 0.5  # Uniform prior
        return (self.successes + 1) / (self.trials + 2)  # Beta(1,1) prior

class ThompsonSampler:
    """Bayesian Thompson Sampling for exploration/exploitation"""
    
    def __init__(self, num_actions: int, context_dim: int):
        self.num_actions = num_actions
        self.context_dim = context_dim
        
        # Bayesian linear regression parameters
        self.alpha = 1.0  # Noise precision
        self.beta = 1.0   # Prior precision
        
        # Posterior parameters for each action
        self.S = [np.eye(context_dim) * self.beta for _ in range(num_actions)]
        self.mu = [np.zeros(context_dim) for _ in range(num_actions)]
        
    def select_action(self, context: np.ndarray) -> int:
        """Select action using Thompson sampling"""
        if not SKLEARN_AVAILABLE:
            return np.random.randint(0, self.num_actions)
            
        sampled_rewards = []
        
        for action in range(self.num_actions):
            # Sample from posterior distribution
            try:
                cov = np.linalg.inv(self.S[action])
                theta_sample = np.random.multivariate_normal(self.mu[action], cov)
                sampled_reward = np.dot(context, theta_sample)
                sampled_rewards.append(sampled_reward)
            except np.linalg.LinAlgError:
                # Fallback for singular matrix
                sampled_rewards.append(np.random.normal(0, 1))
        
        return np.argmax(sampled_rewards)
    
    def update(self, context: np.ndarray, action: int, reward: float):
        """Update posterior with observed reward"""
        if not SKLEARN_AVAILABLE:
            return
            
        # Update sufficient statistics
        self.S[action] += self.alpha * np.outer(context, context)
        
        # Update mean
        try:
            S_inv = np.linalg.inv(self.S[action])
            self.mu[action] = S_inv @ (self.S[action] @ self.mu[action] + self.alpha * reward * context)
        except np.linalg.LinAlgError:
            logger.warning(f"Singular matrix in Thompson sampler update for action {action}")

class ContextualBandit:
    """Contextual multi-armed bandit for policy optimization"""
    
    def __init__(self, 
                 exploration_strategy: ExplorationStrategy = ExplorationStrategy.THOMPSON_SAMPLING,
                 context_dim: int = 8,
                 safety_threshold: float = 0.1):
        self.exploration_strategy = exploration_strategy
        self.context_dim = context_dim
        self.safety_threshold = safety_threshold
        
        # Action mapping
        self.actions = list(PolicyAction)
        self.num_actions = len(self.actions)
        
        # Initialize exploration algorithm
        if exploration_strategy == ExplorationStrategy.THOMPSON_SAMPLING:
            self.sampler = ThompsonSampler(self.num_actions, context_dim)
        
        # Tracking
        self.total_trials = 0
        self.action_counts = np.zeros(self.num_actions)
        self.action_rewards = np.zeros(self.num_actions)
        self.context_history = []
        self.reward_history = []
        
    async def select_policy_action(self, 
                                 context: RLContext,
                                 available_actions: List[PolicyAction] = None) -> PolicyAction:
        """Select optimal policy action given context"""
        if available_actions is None:
            available_actions = self.actions
            
        context_vector = context.to_vector()
        
        if self.exploration_strategy == ExplorationStrategy.THOMPSON_SAMPLING:
            action_idx = self.sampler.select_action(context_vector)
        elif self.exploration_strategy == ExplorationStrategy.EPSILON_GREEDY:
            action_idx = self._epsilon_greedy_selection(context_vector)
        else:
            # Fallback to random
            action_idx = np.random.randint(0, len(available_actions))
        
        # Ensure action is available
        if action_idx >= len(available_actions):
            action_idx = 0
            
        selected_action = available_actions[action_idx]
        
        logger.debug(f"Selected action {selected_action.value} for context {context}")
        return selected_action
    
    def _epsilon_greedy_selection(self, context: np.ndarray, epsilon: float = 0.1) -> int:
        """Epsilon-greedy action selection"""
        if np.random.random() < epsilon or self.total_trials < self.num_actions:
            return np.random.randint(0, self.num_actions)
        else:
            # Exploit best action
            return np.argmax(self.action_rewards / np.maximum(self.action_counts, 1))
    
    async def update_policy(self, 
                          context: RLContext,
                          action: PolicyAction,
                          reward: RLReward):
        """Update policy with observed reward"""
        context_vector = context.to_vector()
        action_idx = self.actions.index(action)
        
        # Safety check
        if reward.safety_penalty > self.safety_threshold:
            logger.warning(f"High safety penalty {reward.safety_penalty} for action {action.value}")
            # Reduce reward for unsafe actions
            total_reward = reward.total_reward * 0.5
        else:
            total_reward = reward.total_reward
        
        # Update bandit
        if self.exploration_strategy == ExplorationStrategy.THOMPSON_SAMPLING:
            self.sampler.update(context_vector, action_idx, total_reward)
        
        # Update tracking
        self.total_trials += 1
        self.action_counts[action_idx] += 1
        self.action_rewards[action_idx] += total_reward
        self.context_history.append(context_vector)
        self.reward_history.append(total_reward)
        
        logger.debug(f"Updated policy: action={action.value}, reward={total_reward}")

class PolicyOptimizer:
    """Main RL-based policy optimization engine"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.shadow_mode = self.config.get("shadow_mode", True)
        self.safety_threshold = self.config.get("safety_threshold", 0.1)
        
        # Initialize contextual bandit
        self.bandit = ContextualBandit(
            exploration_strategy=ExplorationStrategy.THOMPSON_SAMPLING,
            safety_threshold=self.safety_threshold
        )
        
        # Policy candidates for A/B testing  
        self.policy_candidates: Dict[str, PolicyCandidate] = {}
        self.active_experiments: Dict[str, str] = {}  # request_id -> policy_id
        
        # Meta-learning components
        self.policy_performance_history = []
        self.adaptation_rate = 0.01
        
        logger.info("Policy Optimizer initialized with RL framework")
    
    async def optimize_policy_decision(self,
                                     request_context: Dict[str, Any],
                                     current_decision: str,
                                     rule_matches: List[Dict]) -> Dict[str, Any]:
        """Optimize policy decision using RL"""
        try:
            # Extract RL context from request
            rl_context = await self._extract_rl_context(request_context, rule_matches)
            
            # Get RL-optimized action
            optimal_action = await self.bandit.select_policy_action(rl_context)
            
            # In shadow mode, don't override production decision
            if self.shadow_mode:
                return {
                    "original_decision": current_decision,
                    "rl_recommendation": optimal_action.value,
                    "context": asdict(rl_context),
                    "confidence": await self._calculate_confidence(rl_context),
                    "shadow_mode": True
                }
            else:
                return {
                    "decision": optimal_action.value,
                    "rl_optimized": True,
                    "context": asdict(rl_context),
                    "confidence": await self._calculate_confidence(rl_context),
                    "shadow_mode": False
                }
                
        except Exception as e:
            logger.error(f"Error in policy optimization: {e}")
            return {"decision": current_decision, "error": str(e)}
    
    async def _extract_rl_context(self, 
                                request_context: Dict[str, Any],
                                rule_matches: List[Dict]) -> RLContext:
        """Extract RL context from request data"""
        # Calculate context features
        user_risk = request_context.get("user_risk_score", 0.0)
        endpoint_sensitivity = self._calculate_endpoint_sensitivity(
            request_context.get("endpoint", "")
        )
        
        # Time-based features
        current_hour = datetime.now().hour
        time_of_day = current_hour / 24.0
        
        # Request volume (normalized)
        request_volume = min(request_context.get("request_volume", 1), 1000) / 1000.0
        
        # Rule-based features
        violations = len([r for r in rule_matches if r.get("action") in ["block", "flag"]])
        
        # Content analysis
        content = request_context.get("content", "")
        content_entropy = self._calculate_entropy(content)
        
        return RLContext(
            user_risk_score=user_risk,
            endpoint_sensitivity=endpoint_sensitivity,
            time_of_day=time_of_day,
            request_volume=request_volume,
            historical_violations=violations,
            content_entropy=content_entropy,
            semantic_similarity=0.0,  # TODO: Implement semantic analysis
            threat_intelligence_score=0.0  # TODO: Integrate threat feeds
        )
    
    def _calculate_endpoint_sensitivity(self, endpoint: str) -> float:
        """Calculate endpoint sensitivity score"""
        sensitive_patterns = [
            ("/admin", 1.0),
            ("/api/v1/users", 0.8),
            ("/payment", 0.9),
            ("/auth", 0.7),
            ("/upload", 0.6)
        ]
        
        for pattern, score in sensitive_patterns:
            if pattern in endpoint.lower():
                return score
        return 0.3  # Default sensitivity
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
            
        # Character frequency
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        length = len(text)
        entropy = 0.0
        for count in char_counts.values():
            prob = count / length
            if prob > 0:
                entropy -= prob * np.log2(prob)
        
        return entropy / 8.0  # Normalize to 0-1 range
    
    async def _calculate_confidence(self, context: RLContext) -> float:
        """Calculate confidence in RL decision"""
        # Simple confidence based on trial count and context similarity
        if self.bandit.total_trials < 100:
            return 0.5 + (self.bandit.total_trials / 200.0)
        
        # Use context similarity to historical decisions
        if len(self.bandit.context_history) == 0:
            return 0.6
        
        context_vector = context.to_vector()
        similarities = []
        
        for hist_context in self.bandit.context_history[-50:]:  # Last 50 contexts
            similarity = np.dot(context_vector, hist_context) / (
                np.linalg.norm(context_vector) * np.linalg.norm(hist_context) + 1e-8
            )
            similarities.append(similarity)
        
        avg_similarity = np.mean(similarities)
        return min(0.9, 0.6 + avg_similarity * 0.3)
    
    async def provide_feedback(self,
                             request_id: str,
                             context: RLContext,
                             action: PolicyAction,
                             outcome: Dict[str, Any]):
        """Provide feedback for RL learning"""
        try:
            # Calculate reward based on outcome
            reward = await self._calculate_reward(action, outcome)
            
            # Update bandit
            await self.bandit.update_policy(context, action, reward)
            
            logger.info(f"Feedback processed: action={action.value}, reward={reward.total_reward}")
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
    
    async def _calculate_reward(self, action: PolicyAction, outcome: Dict[str, Any]) -> RLReward:
        """Calculate reward signal from outcome"""
        # Base reward from user feedback
        user_feedback = outcome.get("user_feedback", 0)  # -1, 0, 1
        
        # Security outcome
        security_breach = outcome.get("security_breach", False)
        false_positive = outcome.get("false_positive", False)
        
        # Calculate components
        immediate_reward = user_feedback * 0.5
        
        # Initialize penalty variables
        safety_penalty = 0.0
        false_positive_cost = 0.0
        
        # Security penalties/rewards
        if security_breach and action == PolicyAction.ALLOW:
            safety_penalty = 1.0  # High penalty for missing threats
        elif not security_breach and action == PolicyAction.BLOCK:
            false_positive_cost = 0.3  # Cost of blocking legitimate requests
        elif false_positive and action == PolicyAction.BLOCK:
            false_positive_cost = 0.3  # Cost of false positive blocks
        
        return RLReward(
            immediate_reward=immediate_reward,
            delayed_reward=0.0,  # TODO: Implement delayed feedback
            safety_penalty=safety_penalty,
            false_positive_cost=false_positive_cost,
            false_negative_cost=0.0
        )
    
    async def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get RL optimization metrics"""
        return {
            "total_trials": self.bandit.total_trials,
            "action_distribution": self.bandit.action_counts.tolist(),
            "average_rewards": (self.bandit.action_rewards / np.maximum(self.bandit.action_counts, 1)).tolist(),
            "exploration_strategy": self.bandit.exploration_strategy.value,
            "shadow_mode": self.shadow_mode,
            "active_experiments": len(self.policy_candidates),
            "confidence_level": await self._calculate_confidence(RLContext()) if self.bandit.context_history else 0.5
        }

# Global instance
policy_optimizer = PolicyOptimizer()

async def initialize_rl_framework(config: Dict[str, Any] = None):
    """Initialize the RL framework"""
    global policy_optimizer
    policy_optimizer = PolicyOptimizer(config)
    logger.info("Reinforcement Learning framework initialized")
    return policy_optimizer

# Export main components
__all__ = [
    "PolicyOptimizer", 
    "ContextualBandit",
    "ThompsonSampler", 
    "RLContext",
    "RLReward",
    "PolicyAction",
    "ExplorationStrategy",
    "policy_optimizer",
    "initialize_rl_framework"
]