# app/router.py
from __future__ import annotations
import os

SECURE_MODEL = os.getenv("SECURE_MODEL", "gpt-4o")        # e.g., private/VPC or Bedrock titan
STANDARD_MODEL = os.getenv("STANDARD_MODEL", "gpt-4o-mini")

def choose_lane(risk_level: str) -> str:
    """
    Return which lane to use. For now just "secure" or "standard".
    """
    return "secure" if risk_level in ("high",) else "standard"

def resolve_model(lane: str) -> str:
    return SECURE_MODEL if lane == "secure" else STANDARD_MODEL
