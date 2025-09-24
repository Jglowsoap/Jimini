[![CI](https://github.com/Jglowsoap/Jimini/actions/workflows/ci.yml/badge.svg)](https://github.com/Jglowsoap/Jimini/actions/workflows/ci.yml)

Jimini — AI Policy Enforcement & Oversight

Jimini is a lightweight AI governance gateway that sits between your agents and the outside world. It acts as a compliance firewall with:

Rules-as-code (regex, thresholds, direction/endpoint scoping, LLM checks)

Strict decisions (block > flag > allow) with shadow mode for safe rollout

Audit logging (tamper-evident hash chained)

CLI tools for local testing, linting, and running a local gateway

Rule packs for regulated domains (Illinois, CJIS, HIPAA, PCI, Secrets)

Quick Start
1) Environment
# Required
export API_KEY=changeme
export RULES_PATH=policy_rules.yaml        # or a pack file (see below)

# Optional (enables LLM checks if your rules use llm_prompt)
export OPENAI_API_KEY=sk-...

# Optional (safe rollout: never block/flag; still returns rule_ids)
export JIMINI_SHADOW=1

2) Run the API locally
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

3) Health check
curl -s http://localhost:9000/health
# → {"ok": true, "shadow": true}    # true if JIMINI_SHADOW=1

API
POST /v1/evaluate

Evaluate content with optional context.

Request

{
  "api_key": "changeme",
  "agent_id": "orchestrator-1",
  "text": "Include fingerprint data and ghp_abcdefghijklmnopqrstuvwxyz123456",
  "direction": "outbound",
  "endpoint": "/api/cjis/query"
}


Response

{
  "decision": "block",
  "rule_ids": ["GITHUB-TOKEN-1.0","CJIS-BIOMETRIC-1.0"]
}



Shadow mode: If JIMINI_SHADOW=1 and the decision is block/flag, the HTTP response returns allow but still includes the rule_ids. Use this to pilot Jimini without breaking flows.

GET /v1/audit/verify

Verifies integrity of the local audit log hash chain:

{"valid": true, "break_index": null, "count": 123}

GET /health

Basic health + shadow-mode flag:

## Phase 2 Features

Jimini now includes observability, shadow-mode telemetry, and enterprise-friendly exports.

✅ Metrics Endpoint

Every request is counted by decision, rule, endpoint, and direction.
Recent decisions are tracked in-memory (last 100).

Example:

```bash
curl -s http://localhost:9000/v1/metrics | jq
```

Response:

```json
{
  "shadow_mode": true,
  "totals": { "block": 1 },
  "rules": { "IL-AI-4.2": 1, "EMAIL-1.0": 1 },
  "shadow_overrides": { "block": 1 },
  "endpoints": { "/api/export": 1 },
  "directions": { "outbound": 1 },
  "recent": [
    {
      "agent_id": "cli:test",
      "decision": "block",
      "rule_ids": ["IL-AI-4.2"],
      "excerpt": "SSN 123-45-6789"
    }
  ],
  "loaded_rules": 22
}
```

✅ SARIF Export for SIEM

Jimini can output SARIF logs (Static Analysis Results Interchange Format).
This makes audit events consumable by Splunk, Elastic, and other security tooling.

Example:

```bash
curl -s "http://localhost:9000/v1/audit/sarif?only_today=true" | jq
```

Response (truncated):

```json
{
  "version": "2.1.0",
  "runs": [
    {
      "tool": { "driver": { "name": "Jimini" } },
      "results": [
        {
          "ruleId": "IL-AI-4.2",
          "level": "error",
          "message": {
            "text": "block by IL-AI-4.2 for test_agent"
          }
        }
      ]
    }
  ]
}
```

✅ Shadow Mode with Overrides

Global shadow mode (JIMINI_SHADOW=1) allows you to simulate enforcement.
Requests are evaluated, but blocks/flags are downgraded to allow.

Certain rules can override shadow mode by setting in the YAML:

```yaml
id: GITHUB-TOKEN-1.0
title: GitHub Token
pattern: ghp_[A-Za-z0-9]{36}
action: block
severity: error
shadow_override: enforce
```

✅ Webhook Alerts (Slack/Teams/Discord)

High-severity block decisions can trigger a JSON POST to a webhook.
Configure in .env:

```bash
WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

Alerts look like:

```
[Jimini] decision=block agent_id=cli:test endpoint=/api/export direction=outbound rules=['IL-AI-4.2']
excerpt: SSN 123-45-6789
```

✅ OpenTelemetry Traces (Optional)

If you already run an OTEL collector, Jimini can emit spans.
Enable by setting in .env:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
```

Attributes per span:

- jimini.agent_id
- jimini.endpoint
- jimini.direction
- jimini.decision
- jimini.rule_ids_json

If unset, telemetry is disabled automatically (no performance impact).

✅ CI Workflow

Jimini ships with a ready-to-use GitHub Actions pipeline at `.github/workflows/ci.yml`.

It runs on every push:

```yaml
- run: pip install -r requirements.txt
- run: pip install -e .
- run: PYTHONPATH=$PWD pytest -q
```

Add a badge to the top of your README:

```
![CI](https://github.com/Jglowsoap/Jimini/actions/workflows/ci.yml/badge.svg)
```

📌 With these, Phase 2 is fully wrapped:

You can measure, export, alert, and trace.

All features are opt-in via .env.

Defaults are zero-config, safe, and developer-friendly.
{"ok": true, "shadow": false}

Rules

Rules are defined in YAML. Jimini supports:

Regex (pattern) with optional min_count

Length threshold (max_chars)

LLM checks (llm_prompt) — uses OpenAI if configured, fail-safe otherwise

Direction scoping (applies_to: ["inbound"], ["outbound"], or omit)

Endpoint scoping (endpoints: exact, prefix/*, or glob patterns)

Actions (allow, flag, block)

Per-rule shadow override (shadow_override: "enforce") to still enforce during global shadow mode

Example

rules:
  - id: "CJIS-BIOMETRIC-1.0"
    title: "Biometric data exposure"
    text: "Block biometric terms on CJIS endpoints"
    pattern: "(?i)\\b(fingerprint|mugshot|iris scan|retina scan|dna profile)\\b"
    severity: "error"
    action: "block"
    applies_to: ["outbound"]
    endpoints: ["/api/cjis/*"]
    tags: ["cjis","biometric"]
    shadow_override: "enforce"   # still blocks even if JIMINI_SHADOW=1

  - id: "GITHUB-TOKEN-1.0"
    title: "GitHub Personal Access Token"
    pattern: "\\bghp_[A-Za-z0-9]{36}\\b"
    severity: "error"
    action: "block"
    tags: ["secret","github"]

  - id: "API-1.0"
    title: "Generic long secret"
    text: "Flag long alphanumeric blobs; specific secret rules block"
    pattern: "\\b[A-Za-z0-9_\\-]{20,}\\b"
    severity: "warning"
    action: "flag"
    tags: ["security","credentials"]


Jimini suppresses API-1.0 in results if a specific secret rule (e.g., GITHUB-TOKEN-1.0) also matched. This keeps rule_ids clean.

CLI

Install editable (already set up in this repo):

pip install -e .


You now have a jimini command with three core subcommands:

1) jimini lint

Validate a rule file or a rule pack:

jimini lint --rules policy_rules.yaml
# or
jimini lint --rule-pack cjis

2) jimini test

Run the engine locally on sample text:

jimini test --rules policy_rules.yaml \
  --text "jane.doe@example.com" \
  --direction outbound \
  --endpoint /api/coordinator/chat \
  --format table

# JSON or SARIF output:
jimini test --rule-pack cjis --text "fingerprint" --format sarif


Add --shadow to simulate (always exits 0 even if it would block).

3) jimini run-local

Boot a local API using a rules file or pack:

# From a rules file
jimini run-local --rules policy_rules.yaml --port 9000 --shadow

# From a rule pack (versioned)
jimini run-local --rule-pack cjis --version v1 --port 9000

Rule Packs

Built-in packs live under packs/ and are versioned (e.g., packs/cjis/v1.yaml). Examples:

illinois — Illinois AI Policy basics (SSN, IL DL/ID, email, etc.)

cjis — CJIS-sensitive patterns and endpoints

hipaa — PHI/PII basics for healthcare

pci — PAN basics

secrets — Common provider secrets (GitHub, AWS, OpenAI, Slack, JWT…)

Use them via CLI or set RULES_PATH directly to a pack file.

Auditing

Every evaluation produces an AuditRecord:

timestamp (UTC, ISO8601)

agent_id

decision

rule_ids

excerpt (first 200 chars)

Audit entries are hash chained to detect tampering.

Verify chain: jimini verify-audit

API: GET /v1/audit/verify

Integration Pattern (Example: Flask/Claude)

Inbound request → clean → call Jimini → decide → proceed/block.

# pseudo-code
verdict_in  = gate_with_jimini(
    agent_id=f"user:{user_id}",
    text=user_text,
    direction="inbound",
    endpoint="/api/coordinator/chat"
)

# ... run your model/agents ...

verdict_out = gate_with_jimini(
    agent_id="agent:orchestrator",
    text=model_output,
    direction="outbound",
    endpoint="/api/coordinator/chat"
)


If decision == "block" → stop, log, optionally raise a ticket (ServiceNow/Jira).

If decision == "flag" → allow with warning or require reviewer approval.

If JIMINI_SHADOW=1 → you’ll always get "allow" back, but with rule_ids for analysis.

Troubleshooting

decision: allow but rules listed
You’re likely in shadow mode (JIMINI_SHADOW=1). Check /health.

LLM rules never trigger
Ensure OPENAI_API_KEY is set and your rule has llm_prompt. Jimini fails safe (returns False) if the LLM cannot be called.

Generic secret + specific secret both listed
By design Jimini suppresses API-1.0 if a specific secret also matched. If you want the generic to remain, remove that suppression block in app/enforcement.py.

Roadmap

SARIF/OTEL exports; Splunk/Elastic/Sentinel connectors

Multi-layer approval workflow (auto-create ServiceNow/Jira tickets)

Drift detection & rule tuning suggestions

MCP/Function-call gating with signed short-lived exec tokens

Policy-aware routing (risk → model/provider selection)

License

### Run locally (shadow mode)
```bash
jimini run-local --rules policy_rules.yaml --port 9000 --shadow
# health
curl -s http://localhost:9000/health | jq
# metrics
curl -s http://localhost:9000/v1/metrics | jq
# sarif (today)
curl -s "http://localhost:9000/v1/audit/sarif?only_today=true" | jq
````
