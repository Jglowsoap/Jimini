# Copilot instructions for Jimini

Jimini is a lightweight AI policy gateway. It evaluates text against YAML rules and returns a decision (block > flag > allow), logs tamper‑evident audits, exposes metrics, and supports shadow mode.

## Architecture
- FastAPI (`app/main.py`):
  - POST `/v1/evaluate` → check `api_key`, call `enforcement.evaluate`, emit OTEL (optional), update metrics, maybe send webhook, then apply shadow.
  - GET `/v1/metrics`, `/v1/audit/{verify|sarif}`, `/health`.
- Engine (`app/enforcement.py`): regex (`pattern` + optional `min_count`), `max_chars`, `llm_prompt` (OpenAI Chat Completions; fail‑safe off), scoping by `applies_to` and `endpoints`; precedence block > flag > allow; suppresses `API-1.0` if a specific secret also matched; appends `AuditRecord`.
- Rules loader (`app/rules_loader.py`): watches YAML and hot‑reloads into `rules_store` with compiled regex.
- Models (`app/models.py`): `Rule`, `EvaluateRequest`, `EvaluateResponse`, `AuditRecord`.
- Audit (`app/audit.py`): JSONL at `logs/audit.jsonl`, SHA3‑256 chain; `verify_chain()`.
- Telemetry/alerts (`app/telemetry.py`): OTEL spans; webhook on `block` and `HALLUC-1.0` flags.
- CLI (`jimini_cli/`): `lint`, `test`, `run-local`, `verify-audit`.

## Rules-as-code
- Files: `policy_rules.yaml` or `packs/<name>/v1.yaml` (schema: `app/models.Rule`).
- Fields: `pattern`, `min_count`, `max_chars`, `llm_prompt`, `applies_to`, `endpoints`, `action`, optional `shadow_override: enforce`.
- Endpoint matching: exact, prefix `.../*`, or glob (fnmatch). Keep regex in single‑quoted YAML; escape `\` (e.g., `\b...\b`).

## Decision/shadow behavior
- Direction is normalized; endpoint filter runs before checks.
- Response includes all `rule_ids`. Suppress `API-1.0` if a specific secret (e.g., `GITHUB-TOKEN-1.0`) matched.
- `JIMINI_SHADOW=1` downgrades block/flag to allow unless a matched rule has `shadow_override: enforce`.

## Dev workflows
- Install/lint/test (matches CI): `pip install -r requirements.txt && pip install -e .` → `ruff .` → `PYTHONPATH=$PWD pytest -q`.
- Run API: `uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload` or `jimini run-local --rules policy_rules.yaml --port 9000 --shadow`.
- CLI: `jimini lint --rules ...`; `jimini test --rule-pack cjis --text "fingerprint" --format table`; `jimini verify-audit`.

## Integration & env
- Auth: `/v1/evaluate` requires `api_key == JIMINI_API_KEY` (default `changeme`).
- Rules path: API and CLI use `JIMINI_RULES_PATH` (default `policy_rules.yaml`) and hot‑reloads.
- LLM: set `OPENAI_API_KEY`; default model `gpt-4o-mini`; safe no‑op if unavailable.
- OTEL: set `OTEL_EXPORTER_OTLP_ENDPOINT` to enable traces.
- Webhook: set `WEBHOOK_URL` for JSON alerts.
- Audit: override path via `AUDIT_LOG_PATH`.

## Conventions
- Use `EvaluateRequest`/`EvaluateResponse` from `app/models.py`.
- Tests can use simple objects with `action` and a compiled regex (see `tests/test_enforcement.py`).
- Add rule packs under `packs/<name>/v1.yaml`; load via `jimini_cli.loader`.

Note: Rules path is standardized on `JIMINI_RULES_PATH`.