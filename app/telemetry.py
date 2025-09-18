# app/telemetry.py
from __future__ import annotations
from collections import defaultdict
from typing import Dict, List

# In-memory counters (process-local)
TOTALS: "defaultdict[str, int]" = defaultdict(int)          # allow/flag/block
RULE_HITS: "defaultdict[str, int]" = defaultdict(int)       # rule_id -> count
SHADOW_OVERRIDES: "defaultdict[str, int]" = defaultdict(int) # e.g. "block" when shadow allowed it
ENDPOINTS: "defaultdict[str, int]" = defaultdict(int)       # endpoint -> count
DIRECTIONS: "defaultdict[str, int]" = defaultdict(int)      # inbound/outbound
LAST_N: List[Dict] = []                                     # small rolling buffer

MAX_LAST = 200

def incr(decision: str, rule_ids: List[str], *, endpoint: str | None, direction: str | None, shadow_overridden: bool):
    TOTALS[decision] += 1
    for rid in rule_ids or []:
        RULE_HITS[rid] += 1
    if shadow_overridden:
        SHADOW_OVERRIDES[decision] += 1
    if endpoint:
        ENDPOINTS[endpoint] += 1
    if direction:
        DIRECTIONS[direction] += 1

def push_last(event: Dict):
    LAST_N.append(event)
    if len(LAST_N) > MAX_LAST:
        del LAST_N[: len(LAST_N) - MAX_LAST]

def snapshot(loaded_rules: int) -> Dict:
    return {
        "shadow_mode": False,  # main.py will set correct value
        "totals": dict(TOTALS),
        "rules": dict(RULE_HITS),
        "shadow_overrides": dict(SHADOW_OVERRIDES),
        "endpoints": dict(ENDPOINTS),
        "directions": dict(DIRECTIONS),
        "recent": LAST_N[-20:],  # last 20 for quick debugging
        "loaded_rules": loaded_rules,
    }
