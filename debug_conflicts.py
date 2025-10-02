#!/usr/bin/env python3

"""Debug script for policy conflict detection."""

import sys
sys.path.insert(0, '/workspaces/Jimini')

from app.intelligence.policy_recommendations import PolicyRecommendationEngine
from app.models import Rule

# Create test engine
engine = PolicyRecommendationEngine()

# Simple test rules that should definitely have conflicts
test_rules = {
    "API-KEY-1.0": Rule(
        id="API-KEY-1.0",
        title="Detect API Keys", 
        severity="high",
        pattern=r"api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",
        action="block",
        applies_to=["request", "response"],
        endpoints=["/api/*"]
    ),
    "DUPLICATE-KEY-1.0": Rule(
        id="DUPLICATE-KEY-1.0",
        title="Duplicate API Key Detection",
        severity="high",
        pattern=r"api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",  # Same pattern
        action="block",  # Same action
        applies_to=["request", "response"],
        endpoints=["/api/*"]
    ),
    "CONFLICTING-KEY-1.0": Rule(
        id="CONFLICTING-KEY-1.0", 
        title="Conflicting API Key Rule",
        severity="medium",
        pattern=r"api[_-]?key[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_-]{20,})",  # Same pattern
        action="allow",  # Different action - conflict!
        applies_to=["request"],
        endpoints=["/api/*"]
    )
}

print("Testing conflict detection...")
print(f"Rules to analyze: {list(test_rules.keys())}")

# Test individual pattern comparisons
api_pattern = test_rules["API-KEY-1.0"].pattern
dup_pattern = test_rules["DUPLICATE-KEY-1.0"].pattern
conflict_pattern = test_rules["CONFLICTING-KEY-1.0"].pattern

print(f"\nPattern comparisons:")
print(f"API pattern: {api_pattern}")
print(f"DUP pattern: {dup_pattern}")
print(f"CON pattern: {conflict_pattern}")
print(f"API == DUP: {api_pattern == dup_pattern}")
print(f"API == CON: {api_pattern == conflict_pattern}")

# Test overlap calculation
overlap_api_dup = engine._calculate_pattern_overlap(api_pattern, dup_pattern)
overlap_api_con = engine._calculate_pattern_overlap(api_pattern, conflict_pattern)

print(f"\nOverlap scores:")
print(f"API vs DUP overlap: {overlap_api_dup}")
print(f"API vs CON overlap: {overlap_api_con}")

# Run full analysis
print("\nRunning full conflict analysis...")
conflicts = engine.analyze_policy_conflicts(test_rules)

print(f"\nTotal conflicts detected: {len(conflicts)}")
for i, conflict in enumerate(conflicts):
    print(f"{i+1}. {conflict.conflict_type.value}: {conflict.rule_ids}")
    print(f"   Description: {conflict.description}")
    print(f"   Confidence: {conflict.confidence_score}")
    print()

# Check specifically for pattern overlaps and redundant rules
overlap_conflicts = [c for c in conflicts if c.conflict_type.value == 'overlapping_patterns']
redundant_conflicts = [c for c in conflicts if c.conflict_type.value == 'redundant_rules']

print(f"Overlapping pattern conflicts: {len(overlap_conflicts)}")
print(f"Redundant rule conflicts: {len(redundant_conflicts)}")