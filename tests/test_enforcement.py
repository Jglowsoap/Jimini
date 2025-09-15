# tests/test_enforcement.py
import re
from app.enforcement import evaluate

class DummyRule:
    # Mimic only the fields evaluate() inspects
    def __init__(self, action: str):
        self.action = action
        self.applies_to = None
        self.endpoints = None
        self.min_count = None
        self.max_chars = None
        self.llm_prompt = None
        self.shadow_override = None

def test_block_ssn():
    text = "SSN: 123-45-6789"
    # IMPORTANT: single backslashes using a raw string
    rules_store = {
        "IL-AI-4.2": (DummyRule("block"), re.compile(r"\b\d{3}-\d{2}-\d{4}\b"))
    }
    decision, rule_ids, _ = evaluate(text, "test_agent", rules_store)
    assert decision == "block"
    assert "IL-AI-4.2" in rule_ids

def test_allow_no_match():
    text = "No sensitive data here."
    rules_store = {}
    decision, rule_ids, _ = evaluate(text, "test", rules_store) # pyright: ignore[reportUnknownArgumentType]
    assert decision == "allow"
    assert rule_ids == []
