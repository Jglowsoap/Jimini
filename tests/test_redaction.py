# tests/test_redaction.py
import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Rule
from app.enforcement import evaluate


def test_redaction_email():
    """Test that email redaction works correctly"""
    # Create a redaction rule for emails
    email_rule = Rule(
        id="TEST-EMAIL-REDACT-1.0",
        title="Test Email Redaction",
        severity="medium",
        category="pii",
        pattern=r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',
        action="redact",
        applies_to=["user_prompt"],
    )
    
    # Compile the pattern
    email_rule.compiled_pattern = re.compile(email_rule.pattern)
    
    # Create rules store
    rules_store = {
        email_rule.id: (email_rule, email_rule.compiled_pattern)
    }
    
    # Test text with email
    test_text = "Contact me at john.doe@example.com for more info"
    
    # Evaluate
    decision, rule_ids, enforce_shadow, redacted_text = evaluate(
        text=test_text,
        agent_id="test",
        rules_store=rules_store,
        direction="user_prompt",
        endpoint="/test"
    )
    
    # Assertions
    assert decision == "redact", f"Expected 'redact' but got '{decision}'"
    assert email_rule.id in rule_ids, f"Expected {email_rule.id} in {rule_ids}"
    assert redacted_text is not None, "Expected redacted_text to be set"
    assert "[REDACTED]" in redacted_text, f"Expected [REDACTED] in '{redacted_text}'"
    assert "john.doe@example.com" not in redacted_text, "Email should be redacted"
    print(f"✓ Redaction test passed: '{test_text}' → '{redacted_text}'")


def test_redaction_multiple_matches():
    """Test redaction with multiple matches"""
    email_rule = Rule(
        id="TEST-EMAIL-REDACT-2.0",
        title="Test Multiple Email Redaction",
        severity="medium",
        category="pii",
        pattern=r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',
        action="redact",
        applies_to=["user_prompt"],
    )
    
    email_rule.compiled_pattern = re.compile(email_rule.pattern)
    rules_store = {email_rule.id: (email_rule, email_rule.compiled_pattern)}
    
    test_text = "Email alice@test.com or bob@example.org for details"
    
    decision, rule_ids, enforce_shadow, redacted_text = evaluate(
        text=test_text,
        agent_id="test",
        rules_store=rules_store,
        direction="user_prompt",
        endpoint="/test"
    )
    
    assert decision == "redact"
    assert redacted_text is not None
    assert redacted_text.count("[REDACTED]") == 2, "Should redact both emails"
    assert "alice@test.com" not in redacted_text
    assert "bob@example.org" not in redacted_text
    print(f"✓ Multiple redaction test passed: '{test_text}' → '{redacted_text}'")


def test_redaction_precedence():
    """Test that redaction has correct precedence (block > redact > flag)"""
    block_rule = Rule(
        id="TEST-BLOCK-1.0",
        title="Test Block Rule",
        severity="critical",
        category="secrets",
        pattern=r'\bsk-[A-Za-z0-9]{20,}\b',
        action="block",
        applies_to=["user_prompt"],
    )
    
    redact_rule = Rule(
        id="TEST-REDACT-1.0",
        title="Test Redact Rule",
        severity="medium",
        category="pii",
        pattern=r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',
        action="redact",
        applies_to=["user_prompt"],
    )
    
    block_rule.compiled_pattern = re.compile(block_rule.pattern)
    redact_rule.compiled_pattern = re.compile(redact_rule.pattern)
    
    rules_store = {
        block_rule.id: (block_rule, block_rule.compiled_pattern),
        redact_rule.id: (redact_rule, redact_rule.compiled_pattern)
    }
    
    # Test with both block and redact matches - block should win
    test_text = "My email is user@test.com and API key is sk-1234567890abcdefghij"
    
    decision, rule_ids, enforce_shadow, redacted_text = evaluate(
        text=test_text,
        agent_id="test",
        rules_store=rules_store,
        direction="user_prompt",
        endpoint="/test"
    )
    
    assert decision == "block", f"Block should take precedence over redact, got {decision}"
    assert block_rule.id in rule_ids
    assert redact_rule.id in rule_ids
    print(f"✓ Precedence test passed: block takes precedence over redact")


def test_no_redaction_when_no_match():
    """Test that redacted_text is None when no redaction occurs"""
    redact_rule = Rule(
        id="TEST-REDACT-3.0",
        title="Test No Redaction",
        severity="medium",
        category="pii",
        pattern=r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',
        action="redact",
        applies_to=["user_prompt"],
    )
    
    redact_rule.compiled_pattern = re.compile(redact_rule.pattern)
    rules_store = {redact_rule.id: (redact_rule, redact_rule.compiled_pattern)}
    
    test_text = "This text has no sensitive information"
    
    decision, rule_ids, enforce_shadow, redacted_text = evaluate(
        text=test_text,
        agent_id="test",
        rules_store=rules_store,
        direction="user_prompt",
        endpoint="/test"
    )
    
    assert decision == "allow"
    assert len(rule_ids) == 0
    assert redacted_text is None, "redacted_text should be None when no redaction occurs"
    print(f"✓ No redaction test passed: redacted_text is None")


def test_category_field():
    """Test that category field is properly stored"""
    rule = Rule(
        id="TEST-CATEGORY-1.0",
        title="Test Category",
        severity="high",
        category="injection",
        pattern=r'ignore previous instructions',
        action="block",
        applies_to=["user_prompt"],
    )
    
    assert rule.category == "injection", "Category should be set correctly"
    print(f"✓ Category field test passed")


if __name__ == "__main__":
    print("Running redaction tests...\n")
    test_redaction_email()
    test_redaction_multiple_matches()
    test_redaction_precedence()
    test_no_redaction_when_no_match()
    test_category_field()
    print("\n✅ All redaction tests passed!")
