"""
Prometheus Metrics & OpenTelemetry Integration for Jimini Policy Gateway

Provides comprehensive observability with:
- Prometheus metrics endpoint (/v1/metrics/prom)
- OTEL tracing for /v1/evaluate requests
- Custom metrics for decisions, rules, latency, errors
- Enterprise dashboard support
"""

import time
from typing import Dict, Any, Optional
# Optional imports with graceful fallback
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback stubs
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
    def generate_latest(): return ""
    CONTENT_TYPE_LATEST = "text/plain"

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # Fallback stubs
    class trace:
        @staticmethod
        def get_tracer(name): return None
    class FastAPIInstrumentor:
        @staticmethod
        def instrument_app(app): pass

try:
    from fastapi import Response
    import structlog
    logger = structlog.get_logger()
except ImportError:
    import logging
    from fastapi import Response
    logger = logging.getLogger(__name__)

# Prometheus Metrics
jimini_events_total = Counter(
    'jimini_events_total',
    'Total number of policy evaluation events',
    ['decision', 'rule', 'endpoint', 'action']
)

jimini_forwarder_errors_total = Counter(
    'jimini_forwarder_errors_total', 
    'Total forwarder errors by target',
    ['target', 'error_type']
)

jimini_latency_histogram = Histogram(
    'jimini_latency_ms',
    'Policy evaluation latency in milliseconds',
    ['endpoint', 'decision'],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
)

jimini_active_requests = Gauge(
    'jimini_active_requests_total',
    'Number of active policy evaluation requests'
)

jimini_circuit_breaker_state = Gauge(
    'jimini_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

jimini_audit_chain_length = Gauge(
    'jimini_audit_chain_length_total',
    'Current length of audit chain'
)

jimini_rules_loaded = Gauge(
    'jimini_rules_loaded_total',
    'Number of loaded policy rules',
    ['rule_pack']
)

# OpenTelemetry Setup
tracer = trace.get_tracer(__name__)


class MetricsCollector:
    """Centralized metrics collection and reporting."""
    
    def __init__(self):
        self.start_time = time.time()
        self._setup_otel()
    
    def _setup_otel(self):
        """Initialize OpenTelemetry tracing."""
        try:
            trace.set_tracer_provider(TracerProvider())
            otlp_exporter = OTLPSpanExporter(
                endpoint="http://jaeger:14268/api/traces",
                insecure=True
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            logger.info("OTEL tracing initialized successfully")
        except Exception as e:
            logger.warning(f"OTEL setup failed: {e}")
    
    def record_policy_event(self, decision: str, rule_id: str, endpoint: str, action: str):
        """Record a policy evaluation event."""
        jimini_events_total.labels(
            decision=decision,
            rule=rule_id,
            endpoint=endpoint,
            action=action
        ).inc()
        logger.debug(f"Recorded policy event: {decision}/{rule_id}/{endpoint}")
    
    def record_forwarder_error(self, target: str, error_type: str):
        """Record forwarder error."""
        jimini_forwarder_errors_total.labels(
            target=target,
            error_type=error_type
        ).inc()
        logger.warning(f"Recorded forwarder error: {target}/{error_type}")
    
    def record_latency(self, endpoint: str, decision: str, latency_ms: float):
        """Record request latency."""
        jimini_latency_histogram.labels(
            endpoint=endpoint,
            decision=decision
        ).observe(latency_ms)
    
    def increment_active_requests(self):
        """Increment active request counter."""
        jimini_active_requests.inc()
    
    def decrement_active_requests(self):
        """Decrement active request counter."""
        jimini_active_requests.dec()
    
    def update_circuit_breaker_state(self, service: str, state: int):
        """Update circuit breaker state (0=closed, 1=open, 2=half-open)."""
        jimini_circuit_breaker_state.labels(service=service).set(state)
    
    def update_audit_chain_length(self, length: int):
        """Update audit chain length."""
        jimini_audit_chain_length.set(length)
    
    def update_rules_count(self, rule_pack: str, count: int):
        """Update loaded rules count."""
        jimini_rules_loaded.labels(rule_pack=rule_pack).set(count)
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        return generate_latest()
    
    def trace_policy_evaluation(self, request_data: Dict[str, Any]):
        """Create OpenTelemetry span for policy evaluation."""
        with tracer.start_as_current_span("policy_evaluation") as span:
            span.set_attribute("endpoint", request_data.get("endpoint", "unknown"))
            span.set_attribute("text_length", len(request_data.get("text", "")))
            span.set_attribute("request_id", request_data.get("request_id", ""))
            return span


class MetricsMiddleware:
    """FastAPI middleware for automatic metrics collection."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    async def __call__(self, request, call_next):
        """Process request and collect metrics."""
        start_time = time.time()
        self.collector.increment_active_requests()
        
        try:
            response = await call_next(request)
            
            # Record latency
            latency_ms = (time.time() - start_time) * 1000
            endpoint = str(request.url.path)
            
            # Extract decision from response if available
            decision = "unknown"
            if hasattr(response, 'body') and response.status_code == 200:
                try:
                    # This would need to be adapted based on actual response structure
                    decision = getattr(response, 'decision', 'unknown')
                except:
                    pass
            
            self.collector.record_latency(endpoint, decision, latency_ms)
            
            return response
            
        finally:
            self.collector.decrement_active_requests()


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector


async def prometheus_metrics_endpoint():
    """Prometheus metrics endpoint handler."""
    metrics_data = metrics_collector.get_prometheus_metrics()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={"Cache-Control": "no-cache"}
    )


def setup_fastapi_instrumentation(app):
    """Set up FastAPI instrumentation with OpenTelemetry."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OTEL instrumentation enabled")
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {e}")


# Decorators for easy metrics integration
def track_policy_decision(func):
    """Decorator to automatically track policy decisions."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Extract metrics from result
            if hasattr(result, 'decision') and hasattr(result, 'rule_ids'):
                latency_ms = (time.time() - start_time) * 1000
                endpoint = kwargs.get('endpoint', 'unknown')
                
                for rule_id in result.rule_ids:
                    metrics_collector.record_policy_event(
                        decision=result.decision,
                        rule_id=rule_id,
                        endpoint=endpoint,
                        action=result.decision
                    )
                
                metrics_collector.record_latency(endpoint, result.decision, latency_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Policy decision tracking failed: {e}")
            raise
    
    return wrapper


def track_forwarder_operation(target: str):
    """Decorator to track forwarder operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_type = type(e).__name__
                metrics_collector.record_forwarder_error(target, error_type)
                raise
        return wrapper
    return decorator