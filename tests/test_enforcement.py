import re
import pytest
from app.enforcement import evaluate

class DummyRule:
    def __init__(self, action):
        self.action = action

def test_block_ssn():
    text = "SSN: 123-45-6789"
    rules_store = {
        "IL-AI-4.2": (DummyRule("block"), re.compile(r"\\b\\d{3}-\\d{2}-\\d{4}\\b"))
    }
    decision, rule_ids = evaluate(text, "test_agent", rules_store)
    assert decision == "block"
    assert rule_ids == ["IL-AI-4.2"]

def test_allow_no_match():
    text = "No sensitive data here."
    rules_store = {}
    decision, rule_ids = evaluate(text, "test", rules_store)
    assert decision == "allow"
    assert rule_ids == []
