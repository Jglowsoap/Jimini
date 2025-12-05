# Jimini Deployment Guide

This guide focuses on reproducible ways to run Jimini locally, in containers, and in production-like environments. All configurations reference the real code paths in this repository.

## 1. Local Development

1. Install dependencies (see `README.md` for details).
2. Export minimal environment variables:

  ```bash
  export JIMINI_API_KEY=changeme
  export JIMINI_RULES_PATH=policy_rules.yaml
  export JIMINI_SHADOW=1  # optional for shadow mode testing
  ```

3. Launch with Uvicorn:

  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
  ```

4. Confirm health:

  ```bash
  curl -s http://localhost:9000/health | jq
  ```

### Running via CLI helper

```bash
jimini run-local --rules policy_rules.yaml --port 9000 --shadow
```

This wraps the same Uvicorn command while setting `JIMINI_RULES_PATH` automatically.

## 2. Docker

The provided `Dockerfile` bundles the FastAPI app with all dependencies. Build and run:

```bash
docker build -t jimini:latest .
docker run --rm -p 9000:9000 \
  -e JIMINI_API_KEY=changeme \
  -e JIMINI_RULES_PATH=/app/policy_rules.yaml \
  -v $(pwd)/policy_rules.yaml:/app/policy_rules.yaml:ro \
  jimini:latest
```

Optional volumes:

- Mount `logs/` to persist the audit chain: `-v $(pwd)/logs:/app/logs`
- Mount custom token quotas: `-v $(pwd)/token_quotas.yaml:/app/token_quotas.yaml:ro`

## 3. Production Considerations

| Area | Recommendation |
| --- | --- |
| API authentication | Set a strong `JIMINI_API_KEY` and store secrets outside the container image. |
| Rules | Mount `policy_rules.yaml` and `token_quotas.yaml` via ConfigMap/volume so updates do not require image rebuilds. |
| Shadow deployments | Set `JIMINI_SHADOW=1` during rollout; use `shadow_override: enforce` for critical rules. |
| Audit log | Persist `logs/audit.jsonl` to durable storage or ship to an external log sink. |
| Telemetry | Configure `OTEL_EXPORTER_OTLP_ENDPOINT` or `WEBHOOK_URL` when centralised monitoring is required. |
| Semantic cache | Enable only when Redis and `sentence-transformers` dependencies are available; otherwise keep disabled. |

### Horizontal scaling

Jimini is stateless apart from the audit log. Multiple instances can run behind a load balancer. Ensure all replicas share the same rules files and audit storage when integrity checks are required.

### Health checks

- Liveness/readiness: `GET /health`
- Deep diagnostics: `GET /health/detailed`
- Audit verification: `GET /v1/audit/verify` (non-blocking, use for periodic checks)

## 4. Post-Deployment Checklist

- [ ] Replace default API key and restrict access to `/v1/evaluate`.
- [ ] Confirm `/v1/metrics` exposes expected counters.
- [ ] Verify audit chain with `jimini verify-audit` or `/v1/audit/verify`.
- [ ] Review rule matches in `logs/audit.jsonl` and confirm expected decisions.
- [ ] Exercise error paths by simulating shadow mode and blocked traffic.

## 5. Troubleshooting

- Missing rules: ensure `JIMINI_RULES_PATH` points to a readable YAML file and check `/health/detailed` for `rules_not_loaded`.
- Audit verification failures: archive existing `logs/audit.jsonl` and restart; corruption indicates storage or timestamp issues.
- Semantic cache errors: set `semantic_cache.enabled: false` in `jimini.config.yaml` or remove Redis configuration.
- Token limiter warnings: inspect `/v1/token-usage` and confirm `token_quotas.yaml` matches expected tiers.

Keep this guide aligned with real deployment scripts. If the Dockerfile or configuration loader changes, update the relevant sections.