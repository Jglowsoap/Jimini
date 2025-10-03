# app/otel.py
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Dict, Any, Iterator

_OTEL_ENABLED = False
_tracer = None


def init_otel() -> None:
    """Initialize OTEL if endpoint is configured. No-op otherwise."""
    global _OTEL_ENABLED, _tracer
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    try:
        # pip install opentelemetry-sdk opentelemetry-exporter-otlp
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider()
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("jimini")
        _OTEL_ENABLED = True
    except Exception:
        # best effort: keep disabled if libs missing
        _OTEL_ENABLED = False
        _tracer = None


@contextmanager
def span(name: str, attributes: Dict[str, Any] | None = None) -> Iterator[None]:
    """Context manager for a span; no-ops if OTEL disabled."""
    if not _OTEL_ENABLED or _tracer is None:
        yield
        return
    s = _tracer.start_span(name)
    try:
        if attributes:
            for k, v in attributes.items():
                try:
                    s.set_attribute(k, v)
                except Exception:
                    pass
        yield
    finally:
        s.end()
