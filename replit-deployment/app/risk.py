# app/risk.py
from __future__ import annotations
from typing import List, Dict, Tuple, Any

# Simple additive scoring: tune as you learn
SEVERITY_POINTS = {
    "error": 50,
    "warning": 20,
    "info": 5,
}

ACTION_POINTS = {
    "block": 40,
    "flag": 15,
    "allow": 0,
}

# Optional per-rule overrides (ids -> points)
RULE_BONUS = {
    "SSH-PRIVATE-1.0": 50,
    "PGP-PRIVATE-1.0": 50,
    "JWT-1.0": 40,
    "OPENAI-KEY-1.0": 40,
    "GITHUB-TOKEN-1.0": 40,
    "AWS-KEY-1.0": 40,
}


def compute_risk(
    decision: str,
    rule_ids: List[str],
    *,
    rule_index: Dict[
        str, Tuple[Any, Any]
    ],  # Typically Dict[str, Tuple[Rule, Pattern[str] | None]]
) -> int:
    score = ACTION_POINTS.get(decision, 0)
    for rid in rule_ids or []:
        bonus = RULE_BONUS.get(rid, 0)
        score += bonus
        tup = rule_index.get(rid)
        if tup:
            rule = tup[0]
            score += SEVERITY_POINTS.get(getattr(rule, "severity", "info"), 0)
    return score


def bucket(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 40:
        return "medium"
    return "low"
