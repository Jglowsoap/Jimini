# app/telemetry.py
from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional, Any

# In-memory counters (process-local)
TOTALS: "defaultdict[str, int]" = defaultdict(int)          # allow/flag/block
RULE_HITS: "defaultdict[str, int]" = defaultdict(int)       # rule_id -> count
SHADOW_OVERRIDES: "defaultdict[str, int]" = defaultdict(int) # e.g. "block" when shadow allowed it
ENDPOINTS: "defaultdict[str, int]" = defaultdict(int)       # endpoint -> count
DIRECTIONS: "defaultdict[str, int]" = defaultdict(int)      # inbound/outbound
LAST_N: List[Dict[str, Any]] = []                           # small rolling buffer

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

def push_last(event: Dict[str, Any]) -> None:
    LAST_N.append(event)
    if len(LAST_N) > MAX_LAST:
        del LAST_N[: len(LAST_N) - MAX_LAST]

def snapshot(loaded_rules: int) -> Dict[str, Any]:
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

# ---- OpenTelemetry tracing (lazy, optional) ----
_tracer: Optional[Any] = None

def init_tracing() -> Optional[Any]:
    """
    Initialize OpenTelemetry tracing if OTEL_EXPORTER_OTLP_ENDPOINT is set.
    Returns a tracer (or None if telemetry is disabled or deps missing).
    """
    global _tracer
    if _tracer is not None:
        return _tracer

    import os
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        service_name = os.getenv("OTEL_SERVICE_NAME", "jimini")
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        _tracer = trace.get_tracer(service_name)
        return _tracer
    except Exception:
        _tracer = None
        return None
