# Jimini Architecture

This document describes the concrete building blocks that make up Jimini and how requests flow through the system. The goal is to provide enough detail for contributors and operators without relying on generated diagrams or hypothetical components.

## High-Level Components

- **Gateway (`app/main.py`)**
  - FastAPI application that wires middleware, loads rules on startup, exposes REST endpoints, and publishes metrics.
  - Adds request ID headers, enforces a 10 MB body limit, and respects global shadow mode.

- **Policy Engine (`app/enforcement.py`)**
  - Normalises the evaluation context (direction, endpoint, agent id).
  - Filters rules by `applies_to` and endpoint globbing.
  - Executes regex and threshold checks, optionally running an LLM prompt when `llm_prompt` is configured and an OpenAI API key is available.
  - Returns a decision with rule IDs and writes an `AuditRecord`.

- **Rules Loader (`app/rules_loader.py`)**
  - Parses YAML using Pydantic models (`app/models.py`), compiles regexes, and stores live rules in a shared dictionary.
  - Watches the file system for updates and hot-reloads automatically.
  - Loads token quota tiers used by the limiter.

- **Audit Chain (`app/audit.py`)**
  - Persists decisions to JSONL (`logs/audit.jsonl` by default).
  - Prepends each record with a SHA3-256 link to the previous hash to detect tampering.
  - Provides `verify_chain()` and FastAPI wrappers for on-demand verification.

- **Telemetry (`app/telemetry.py`)**
  - Tracks counters for rule hits, decisions, and latency buckets.
  - Supports optional OTEL exporting and webhooks.
  - Offers a dead-letter queue for failed forwarders.

- **Semantic Cache (`app/semantic_cache.py`)**
  - Optional Redis-backed cache for LLM prompts.
  - Gracefully disables itself when Redis or embedding libraries are not installed.

- **Token Limiter (`app/token_limiter.py`)**
  - Tracks token usage per API key with rolling minute/hour/day quotas.
  - Estimates token counts via `tiktoken` when available, otherwise falls back to character length.

- **CLI (`jimini_cli/`)**
  - `jimini lint`/`test`/`run-local` for rules workflows.
  - `jimini verify-audit`, `jimini telemetry counters`, and dead-letter helpers for operations.

## Request Flow

1. **Client request** hits `/v1/evaluate` with `api_key`, text, optional endpoint, and direction.
2. **Middleware** assigns a request ID, enforces size limits, counts metrics, and checks the API key.
3. **Rules loader** provides the current compiled rules set and token quota config.
4. **Policy engine** evaluates rules, optionally consulting the semantic cache and LLM, and produces a decision.
5. **Audit module** persists the decision and updates the hash chain.
6. **Telemetry** records counters; webhook/OTEL exporters run asynchronously.
7. **Shadow logic** downgrades the decision to `allow` when global shadow mode is active and no rule overrides enforcement.
8. **Response** returns the action, matching rule IDs, optional risk metadata, and informational message.

Other endpoints reuse the same infrastructure:

- `/v1/audit/verify` and `/v1/audit/sarif` read audit logs without touching the policy engine.
- `/v1/metrics` dumps in-memory counters and semantic cache status.
- `/v1/token-usage` exposes limiter state for operators.

## Deployment Considerations

- The application is stateless apart from the audit log and optional semantic cache; run multiple replicas behind a load balancer.
- Mount `policy_rules.yaml` and `token_quotas.yaml` via ConfigMap/volume to allow hot reloads.
- Persist `logs/audit.jsonl` on durable storage or forward entries to another system.
- Set `JIMINI_SHADOW=1` for phased rollouts; use per-rule `shadow_override: enforce` for critical protections.
- When enabling semantic cache, provide Redis credentials and `OPENAI_API_KEY`. The gateway operates without these dependencies, skipping cache/LLM logic.

## Files of Note

- `config/loader.py` – Validates `jimini.config.yaml`, merges environment overrides, and surfaces a pydantic `Config` object.
- `app/util.py` – Utility helpers (`now_iso`, `gen_request_id`) used across modules.
- `app/notifier.py`, `app/forwarders/` – Optional telemetry forwarders. Disabled unless configured.
- `tests/` – Integration tests covering enforcement precedence, shadow behaviour, audit chain checks, and CLI helpers.

This architecture description reflects the modules currently present in the repository (December 2025). Update the document whenever runtime dependencies or request flows change.