"""
Phase 6C - Intelligent Policy Recommendations Engine
Smart policy optimization with cross-regulation conflict detection

This module implements intelligent policy recommendation capabilities:

1. Cross-Regulation Conflict Detection - Identify conflicting policy rules
2. Smart Policy Optimization - ML-powered policy tuning suggestions  
3. Automated Compliance Gap Analysis - Missing coverage identification
4. Policy Performance Analytics - Data-driven optimization insights
5. Recommendation Engine - Actionable policy improvement suggestions
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import logging
from pathlib import Path

try:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from app.models import Rule, EvaluateRequest, EvaluateResponse
from app.util import get_logger

logger = get_logger(__name__)


class RecommendationType(str, Enum):
    """Types of policy recommendations."""
    CONFLICT_RESOLUTION = "conflict_resolution"
    OPTIMIZATION = "optimization" 
    COVERAGE_GAP = "coverage_gap"
    PERFORMANCE_TUNING = "performance_tuning"
    SECURITY_ENHANCEMENT = "security_enhancement"
    COMPLIANCE_ALIGNMENT = "compliance_alignment"


class RecommendationPriority(str, Enum):
    """Recommendation priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ConflictType(str, Enum):
    """Types of policy conflicts."""
    OVERLAPPING_PATTERNS = "overlapping_patterns"
    CONTRADICTORY_ACTIONS = "contradictory_actions"
    SCOPE_CONFLICTS = "scope_conflicts"
    REDUNDANT_RULES = "redundant_rules"
    PRECEDENCE_ISSUES = "precedence_issues"


@dataclass
class PolicyConflict:
    """Represents a detected policy conflict."""
    conflict_id: str
    conflict_type: ConflictType
    rule_ids: List[str]
    description: str
    impact_assessment: str
    resolution_suggestions: List[str]
    confidence_score: float
    detected_at: str


@dataclass 
class PolicyRecommendation:
    """Represents a policy optimization recommendation."""
    recommendation_id: str
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    affected_rules: List[str]
    suggested_changes: Dict[str, Any]
    rationale: str
    expected_impact: str
    confidence_score: float
    created_at: str
    implementation_steps: List[str]


@dataclass
class CoverageGap:
    """Represents identified policy coverage gaps."""
    gap_id: str
    gap_type: str  # "endpoint", "content_pattern", "regulation_area"
    description: str
    uncovered_scenarios: List[str]
    suggested_rules: List[Dict[str, Any]]
    risk_level: str
    compliance_implications: List[str]
    identified_at: str


@dataclass
class PolicyPerformanceMetrics:
    """Policy performance analytics."""
    rule_id: str
    total_evaluations: int
    block_rate: float
    flag_rate: float
    allow_rate: float
    false_positive_rate: float
    false_negative_rate: float
    average_response_time: float
    effectiveness_score: float
    last_updated: str


class PolicyRecommendationEngine:
    """Advanced policy recommendation and conflict detection engine."""
    
    def __init__(self, rules_cache: Dict[str, Rule] = None):
        self.rules_cache = rules_cache or {}
        self.conflicts_detected = []
        self.recommendations_generated = []
        self.coverage_gaps_identified = []
        self.performance_metrics = {}
        
        # Initialize ML components if available
        if ML_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 3)
            )
            self.similarity_threshold = 0.8
        else:
            self.vectorizer = None
            self.similarity_threshold = None
            
        logger.info(f"Policy Recommendation Engine initialized (ML: {ML_AVAILABLE})")
    
    def analyze_policy_conflicts(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """Comprehensive policy conflict analysis."""
        logger.info("Starting comprehensive policy conflict analysis")
        
        conflicts = []
        self.rules_cache = rules
        
        # 1. Pattern Overlap Detection
        conflicts.extend(self._detect_pattern_overlaps(rules))
        
        # 2. Action Contradiction Detection  
        conflicts.extend(self._detect_action_contradictions(rules))
        
        # 3. Scope Conflict Detection
        conflicts.extend(self._detect_scope_conflicts(rules))
        
        # 4. Redundant Rule Detection
        conflicts.extend(self._detect_redundant_rules(rules))
        
        # 5. Precedence Issue Detection
        conflicts.extend(self._detect_precedence_issues(rules))
        
        self.conflicts_detected = conflicts
        logger.info(f"Detected {len(conflicts)} policy conflicts")
        
        return conflicts
    
    def _detect_pattern_overlaps(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """Detect overlapping regex patterns that might conflict."""
        conflicts = []
        
        # Group rules by pattern similarity
        pattern_rules = [(rule_id, rule) for rule_id, rule in rules.items() 
                        if rule.pattern]
        
        for i, (rule_id_1, rule_1) in enumerate(pattern_rules):
            for rule_id_2, rule_2 in pattern_rules[i+1:]:
                
                # Check for literal pattern overlaps
                overlap_score = self._calculate_pattern_overlap(
                    rule_1.pattern, rule_2.pattern
                )
                
                if overlap_score > 0.3:  # More sensitive threshold for overlaps
                    conflict = PolicyConflict(
                        conflict_id=f"overlap_{rule_id_1}_{rule_id_2}",
                        conflict_type=ConflictType.OVERLAPPING_PATTERNS,
                        rule_ids=[rule_id_1, rule_id_2],
                        description=f"Rules have overlapping patterns: '{rule_1.pattern}' and '{rule_2.pattern}'",
                        impact_assessment="May cause unpredictable evaluation results",
                        resolution_suggestions=[
                            "Merge rules with compatible actions",
                            "Add more specific pattern constraints",
                            "Adjust rule precedence order"
                        ],
                        confidence_score=overlap_score,
                        detected_at=datetime.now().isoformat()
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_action_contradictions(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """Detect rules with same patterns but contradictory actions."""
        conflicts = []
        
        # Group rules by similar patterns
        pattern_groups = defaultdict(list)
        
        for rule_id, rule in rules.items():
            if rule.pattern:
                # Normalize pattern for grouping
                normalized_pattern = self._normalize_pattern(rule.pattern)
                pattern_groups[normalized_pattern].append((rule_id, rule))
        
        # Check for action contradictions within groups
        for pattern, rule_list in pattern_groups.items():
            if len(rule_list) > 1:
                actions = [(rule_id, rule.action) for rule_id, rule in rule_list]
                unique_actions = set(action for _, action in actions)
                
                if len(unique_actions) > 1 and self._has_contradictory_actions(unique_actions):
                    rule_ids = [rule_id for rule_id, _ in actions]
                    
                    conflict = PolicyConflict(
                        conflict_id=f"contradiction_{'_'.join(rule_ids)}",
                        conflict_type=ConflictType.CONTRADICTORY_ACTIONS,
                        rule_ids=rule_ids,
                        description=f"Rules with similar patterns have contradictory actions: {unique_actions}",
                        impact_assessment="Creates inconsistent policy enforcement",
                        resolution_suggestions=[
                            "Consolidate rules with consistent action",
                            "Add more specific matching criteria",
                            "Implement rule precedence hierarchy"
                        ],
                        confidence_score=0.9,
                        detected_at=datetime.now().isoformat()
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_scope_conflicts(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """Detect conflicting endpoint/applies_to scopes."""
        conflicts = []
        
        for rule_id_1, rule_1 in rules.items():
            for rule_id_2, rule_2 in rules.items():
                if rule_id_1 >= rule_id_2:  # Avoid duplicate checks
                    continue
                
                # Check endpoint scope conflicts
                if (rule_1.endpoints and rule_2.endpoints and 
                    rule_1.action != rule_2.action):
                    
                    overlapping_endpoints = self._find_overlapping_endpoints(
                        rule_1.endpoints, rule_2.endpoints
                    )
                    
                    if overlapping_endpoints:
                        conflict = PolicyConflict(
                            conflict_id=f"scope_{rule_id_1}_{rule_id_2}",
                            conflict_type=ConflictType.SCOPE_CONFLICTS,
                            rule_ids=[rule_id_1, rule_id_2],
                            description=f"Rules have overlapping endpoint scopes with different actions: {overlapping_endpoints}",
                            impact_assessment="Ambiguous policy enforcement for shared endpoints",
                            resolution_suggestions=[
                                "Refine endpoint scope definitions",
                                "Establish clear precedence rules",
                                "Add additional filtering criteria"
                            ],
                            confidence_score=0.8,
                            detected_at=datetime.now().isoformat()
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def _detect_redundant_rules(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """Detect redundant or duplicate rules."""
        conflicts = []
        
        # Use both ML-based and heuristic detection for thoroughness
        if ML_AVAILABLE and self.vectorizer:
            conflicts.extend(self._ml_detect_redundancy(rules))
        
        # Always run heuristic detection as well
        conflicts.extend(self._heuristic_detect_redundancy(rules))
        
        return conflicts
    
    def _ml_detect_redundancy(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """ML-based redundancy detection using pattern similarity."""
        conflicts = []
        
        try:
            # Extract rule features for comparison
            rule_texts = []
            rule_ids = []
            
            for rule_id, rule in rules.items():
                # Combine pattern, title, and applies_to for feature extraction
                feature_text = " ".join(filter(None, [
                    rule.pattern or "",
                    rule.title or "",
                    " ".join(rule.applies_to or [])
                ]))
                
                if feature_text.strip():
                    rule_texts.append(feature_text)
                    rule_ids.append(rule_id)
            
            if len(rule_texts) < 2:
                return conflicts
            
            # Calculate similarity matrix
            tfidf_matrix = self.vectorizer.fit_transform(rule_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find highly similar rule pairs
            for i in range(len(rule_ids)):
                for j in range(i+1, len(rule_ids)):
                    similarity_score = similarity_matrix[i][j]
                    
                    if similarity_score > self.similarity_threshold:
                        rule_1 = rules[rule_ids[i]]
                        rule_2 = rules[rule_ids[j]]
                        
                        # Check if they have same action (indicating redundancy)
                        if rule_1.action == rule_2.action:
                            conflict = PolicyConflict(
                                conflict_id=f"redundant_{rule_ids[i]}_{rule_ids[j]}",
                                conflict_type=ConflictType.REDUNDANT_RULES,
                                rule_ids=[rule_ids[i], rule_ids[j]],
                                description=f"Rules are highly similar and may be redundant (similarity: {similarity_score:.3f})",
                                impact_assessment="Unnecessary complexity and maintenance overhead",
                                resolution_suggestions=[
                                    "Merge rules into single comprehensive rule",
                                    "Remove the less specific rule",
                                    "Differentiate rules with additional criteria"
                                ],
                                confidence_score=similarity_score,
                                detected_at=datetime.now().isoformat()
                            )
                            conflicts.append(conflict)
            
        except Exception as e:
            logger.warning(f"ML-based redundancy detection failed: {e}")
            
        return conflicts
    
    def _heuristic_detect_redundancy(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """Heuristic-based redundancy detection."""
        conflicts = []
        
        # Simple pattern matching for redundancy
        rules_list = list(rules.items())
        for i, (rule_id_1, rule_1) in enumerate(rules_list):
            for rule_id_2, rule_2 in rules_list[i+1:]:
                
                # Check for exact pattern matches with same action
                if (rule_1.pattern and rule_2.pattern and 
                    rule_1.pattern == rule_2.pattern and
                    rule_1.action == rule_2.action):
                    
                    conflict = PolicyConflict(
                        conflict_id=f"duplicate_{rule_id_1}_{rule_id_2}",
                        conflict_type=ConflictType.REDUNDANT_RULES,
                        rule_ids=[rule_id_1, rule_id_2],
                        description="Rules have identical patterns and actions",
                        impact_assessment="Duplicate processing and maintenance overhead",
                        resolution_suggestions=[
                            "Remove duplicate rule",
                            "Consolidate into single rule"
                        ],
                        confidence_score=1.0,
                        detected_at=datetime.now().isoformat()
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_precedence_issues(self, rules: Dict[str, Rule]) -> List[PolicyConflict]:
        """Detect rule precedence and ordering issues."""
        conflicts = []
        
        # Analyze rules that might have precedence conflicts
        # Rules processed in dictionary order, so check for logical ordering issues
        
        rule_list = list(rules.items())
        
        for i, (rule_id_1, rule_1) in enumerate(rule_list):
            for j, (rule_id_2, rule_2) in enumerate(rule_list[i+1:], i+1):
                
                # Check if a more specific rule comes after a general one
                if self._is_more_specific(rule_2, rule_1):
                    # More specific rule comes after general rule - potential precedence issue
                    
                    if self._patterns_overlap(rule_1.pattern, rule_2.pattern):
                        conflict = PolicyConflict(
                            conflict_id=f"precedence_{rule_id_1}_{rule_id_2}",
                            conflict_type=ConflictType.PRECEDENCE_ISSUES,
                            rule_ids=[rule_id_1, rule_id_2],
                            description=f"More specific rule '{rule_id_2}' may be overshadowed by general rule '{rule_id_1}'",
                            impact_assessment="Specific rule may never be triggered",
                            resolution_suggestions=[
                                f"Move rule '{rule_id_2}' before '{rule_id_1}'",
                                "Add more specific constraints to general rule",
                                "Review rule evaluation order"
                            ],
                            confidence_score=0.7,
                            detected_at=datetime.now().isoformat()
                        )
                        conflicts.append(conflict)
        
        return conflicts
    
    def generate_policy_recommendations(self, 
                                      rules: Dict[str, Rule],
                                      performance_data: Dict[str, Any] = None,
                                      compliance_requirements: List[str] = None) -> List[PolicyRecommendation]:
        """Generate intelligent policy optimization recommendations."""
        logger.info("Generating intelligent policy recommendations")
        
        recommendations = []
        
        # 1. Performance-based optimization recommendations
        if performance_data:
            recommendations.extend(self._generate_performance_recommendations(rules, performance_data))
        
        # 2. Security enhancement recommendations
        recommendations.extend(self._generate_security_recommendations(rules))
        
        # 3. Compliance alignment recommendations
        if compliance_requirements:
            recommendations.extend(self._generate_compliance_recommendations(rules, compliance_requirements))
        
        # 4. Pattern optimization recommendations
        recommendations.extend(self._generate_pattern_optimization_recommendations(rules))
        
        # 5. Coverage improvement recommendations
        recommendations.extend(self._generate_coverage_recommendations(rules))
        
        self.recommendations_generated = recommendations
        logger.info(f"Generated {len(recommendations)} policy recommendations")
        
        return recommendations
    
    def _generate_performance_recommendations(self, 
                                           rules: Dict[str, Rule], 
                                           performance_data: Dict[str, Any]) -> List[PolicyRecommendation]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        for rule_id, metrics in performance_data.items():
            if rule_id not in rules:
                continue
                
            rule = rules[rule_id]
            
            # High false positive rate recommendation
            if metrics.get('false_positive_rate', 0) > 0.3:
                recommendation = PolicyRecommendation(
                    recommendation_id=f"perf_fp_{rule_id}",
                    recommendation_type=RecommendationType.PERFORMANCE_TUNING,
                    priority=RecommendationPriority.HIGH,
                    title=f"Reduce False Positives in Rule {rule_id}",
                    description=f"Rule has high false positive rate ({metrics['false_positive_rate']:.1%})",
                    affected_rules=[rule_id],
                    suggested_changes={
                        "pattern": "Make pattern more specific",
                        "min_count": "Increase minimum occurrence threshold",
                        "context_filters": "Add contextual filtering"
                    },
                    rationale="High false positive rates reduce user trust and system effectiveness",
                    expected_impact="Improved accuracy and user experience",
                    confidence_score=0.8,
                    created_at=datetime.now().isoformat(),
                    implementation_steps=[
                        "Analyze false positive cases",
                        "Refine pattern specificity", 
                        "Add contextual constraints",
                        "Test with historical data"
                    ]
                )
                recommendations.append(recommendation)
            
            # Low effectiveness recommendation
            if metrics.get('effectiveness_score', 1.0) < 0.6:
                recommendation = PolicyRecommendation(
                    recommendation_id=f"perf_eff_{rule_id}",
                    recommendation_type=RecommendationType.OPTIMIZATION,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"Improve Rule Effectiveness: {rule_id}",
                    description=f"Rule shows low effectiveness score ({metrics['effectiveness_score']:.2f})",
                    affected_rules=[rule_id],
                    suggested_changes={
                        "review_pattern": "Review and update detection pattern",
                        "adjust_thresholds": "Optimize detection thresholds",
                        "enhance_context": "Add contextual analysis"
                    },
                    rationale="Low effectiveness indicates suboptimal rule configuration",
                    expected_impact="Better threat detection and policy enforcement",
                    confidence_score=0.7,
                    created_at=datetime.now().isoformat(),
                    implementation_steps=[
                        "Analyze missed detection cases",
                        "Update detection criteria",
                        "Validate against test cases"
                    ]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_security_recommendations(self, rules: Dict[str, Rule]) -> List[PolicyRecommendation]:
        """Generate security enhancement recommendations."""
        recommendations = []
        
        # Check for missing common security patterns
        security_patterns = {
            "api_keys": r"(?i)(api[_-]?key|token|secret)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",
            "passwords": r"(?i)password[\"']?\s*[:=]\s*[\"']?([^\s\"']{8,})",
            "credit_cards": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "social_security": r"\b\d{3}-\d{2}-\d{4}\b",
            "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "ip_addresses": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "urls": r"https?://[^\s<>\"]+",
            "sql_injection": r"(?i)(union|select|insert|update|delete|drop|create|alter)\s+",
            "xss_patterns": r"(?i)<script|javascript:|on\w+\s*=",
            "file_paths": r"(?:[a-zA-Z]:)?[\\\/](?:[^\\\/\n]+[\\\/])*[^\\\/\n]*"
        }
        
        existing_patterns = set()
        for rule in rules.values():
            if rule.pattern:
                existing_patterns.add(rule.pattern.lower())
        
        missing_patterns = []
        for pattern_name, pattern in security_patterns.items():
            # Check if similar pattern exists
            pattern_exists = any(
                pattern_name.replace("_", "") in existing.replace("_", "").replace("-", "") 
                for existing in existing_patterns
            )
            
            if not pattern_exists:
                missing_patterns.append((pattern_name, pattern))
        
        if missing_patterns:
            recommendation = PolicyRecommendation(
                recommendation_id="security_gaps",
                recommendation_type=RecommendationType.SECURITY_ENHANCEMENT,
                priority=RecommendationPriority.HIGH,
                title="Add Missing Security Detection Patterns",
                description=f"Missing detection for common security patterns: {', '.join([p[0] for p in missing_patterns])}",
                affected_rules=[],
                suggested_changes={
                    "new_rules": [
                        {
                            "id": f"SECURITY-{pattern_name.upper()}-1.0",
                            "title": f"Detect {pattern_name.replace('_', ' ').title()}",
                            "pattern": pattern,
                            "action": "flag",
                            "severity": "high"
                        }
                        for pattern_name, pattern in missing_patterns
                    ]
                },
                rationale="Comprehensive security coverage requires detection of common sensitive data patterns",
                expected_impact="Improved security posture and compliance coverage",
                confidence_score=0.9,
                created_at=datetime.now().isoformat(),
                implementation_steps=[
                    "Review organizational security requirements",
                    "Customize patterns for specific context",
                    "Test patterns against sample data",
                    "Deploy incrementally with monitoring"
                ]
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def identify_coverage_gaps(self, 
                             rules: Dict[str, Rule],
                             evaluation_history: List[Dict[str, Any]] = None,
                             compliance_frameworks: List[str] = None) -> List[CoverageGap]:
        """Identify policy coverage gaps and missing protection areas."""
        logger.info("Identifying policy coverage gaps")
        
        gaps = []
        
        # 1. Endpoint coverage gaps
        gaps.extend(self._identify_endpoint_gaps(rules, evaluation_history))
        
        # 2. Content pattern gaps
        gaps.extend(self._identify_content_gaps(rules, evaluation_history))
        
        # 3. Compliance requirement gaps  
        if compliance_frameworks:
            gaps.extend(self._identify_compliance_gaps(rules, compliance_frameworks))
        
        # 4. Temporal coverage gaps
        gaps.extend(self._identify_temporal_gaps(rules, evaluation_history))
        
        self.coverage_gaps_identified = gaps
        logger.info(f"Identified {len(gaps)} coverage gaps")
        
        return gaps
    
    def get_policy_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive policy optimization report."""
        return {
            "report_generated_at": datetime.now().isoformat(),
            "summary": {
                "total_conflicts_detected": len(self.conflicts_detected),
                "total_recommendations": len(self.recommendations_generated),
                "total_coverage_gaps": len(self.coverage_gaps_identified),
                "critical_issues": len([
                    c for c in self.conflicts_detected 
                    if c.confidence_score > 0.8
                ]) + len([
                    r for r in self.recommendations_generated 
                    if r.priority == RecommendationPriority.CRITICAL
                ])
            },
            "conflicts": [asdict(conflict) for conflict in self.conflicts_detected],
            "recommendations": [asdict(rec) for rec in self.recommendations_generated],
            "coverage_gaps": [asdict(gap) for gap in self.coverage_gaps_identified],
            "next_actions": self._generate_next_actions()
        }
    
    # Helper methods
    def _calculate_pattern_overlap(self, pattern1: str, pattern2: str) -> float:
        """Calculate overlap score between two regex patterns."""
        if not pattern1 or not pattern2:
            return 0.0
        
        # Exact match
        if pattern1 == pattern2:
            return 1.0
            
        # Normalize patterns
        norm1 = pattern1.lower().strip()
        norm2 = pattern2.lower().strip()
        
        # Check for substring containment (high overlap indicator)
        if norm1 in norm2 or norm2 in norm1:
            shorter = min(len(norm1), len(norm2))
            longer = max(len(norm1), len(norm2))
            return (shorter / longer) * 0.9
        
        # Convert to sets of n-grams for comparison
        def get_ngrams(s, n=2):  # Use smaller n-grams for better sensitivity
            return set(s[i:i+n] for i in range(len(s) - n + 1))
        
        ngrams1 = get_ngrams(norm1)
        ngrams2 = get_ngrams(norm2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = ngrams1.intersection(ngrams2)
        union = ngrams1.union(ngrams2)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Also check for common regex constructs
        common_constructs = [
            'api', 'key', 'password', 'token', 'secret',
            r'\d', r'\w', r'\s', r'[a-z]', r'[A-Z]', r'[0-9]'
        ]
        
        construct_matches = 0
        for construct in common_constructs:
            if construct in norm1 and construct in norm2:
                construct_matches += 1
        
        construct_bonus = min(0.3, construct_matches * 0.1)
        
        return min(1.0, jaccard + construct_bonus)
    
    def _normalize_pattern(self, pattern: str) -> str:
        """Normalize regex pattern for comparison."""
        # Remove common regex modifiers and normalize
        normalized = re.sub(r'\(\?\w+\)', '', pattern)  # Remove flags
        normalized = re.sub(r'\\[bswdWSD]', '.', normalized)  # Normalize character classes
        return normalized.lower().strip()
    
    def _has_contradictory_actions(self, actions: Set[str]) -> bool:
        """Check if action set contains contradictory actions."""
        # Block vs Allow is contradictory, Flag is compatible with both
        return "block" in actions and "allow" in actions
    
    def _find_overlapping_endpoints(self, endpoints1: List[str], endpoints2: List[str]) -> List[str]:
        """Find overlapping endpoint patterns."""
        overlaps = []
        
        for ep1 in endpoints1:
            for ep2 in endpoints2:
                if ep1 == ep2:
                    overlaps.append(ep1)
                elif self._endpoints_overlap(ep1, ep2):
                    overlaps.append(f"{ep1}↔{ep2}")
        
        return overlaps
    
    def _endpoints_overlap(self, ep1: str, ep2: str) -> bool:
        """Check if two endpoint patterns overlap."""
        # Handle wildcard patterns
        if ep1.endswith("/*") and ep2.startswith(ep1[:-2]):
            return True
        if ep2.endswith("/*") and ep1.startswith(ep2[:-2]):
            return True
        return False
    
    def _is_more_specific(self, rule1: Rule, rule2: Rule) -> bool:
        """Check if rule1 is more specific than rule2."""
        # Simple heuristic: longer pattern = more specific
        pattern1_len = len(rule1.pattern or "")
        pattern2_len = len(rule2.pattern or "")
        
        # More criteria = more specific
        criteria1 = sum([
            bool(rule1.pattern),
            bool(rule1.min_count and rule1.min_count > 1),
            bool(rule1.max_chars),
            bool(rule1.endpoints),
            bool(rule1.applies_to)
        ])
        
        criteria2 = sum([
            bool(rule2.pattern),
            bool(rule2.min_count and rule2.min_count > 1),
            bool(rule2.max_chars),
            bool(rule2.endpoints),
            bool(rule2.applies_to)
        ])
        
        return criteria1 > criteria2 or (criteria1 == criteria2 and pattern1_len > pattern2_len)
    
    def _patterns_overlap(self, pattern1: Optional[str], pattern2: Optional[str]) -> bool:
        """Check if two patterns might match overlapping content."""
        if not pattern1 or not pattern2:
            return False
        
        # Simplified overlap detection
        return self._calculate_pattern_overlap(pattern1, pattern2) > 0.3
    
    def _generate_pattern_optimization_recommendations(self, rules: Dict[str, Rule]) -> List[PolicyRecommendation]:
        """Generate pattern optimization recommendations.""" 
        recommendations = []
        
        # Check for overly broad patterns
        for rule_id, rule in rules.items():
            if rule.pattern and len(rule.pattern) < 10:  # Very short patterns
                recommendation = PolicyRecommendation(
                    recommendation_id=f"pattern_opt_{rule_id}",
                    recommendation_type=RecommendationType.OPTIMIZATION,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"Refine Pattern Specificity: {rule_id}",
                    description="Pattern may be too broad and could cause false positives",
                    affected_rules=[rule_id],
                    suggested_changes={
                        "pattern": "Add more specific constraints and context",
                        "min_count": "Consider minimum occurrence thresholds",
                        "context": "Add contextual filtering"
                    },
                    rationale="Broad patterns often lead to false positives",
                    expected_impact="Reduced false positives and improved accuracy",
                    confidence_score=0.6,
                    created_at=datetime.now().isoformat(),
                    implementation_steps=[
                        "Analyze pattern match examples",
                        "Add boundary conditions",
                        "Test refined pattern"
                    ]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_coverage_recommendations(self, rules: Dict[str, Rule]) -> List[PolicyRecommendation]:
        """Generate coverage improvement recommendations."""
        # Placeholder - would analyze actual coverage gaps
        return []
    
    def _generate_compliance_recommendations(self, 
                                          rules: Dict[str, Rule], 
                                          compliance_requirements: List[str]) -> List[PolicyRecommendation]:
        """Generate compliance alignment recommendations."""
        # Placeholder - would map compliance requirements to rules
        return []
    
    def _identify_endpoint_gaps(self, 
                              rules: Dict[str, Rule], 
                              evaluation_history: Optional[List[Dict[str, Any]]]) -> List[CoverageGap]:
        """Identify endpoint coverage gaps."""
        # Placeholder - would analyze endpoint coverage
        return []
    
    def _identify_content_gaps(self, 
                             rules: Dict[str, Rule], 
                             evaluation_history: Optional[List[Dict[str, Any]]]) -> List[CoverageGap]:
        """Identify content pattern coverage gaps."""
        # Placeholder - would analyze content coverage
        return []
    
    def _identify_compliance_gaps(self, 
                                rules: Dict[str, Rule], 
                                compliance_frameworks: List[str]) -> List[CoverageGap]:
        """Identify compliance requirement gaps."""
        # Placeholder - would map compliance frameworks to coverage
        return []
    
    def _identify_temporal_gaps(self, 
                              rules: Dict[str, Rule], 
                              evaluation_history: Optional[List[Dict[str, Any]]]) -> List[CoverageGap]:
        """Identify temporal coverage gaps."""
        # Placeholder - would analyze time-based coverage patterns
        return []
    
    def _generate_next_actions(self) -> List[str]:
        """Generate recommended next actions based on analysis."""
        actions = []
        
        if self.conflicts_detected:
            critical_conflicts = [c for c in self.conflicts_detected if c.confidence_score > 0.8]
            if critical_conflicts:
                actions.append(f"Resolve {len(critical_conflicts)} critical policy conflicts")
        
        high_priority_recs = [r for r in self.recommendations_generated 
                             if r.priority in [RecommendationPriority.CRITICAL, RecommendationPriority.HIGH]]
        if high_priority_recs:
            actions.append(f"Implement {len(high_priority_recs)} high-priority recommendations")
        
        if self.coverage_gaps_identified:
            actions.append(f"Address {len(self.coverage_gaps_identified)} coverage gaps")
        
        if not actions:
            actions.append("Policy set appears well-optimized. Continue monitoring performance.")
        
        return actions


# Global instance for easy access
_recommendation_engine = None

def get_policy_recommendation_engine(rules_cache: Dict[str, Rule] = None) -> PolicyRecommendationEngine:
    """Get or create the global policy recommendation engine instance."""
    global _recommendation_engine
    
    if _recommendation_engine is None:
        _recommendation_engine = PolicyRecommendationEngine(rules_cache)
    elif rules_cache:
        _recommendation_engine.rules_cache = rules_cache
    
    return _recommendation_engine