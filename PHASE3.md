# Phase 3: Telemetry & Integration Guide

## Overview

Phase 3 adds comprehensive telemetry, SIEM integration, and shadow mode with overrides to Jimini.

## Features

### 1. Configuration (YAML + .env)

Create a `jimini.config.yaml` file with:

```yaml
app:
  env: dev
  shadow_mode: true  # evaluate but don't enforce (except overrides)
  shadow_overrides:   # rules that ALWAYS enforce even in shadow mode
    - "IL-AI-1.1"
    - "SECRETS-EXFIL"

notifiers:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#jimini-alerts"
    username: "Jimini"
    icon_emoji: ":shield:"

  teams:
    enabled: false
    webhook_url: "${TEAMS_WEBHOOK_URL}"

siem:
  jsonl:
    enabled: true
    path: "logs/jimini_events.jsonl"

  splunk_hec:
    enabled: false
    url: "https://splunk.example.com:8088/services/collector"
    token: "${SPLUNK_HEC_TOKEN}"
    sourcetype: "jimini:event"
    verify_tls: true

  elastic:
    enabled: false
    url: "https://elastic.example.com:9200/jimini-events/_doc"
    basic_auth_user: "${ELASTIC_USER}"
    basic_auth_pass: "${ELASTIC_PASS}"
    verify_tls: true

otel:
  enabled: false
  endpoint: "${OTEL_EXPORTER_OTLP_ENDPOINT}"
  service_name: "jimini"
  resource:
    environment: "dev"
```

Environment variables (`.env`):

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TEAMS_WEBHOOK_URL=...
SPLUNK_HEC_TOKEN=...
ELASTIC_USER=...
ELASTIC_PASS=...
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 2. Telemetry

Thread-safe counters and periodic exporters track all evaluation events:

- **Counters**: Track decisions by (endpoint, direction, rule, decision)
- **Events**: Full event data with timestamps, latency, request IDs
- **Export**: Periodic flush to JSONL, Splunk HEC, Elasticsearch

### 3. Notifiers

Automatic alerts on BLOCK/FLAG events:

- **Slack**: Incoming webhook integration
- **Teams**: Microsoft Teams webhook
- Fire-and-forget (non-blocking)

### 4. SIEM Forwarders

#### JSONL
Always available, writes to local file:
```json
{
  "ts": "2025-09-30T16:10:05.123Z",
  "endpoint": "/v1/evaluate",
  "direction": "outbound",
  "decision": "BLOCK",
  "shadow_mode": true,
  "rule_ids": ["SECRETS-EXFIL"],
  "request_id": "req_abc123",
  "latency_ms": 12.5,
  "meta": {"raw_decision": "BLOCK"}
}
```

#### Splunk HEC
Send events to Splunk HTTP Event Collector:
```spl
sourcetype="jimini:event" decision=BLOCK | stats count by rule_ids{}
```

#### Elasticsearch
Index events in Elasticsearch for Kibana visualization.

### 5. Shadow Mode with Overrides

- **Shadow Mode (`shadow_mode: true`)**: Evaluate but don't enforce (decisions become ALLOW)
- **Shadow Overrides**: Specific rules that ALWAYS enforce even in shadow mode
- **Use Case**: Test new rules in production without blocking legitimate traffic

Example:
```yaml
app:
  shadow_mode: true
  shadow_overrides:
    - "IL-AI-1.1"  # Always enforce this critical rule
```

### 6. CLI Commands

```bash
# View telemetry counters
jimini telemetry counters

# Force flush events to forwarders
jimini telemetry flush

# Tail JSONL events in real-time
jimini telemetry tail --file logs/jimini_events.jsonl
```

## Usage Examples

### Basic Setup

1. Create `jimini.config.yaml` (see above)
2. Set environment variables in `.env`
3. Start the server:

```bash
uvicorn app.main:app --reload
```

### Testing Shadow Mode

```bash
# Enable shadow mode
export JIMINI_SHADOW=1

# Make a request that would normally block
curl -X POST http://localhost:8000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key",
    "agent_id": "test-agent",
    "text": "SSN: 123-45-6789",
    "direction": "outbound"
  }'

# Result: decision="allow" (but telemetry shows it would have blocked)
```

### Viewing Telemetry

```bash
# Check counters
jimini telemetry counters

# Output:
{
  "/v1/evaluate|outbound|IL-AI-4.2|BLOCK": 5,
  "/v1/evaluate|outbound|EMAIL-1.0|FLAG": 12
}
```

### JSONL Tailing

```bash
jimini telemetry tail
```

Output:
```
{"ts": "2025-09-30T16:10:05.123Z", "decision": "BLOCK", ...}
{"ts": "2025-09-30T16:10:06.456Z", "decision": "FLAG", ...}
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific Phase 3 tests
pytest tests/test_config.py
pytest tests/test_telemetry.py
pytest tests/test_forwarders.py
pytest tests/test_notifier.py
pytest tests/test_shadow_override.py
```

## Architecture

### Telemetry Flow

```
Request → /v1/evaluate → Evaluate → Record Event → Periodic Flush → Forwarders
                                          ↓
                                      Counters
                                          ↓
                                      Notifiers (on BLOCK/FLAG)
```

### Thread Safety

- Telemetry uses `threading.RLock()` for thread-safe operations
- Background daemon thread flushes events every 5 seconds
- Non-blocking webhook notifications

## Next Steps (Phase 4)

- Retry logic for forwarders
- Bulk API for Elasticsearch
- OpenTelemetry metrics integration
- Advanced dashboards and alerting
