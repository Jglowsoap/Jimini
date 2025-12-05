# Jimini AI Policy Gateway

## Overview

Jimini is a FastAPI-based AI policy gateway that evaluates unstructured text against security rules before content enters or leaves AI systems. It provides zero-retention policy enforcement with deterministic blocking, flagging, and redaction based on regex patterns, threshold checks, and optional LLM validation. The system operates entirely in-memory with no persistence of customer content, making it suitable for security-first organizations requiring self-hosted AI governance.

Key capabilities include PII detection and redaction, prompt injection defense, secret scanning, toxicity filtering, hallucination checking, and token quota management. The gateway maintains a SHA3-256 linked audit chain for tamper-evident logging while never storing the actual content being evaluated.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Application Layer

**FastAPI Gateway** (`app/main.py`): The main application exposes REST endpoints for policy evaluation (`/v1/evaluate`), health checks, metrics, audit verification, and rule management. Middleware handles request ID assignment, 10 MB body limits, API key validation, and global shadow mode enforcement. The server runs on Uvicorn with hot-reload support for development.

**Policy Engine** (`app/enforcement.py`): Normalizes evaluation context (direction, endpoint, agent ID), filters rules by `applies_to` and endpoint glob patterns, executes regex and threshold checks, optionally runs LLM prompts when configured with OpenAI API keys, and applies redaction actions. Returns decisions with matched rule IDs and writes tamper-evident audit records.

**Rules Loader** (`app/rules_loader.py`): Parses YAML rule definitions using Pydantic models, compiles regex patterns for performance, stores live rules in a shared dictionary, watches the filesystem for changes to enable hot-reloading without restarts, and loads token quota tier configurations used by the rate limiter.

**Data Models** (`app/models.py`): Pydantic schemas define the structure for evaluation requests/responses, rule definitions (supporting `redact` action), audit records, and health check responses. Rules are categorized (pii, secrets, injection, toxicity, hallucination) for better organization.

### Security and Audit Layer

**Audit Chain** (`app/audit.py`): Persists policy decisions to JSONL format (default: `logs/audit.jsonl`) with each record prepended by a SHA3-256 hash linking to the previous record. Provides `verify_chain()` function and FastAPI endpoints for on-demand tamper detection. No user content is logged - only metadata, decisions, and rule IDs.

**PII Redaction**: Rules with `action: redact` automatically mask sensitive patterns (SSN, credit cards, API keys) with `[REDACTED]` tokens before content reaches downstream systems. Pre-built detection patterns are available in the Security Core rule pack.

**RBAC System** (`app/config.py`): JWT-based role-based access control with four-tier hierarchy (ADMIN → REVIEWER → SUPPORT → USER). Roles control access to admin endpoints, rule management, and audit operations. API keys map to roles for authorization.

### Observability and Operations

**Telemetry** (`app/telemetry.py`): Tracks counters for rule hits, policy decisions, and latency distribution buckets. Supports optional OpenTelemetry export to external observability platforms and webhook alerts for blocked or high-risk events. Includes a dead-letter queue for failed event forwarding with replay capability.

**Token Limiter** (`app/token_limiter.py`): Enforces rolling quotas (tokens per minute/hour/day) per API key. Estimates token counts using `tiktoken` when available, otherwise falls back to character-based approximation. Quota tiers are defined in the rules YAML configuration.

**Circuit Breaker** (`app/config.py`): Resilience pattern implementation with three states (CLOSED/OPEN/HALF_OPEN) to prevent cascading failures when external dependencies (LLM APIs, Redis) become unhealthy. Automatic recovery with exponential backoff.

**Semantic Cache** (`app/semantic_cache.py`): Optional Redis-backed cache for LLM prompt results using embedding-based similarity matching. Gracefully disables itself when Redis or required embedding libraries are unavailable, allowing the system to operate without caching.

### CLI and Tooling

**Command Line Interface** (`jimini_cli/`): Provides utilities for operational workflows:
- `jimini lint` and `jimini test` for rules validation
- `jimini run-local` for quick local gateway startup
- `jimini verify-audit` for audit chain integrity checks
- `jimini telemetry counters` for metrics inspection
- `jimini-admin` for system management (circuit breaker status, configuration validation)

### AI Innovation Engines

**AI-Powered Rule Generation** (`ai_powered_rule_generation.py`): ML-based system that analyzes attack patterns and automatically generates new security rules. Uses GPT-4 for attack analysis and rule synthesis with A/B testing for effectiveness validation.

**Multi-Language Obfuscation Detection** (`multilanguage_obfuscation_engine.py`): Detects obfuscated attacks across multiple languages and character encodings to prevent evasion techniques.

**Zero-Day Prediction Engine** (`zero_day_prediction_engine.py`): Predictive threat intelligence system that identifies emerging attack patterns before they become widespread.

**Enterprise AI Security Copilot** (`enterprise_ai_security_copilot.py`): Natural language assistant for security policy configuration, incident investigation, and automated security recommendations.

These AI modules are integrated into the main FastAPI application with endpoints under `/v1/ai/*` but can operate independently.

## External Dependencies

### Required Runtime Dependencies

**FastAPI** (Apache 2.0): Web framework providing the REST API layer with automatic OpenAPI documentation and request validation.

**Uvicorn** (BSD-3-Clause): ASGI server for running the FastAPI application with support for hot-reload during development.

**Pydantic** (MIT): Data validation and settings management using Python type annotations for request/response schemas and configuration models.

**PyYAML** (MIT): YAML parser for loading rule definitions from `policy_rules.yaml` and rule packs under `packs/`.

**python-dotenv** (BSD-3-Clause): Environment variable loading from `.env` files for configuration management.

**PyJWT** (MIT): JSON Web Token implementation for RBAC authentication and role-based authorization.

### Optional Service Dependencies

**OpenAI API**: When `OPENAI_API_KEY` is configured, enables LLM-based rule evaluation for sophisticated attack detection using GPT-4. Rules with `llm_prompt` field leverage this integration.

**Redis**: Powers the semantic cache when `semantic_cache.enabled` is true. The system gracefully degrades to no-caching mode when Redis is unavailable, maintaining full functionality.

**Elasticsearch / Splunk**: Optional telemetry export targets for centralized log aggregation. Configured via `OTEL_EXPORTER_OTLP_ENDPOINT` or webhook URLs.

**tiktoken**: OpenAI's token counting library for accurate token quota enforcement. Falls back to character-based estimation when unavailable.

### Development and Monitoring

**pytest** (MIT): Testing framework with async support (`pytest-asyncio`) and coverage reporting (`pytest-cov`). Test coverage currently at 41% with comprehensive security feature testing.

**OpenTelemetry**: Optional observability stack (API, SDK, OTLP exporter) for distributed tracing and metrics export to Prometheus/Jaeger.

**Prometheus Client** (Apache 2.0): Exposes metrics in Prometheus format at `/v1/metrics/prom` for enterprise monitoring integrations.

### Pre-built Rule Packs

The `packs/` directory contains curated rule collections for specific compliance frameworks:
- **Security Core** (`packs/security-core/v1.yaml`): 30+ pre-built rules for PII detection, prompt injection defense, secret scanning, and toxicity filtering
- **CJIS, HIPAA, PCI-DSS**: Industry-specific compliance rule sets
- **Government** (`packs/government/v1_fixed.yaml`): Rules tailored for government sector deployments

Rules are hot-reloaded automatically when YAML files change, enabling zero-downtime policy updates.