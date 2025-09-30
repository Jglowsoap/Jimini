# app/telemetry.py
from __future__ import annotations
import json
import threading
import time
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Iterable, Tuple

from app.util import now_iso
from app.config import get_config
from app.forwarders import JsonlForwarder, SplunkHECForwarder, ElasticForwarder
from app.notifier import Notifier

@dataclass
class TelemetryEvent:
    """Telemetry event structure for tracking evaluations."""
    ts: str
    endpoint: str             # e.g., /v1/evaluate
    direction: str            # inbound|outbound
    decision: str             # ALLOW|BLOCK|FLAG|SHADOW
    shadow_mode: bool
    rule_ids: Iterable[str]
    request_id: Optional[str] = None
    latency_ms: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None

class Telemetry:
    """
    Phase 3 Telemetry with thread-safe counters and periodic exporters.
    Singleton pattern for application-wide telemetry.
    """
    _instance: Optional['Telemetry'] = None
    _lock = threading.Lock()

    def __init__(self, flush_sec: int = 5):
        self.cfg = get_config()
        self.flush_sec = flush_sec
        self.events: list[TelemetryEvent] = []
        self.counters = Counter()
        self.lock = threading.RLock()
        self.stop_event = threading.Event()

        # Initialize forwarders
        self.forwarders = []
        if self.cfg.siem.jsonl.enabled:
            self.forwarders.append(JsonlForwarder(self.cfg.siem.jsonl.path))
        if self.cfg.siem.splunk_hec.enabled:
            self.forwarders.append(SplunkHECForwarder(
                url=self.cfg.siem.splunk_hec.url,
                token=self.cfg.siem.splunk_hec.token,
                sourcetype=self.cfg.siem.splunk_hec.sourcetype,
                verify=self.cfg.siem.splunk_hec.verify_tls,
            ))
        if self.cfg.siem.elastic.enabled:
            self.forwarders.append(ElasticForwarder(
                url=self.cfg.siem.elastic.url,
                auth=(self.cfg.siem.elastic.basic_auth_user,
                      self.cfg.siem.elastic.basic_auth_pass),
                verify=self.cfg.siem.elastic.verify_tls,
            ))

        self.notifier = Notifier(self.cfg.notifiers)

        # Start background flush thread
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    @classmethod
    def instance(cls) -> "Telemetry":
        """Get or create singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = Telemetry()
            return cls._instance

    def record_event(self, evt: TelemetryEvent):
        """Record a telemetry event and update counters."""
        with self.lock:
            self.events.append(evt)
            # Update counters
            for rule in (evt.rule_ids or []):
                key = (evt.endpoint, evt.direction, rule, evt.decision)
                self.counters[key] += 1

            # Notify on BLOCK/FLAG
            if evt.decision in ("BLOCK", "FLAG"):
                try:
                    self.notifier.notify(evt)
                except Exception as e:
                    print(f"[telemetry] notification error: {e}")

    def snapshot_counters(self) -> Dict[str, int]:
        """Get current counter snapshot."""
        with self.lock:
            return {self._fmt_key(k): v for k, v in self.counters.items()}

    def flush(self):
        """Flush queued events to all forwarders."""
        with self.lock:
            batch = self.events[:]
            self.events.clear()
        
        if not batch:
            return
        
        payloads = [asdict(e) for e in batch]
        for fwd in self.forwarders:
            try:
                fwd.send_many(payloads)
            except Exception as e:
                # Phase 4: add retry logic
                print(f"[telemetry] forwarder {type(fwd).__name__} error: {e}")

    def _loop(self):
        """Background thread loop for periodic flushing."""
        while not self.stop_event.is_set():
            time.sleep(self.flush_sec)
            self.flush()

    def stop(self):
        """Stop telemetry background thread and flush remaining events."""
        self.stop_event.set()
        self.thread.join(timeout=1)
        self.flush()

    @staticmethod
    def _fmt_key(k: Tuple[str, str, str, str]) -> str:
        """Format counter key as string."""
        endpoint, direction, rule, decision = k
        return f"{endpoint}|{direction}|{rule}|{decision}"


# Legacy OTEL support - kept for backward compatibility
import os
from typing import List

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
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        resource = Resource.create({"service.name": "jimini-gateway"})
        provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(span_exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("jimini")
    except Exception:
        _tracer = None

def emit_decision_span(
    *,
    agent_id: str,
    endpoint: Optional[str],
    direction: Optional[str],
    decision: str,
    rule_ids: Iterable[str],
):
    """Legacy OTEL span emission - kept for backward compatibility."""
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
            span.set_attribute("jimini.rule_ids_json", json.dumps(list(rule_ids)))
    except Exception:
        pass

def post_webhook_alert(
    *,
    agent_id: str,
    endpoint: Optional[str],
    direction: Optional[str],
    decision: str,
    rule_ids: List[str],
    excerpt: str,
):
    """Legacy webhook alert - kept for backward compatibility."""
    import requests
    _WEBHOOK_URL = os.getenv("WEBHOOK_URL")
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
