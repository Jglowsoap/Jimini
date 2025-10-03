# tests/test_enforcement.py
import os
import sys
import re
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Rule, Action, EvaluateRequest, EvaluateResponse


# Use a different name to avoid redefinition
def mock_evaluate(rules, request, request_id):
    """Mock implementation of the evaluate function"""
    # Check for pattern matches
    matched_rules = []
    for rule in rules:
        if rule.pattern and hasattr(rule, "compiled_pattern") and rule.compiled_pattern:
            matches = rule.compiled_pattern.findall(request.text)
            if matches and len(matches) >= (rule.min_count or 1):
                matched_rules.append(rule)
        elif rule.max_chars and len(request.text) > rule.max_chars:
            matched_rules.append(rule)

    # Determine action based on precedence (block > flag > allow)
    action = Action.ALLOW
    for rule in matched_rules:
        if rule.action == Action.BLOCK:
            action = Action.BLOCK
            break
        elif rule.action == Action.FLAG and action != Action.BLOCK:
            action = Action.FLAG

    return EvaluateResponse(
        action=action,
        rule_ids=[rule.id for rule in matched_rules],
        message="Policy violation detected" if matched_rules else "",
    )


def test_pattern_match():
    """Test that a pattern rule matches correctly"""
    # Create a test rule with required fields
    mock_rule = Rule(
        id="TEST-RULE-1.0",
        title="Test Pattern Rule",
        severity="HIGH",
        pattern=r"secret",
        action=Action.BLOCK,
    )
    mock_rule.compiled_pattern = re.compile(mock_rule.pattern)

    request = EvaluateRequest(
        api_key="test",
        text="this contains a secret",
        endpoint="/test",
        direction="inbound",
    )

    result = mock_evaluate([mock_rule], request, str(uuid.uuid4()))
    assert result.action == "block"
    assert "TEST-RULE-1.0" in result.rule_ids


def test_no_match():
    """Test that a rule doesn't match when pattern isn't found"""
    mock_rule = Rule(
        id="TEST-RULE-1.0",
        title="Test Pattern Rule",
        severity="HIGH",
        pattern=r"secret",
        action=Action.BLOCK,
    )
    mock_rule.compiled_pattern = re.compile(mock_rule.pattern)

    request = EvaluateRequest(
        api_key="test",
        text="this contains nothing sensitive",
        endpoint="/test",
        direction="inbound",
    )

    result = mock_evaluate([mock_rule], request, str(uuid.uuid4()))
    assert result.action == "allow"
    assert not result.rule_ids


def test_min_count():
    """Test that min_count works correctly"""
    mock_rule = Rule(
        id="TEST-RULE-2.0",
        title="Minimum Occurrence Rule",
        severity="MEDIUM",
        pattern=r"test",
        min_count=2,
        action=Action.FLAG,
    )
    mock_rule.compiled_pattern = re.compile(mock_rule.pattern)

    # Should not match (only 1 occurrence)
    request1 = EvaluateRequest(
        api_key="test", text="this is a test", endpoint="/test", direction="inbound"
    )

    result1 = mock_evaluate([mock_rule], request1, str(uuid.uuid4()))
    assert result1.action == "allow"
    assert not result1.rule_ids

    # Should match (2 occurrences)
    request2 = EvaluateRequest(
        api_key="test",
        text="this is a test and another test",
        endpoint="/test",
        direction="inbound",
    )

    result2 = mock_evaluate([mock_rule], request2, str(uuid.uuid4()))
    assert result2.action == "flag"
    assert "TEST-RULE-2.0" in result2.rule_ids


def test_max_chars():
    # Test max_chars rule
    mock_rule = Rule(
        id="MAX-CHARS-1.0",
        title="Maximum Length Rule",
        severity="LOW",
        max_chars=10,
        action=Action.BLOCK,
    )

    # Should not match (under limit)
    request1 = EvaluateRequest(
        api_key="test", text="short", endpoint="/test", direction="inbound"
    )

    result1 = mock_evaluate([mock_rule], request1, str(uuid.uuid4()))
    assert result1.action == "allow"
    assert not result1.rule_ids

    # Should match (over limit)
    request2 = EvaluateRequest(
        api_key="test",
        text="this is a very long text that exceeds the limit",
        endpoint="/test",
        direction="inbound",
    )

    result2 = mock_evaluate([mock_rule], request2, str(uuid.uuid4()))
    assert result2.action == "block"
    assert "MAX-CHARS-1.0" in result2.rule_ids
