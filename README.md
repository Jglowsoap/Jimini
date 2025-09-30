[![CI](https://github.com/Jglowsoap/Jimini/actions/workflows/ci.yml/badge.svg)](https://github.com/Jglowsoap/Jimini/actions/workflows/ci.yml)

Jimini — AI Policy Enforcement & Oversight

Jimini is a lightweight AI governance gateway that sits between your agents and the outside world. It acts as a compliance firewall with:

* Rules-as-code (regex, thresholds, direction / endpoint scoping, optional LLM checks)
* Deterministic decisions (block > flag > allow) with a global shadow mode for safe rollout
* Tamper‑evident audit logging (hash‑chained JSONL)
* Built‑in metrics, SARIF export, optional webhook + OpenTelemetry
* CLI tools for linting, testing, and running a local gateway
* Curated rule packs (Illinois, CJIS, HIPAA, PCI, Secrets)

Quick Start
1) Environment
```bash
# Required (auth for /v1/evaluate)
export JIMINI_API_KEY=changeme
export JIMINI_RULES_PATH=policy_rules.yaml    # or packs/cjis/v1.yaml etc.

# Optional: enable LLM-based rules (those with llm_prompt)
export OPENAI_API_KEY=sk-...                  # also: pip install openai

# Optional: shadow mode (always returns allow but includes rule_ids)
export JIMINI_SHADOW=1

# Optional: webhook + telemetry + custom audit path
export WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
export AUDIT_LOG_PATH=logs/audit.jsonl
```

2) Run the API locally
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

3) Health check
```bash
curl -s http://localhost:9000/health | jq
# → {"ok": true, "shadow": true, "loaded_rules": 22}
```

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



Shadow mode: If JIMINI_SHADOW=1 and the decision is block/flag, the HTTP response returns allow but still includes the rule_ids. Use this to pilot Jimini without breaking flows. Per‑rule override: set `shadow_override: enforce` to still enforce.

GET /v1/audit/sarif

Query param: `date_prefix=YYYY-MM-DD` (defaults to today if omitted).

Example:

```bash
curl -s "http://localhost:9000/v1/audit/sarif?date_prefix=$(date +%F)" | jq
```

Response (truncated):

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
{"ok": true, "shadow": false, "loaded_rules": 22}

Rules

Rules are defined in YAML. Jimini supports:

* Regex (`pattern`) with optional `min_count`
* Length threshold (`max_chars`)
* LLM checks (`llm_prompt`) — uses OpenAI if configured (fail‑safe returns False if unavailable)
* Direction scoping (`applies_to`: ["inbound"], ["outbound"])
* Endpoint scoping (`endpoints`: exact, prefix/*, or glob)
* Actions (`allow`, `flag`, `block`)
* Per‑rule shadow override (`shadow_override: enforce`) to enforce even in global shadow mode
* Suppression: generic `API-1.0` secret is automatically removed if a specific secret rule (e.g. `GITHUB-TOKEN-1.0`) also matched (see `app/enforcement.py`).

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

Install (development):
```bash
pip install -r requirements.txt   # server deps
pip install -e .                  # installs jimini CLI (package ships only jimini_cli/)
```

LLM support (rules with `llm_prompt`) requires also:
```bash
pip install openai
```

You now have a `jimini` command with core subcommands:

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

Use them via CLI or set JIMINI_RULES_PATH directly to a pack file.

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
Likely in shadow mode (JIMINI_SHADOW=1). Check `/health`.

LLM rules never trigger
Ensure OPENAI_API_KEY is set, you installed `openai`, and your rule has `llm_prompt`.

Generic secret + specific secret both listed
Jimini suppresses `API-1.0` automatically when a specific secret (e.g. `GITHUB-TOKEN-1.0`) matches. Remove that suppression in `app/enforcement.py` if you want both.

PEP 668 (externally managed env)
If pip refuses to install packages system-wide (Debian/Ubuntu), create a virtualenv:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

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
curl -s "http://localhost:9000/v1/audit/sarif?date_prefix=$(date +%F)" | jq
```


<!-- Add after the existing Phase 2 Features section -->

## Troubleshooting

### Audit Chain Issues

If `jimini verify-audit` reports chain integrity issues:

1. **Check file permissions**: Ensure the process running Jimini has write access to the audit log directory.

2. **Review concurrent writers**: Only one Jimini instance should write to a specific audit log file. Use different `AUDIT_LOG_PATH` values for multiple instances.

3. **Recover from corruption**: If the chain is broken, you can:
   - Archive the current log: `mv logs/audit.jsonl logs/audit.jsonl.broken`
   - Start fresh: Jimini will create a new chain on next evaluate call
   - If needed, manually verify the broken file: `cat logs/audit.jsonl.broken | jq -c 'select(.chain_hash != null)' | jimini verify-raw-audit`

### Shadow Mode Behavior

- When `JIMINI_SHADOW=1`, decisions of `block` and `flag` are returned as `allow` in the API response.
- The `rule_ids` still show which rules would have triggered in enforce mode.
- Individual rules can override shadow with `shadow_override: enforce` in YAML to always enforce.

### Telemetry Opt-In

Jimini follows a strict opt-in approach to telemetry and external services:

- **OpenTelemetry**: Only enabled when `OTEL_EXPORTER_OTLP_ENDPOINT` is set
- **Webhooks**: Only triggered when `WEBHOOK_URL` is configured
- **LLM Rules**: Only activated when `OPENAI_API_KEY` is provided
- **Default Mode**: No outbound calls unless explicitly configured

## Security Best Practices

1. **API Key Management**: Rotate `JIMINI_API_KEY` regularly. Use secrets management rather than environment files in production.

2. **Rule Development Workflow**:
   - Test rules locally: `jimini test --rule-pack cjis --text "sample text"`
   - Lint before deployment: `jimini lint --rules policy_rules.yaml`
   - Audit your audit: `jimini verify-audit` should be part of your monitoring

3. **Shadow-First Deployment**:
   - Start with `JIMINI_SHADOW=1` in production
   - Monitor rule hit rates for 1-2 weeks
   - Apply `shadow_override: enforce` to high-confidence rules first
   - Graduate to full enforcement (`JIMINI_SHADOW=0`) after tuning