from __future__ import annotations
import json
import os
import threading
import time
import urllib.request
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Iterable, Tuple, List

from config.loader import get_current_config
from app.forwarders.jsonl_forwarder import JsonlForwarder
from app.forwarders.splunk_forwarder import SplunkHECForwarder
from app.forwarders.elastic_forwarder import ElasticForwarder
from app.notifier import Notifier


@dataclass
class TelemetryEvent:
    ts: str
    endpoint: str  # e.g., /v1/evaluate
    direction: str  # inbound|outbound
    decision: str  # ALLOW|BLOCK|FLAG|SHADOW
    shadow_mode: bool
    rule_ids: Iterable[str]
    request_id: Optional[str] = None
    latency_ms: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None


class Telemetry:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, flush_sec: int = 5):
        self.cfg = get_current_config()
        self.flush_sec = flush_sec
        self.events: list[TelemetryEvent] = []
        self.counters = Counter()
        self.lock = threading.RLock()
        self.stop_event = threading.Event()

        # forwarders with new configuration structure
        self.forwarders = []
        if self.cfg.siem.jsonl.enabled:
            self.forwarders.append(JsonlForwarder(self.cfg.siem.jsonl.file_path))
        if self.cfg.siem.splunk.enabled:
            self.forwarders.append(
                SplunkHECForwarder(
                    url=str(self.cfg.siem.splunk.hec_url),
                    token=self.cfg.siem.splunk.hec_token,
                    sourcetype="jimini:event",
                    verify=self.cfg.siem.splunk.verify_tls,
                )
            )
        if self.cfg.siem.elastic.enabled:
            self.forwarders.append(
                ElasticForwarder(
                    url=str(self.cfg.siem.elastic.url),
                    auth=(
                        self.cfg.siem.elastic.username,
                        self.cfg.siem.elastic.password,
                    ) if self.cfg.siem.elastic.username else None,
                    verify=self.cfg.siem.elastic.verify_tls,
                )
            )

        self.notifier = Notifier(self.cfg.notifiers)

        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    @classmethod
    def instance(cls) -> "Telemetry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = Telemetry()
            return cls._instance

    def record_event(self, evt: TelemetryEvent):
        with self.lock:
            self.events.append(evt)
            # counters
            for rule in evt.rule_ids or []:
                key = (evt.endpoint, evt.direction, rule, evt.decision)
                self.counters[key] += 1

            # notify on BLOCK/FLAG
            if evt.decision in ("BLOCK", "FLAG"):
                self.notifier.notify(evt)

    def snapshot_counters(self) -> Dict[str, int]:
        with self.lock:
            return {self._fmt_key(k): v for k, v in self.counters.items()}

    def flush(self):
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
                # In Phase 4 we'll add robust error pipelines/retry
                print(f"[telemetry] forwarder {type(fwd).__name__} error: {e}")

    def _loop(self):
        while not self.stop_event.is_set():
            time.sleep(self.flush_sec)
            self.flush()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=1)
        self.flush()

    @staticmethod
    def _fmt_key(k: Tuple[str, str, str, str]) -> str:
        endpoint, direction, rule, decision = k
        return f"{endpoint}|{direction}|{rule}|{decision}"

    @staticmethod
    def _post_json(url, payload):
        """Post JSON payload to URL."""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as _:
                pass
        except Exception:
            pass


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
            _post_webhook(url, payload)
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()


def _post_webhook(url, payload):
    """Post JSON payload to webhook URL."""
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as _:
            pass
    except Exception:
        # Don't let webhook failures impact the main flow
        pass
