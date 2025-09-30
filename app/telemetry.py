from __future__ import annotations
import os
from typing import Iterable, List, Optional, Any
import json
import threading
import requests  # lightweight dep

# --- Optional OpenTelemetry (zero-config if not installed or not configured) ---
_tracer: Optional[Any] = None
_otel_inited: bool = False


def _init_tracer_once():
    global _tracer, _otel_inited
    if _otel_inited:
        return
    _otel_inited = True
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        _tracer = None
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        resource = Resource.create({"service.name": "jimini-gateway"})
        provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("jimini")
    except Exception:
        _tracer = None  # gracefully disable if anything fails


def emit_decision_span(
    *,
    agent_id: str,
    endpoint: Optional[str],
    direction: Optional[str],
    decision: str,
    rule_ids: Iterable[str],
):
    """
    Emits a single OTEL span for an evaluate() decision when enabled.
    No-ops if OTEL is not configured.
    """
    _init_tracer_once()
    if _tracer is None:
        return
    try:
        with _tracer.start_as_current_span("jimini.evaluate") as span:
            span.set_attribute("jimini.agent_id", agent_id)
            if endpoint:
                span.set_attribute("jimini.endpoint", endpoint)
            if direction:
                span.set_attribute("jimini.direction", direction)
            span.set_attribute("jimini.decision", decision)
            span.set_attribute("jimini.rule_count", len(list(rule_ids)))
            # store rule ids as a JSON string so backends can parse
            span.set_attribute("jimini.rule_ids_json", json.dumps(list(rule_ids)))
    except Exception:
        pass  # never break the request path


# --- Minimal webhook notifier (Slack/Teams/Discord/etc.) ---

_WEBHOOK_URL = os.getenv("WEBHOOK_URL")


def post_webhook_alert(
    *,
    agent_id: str,
    endpoint: Optional[str],
    direction: Optional[str],
    decision: str,
    rule_ids: List[str],
    excerpt: str,
):
    """
    Fire-and-forget notifier. If WEBHOOK_URL is not set, it's a no-op.
    Runs in a short background thread so it doesn't add latency.
    """
    url = _WEBHOOK_URL
    if not url:
        return

    def _send():
        payload = {
            "text": (
                f"[Jimini] decision={decision} agent_id={agent_id} "
                f"endpoint={endpoint or '-'} direction={direction or '-'} "
                f"rules={rule_ids or []}\nexcerpt: {excerpt}"
            )
        }
        try:
            requests.post(url, json=payload, timeout=3)
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()
