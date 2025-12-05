# Jimini Operations Runbook

This runbook collects the operational tasks that engineers actually need when supporting Jimini in production. Commands reference implemented endpoints and documented tooling.

## Quick Reference

| Purpose | How |
| --- | --- |
| Liveness/readiness | `curl -s http://HOST:PORT/health` |
| Deep diagnostics | `curl -s http://HOST:PORT/health/detailed` |
| Metrics snapshot | `curl -s http://HOST:PORT/v1/metrics` |
| Audit verification | `curl -s http://HOST:PORT/v1/audit/verify` or `jimini verify-audit` |
| Token usage | `curl -s http://HOST:PORT/v1/token-usage` |

Replace `HOST:PORT` with your deployment endpoint (default `localhost:9000`).

## Daily Checklist

1. **Service health**

   ```bash
   curl -s http://localhost:9000/health | jq
   ```

2. **Audit chain integrity**

   ```bash
   curl -s http://localhost:9000/v1/audit/verify | jq
   ```

3. **Decision metrics**

   ```bash
   curl -s http://localhost:9000/v1/metrics | jq '.totals, .rules'
   ```

4. **Semantic cache (if enabled)**

   Check `.semantic_cache` section in `/health/detailed` for connectivity errors.

## Incident Response

### Elevated block rate or false positives

1. Inspect recent audit entries (`logs/audit.jsonl`) and `/v1/metrics` rule counters.
2. Confirm whether shadow mode is active via `/health/detailed`.
3. If necessary, disable problematic rules by editing the YAML file and allowing hot reload to pick up the change.

### Audit verification failure

1. Run `jimini verify-audit` to identify the break point.
2. Quarantine the affected audit file and restore the last known good copy.
3. Investigate filesystem integrity or clock skew that may have caused the issue.

### Token limiter warnings

1. Query `/v1/token-usage` for the offending API key.
2. Adjust limits in `token_quotas.yaml` or rotate the key if abuse is suspected.

### Semantic cache timeouts

1. Disable the cache by setting `semantic_cache.enabled: false` in `jimini.config.yaml`.
2. Restart the service or trigger a config reload.
3. Investigate Redis connectivity and credentials before re-enabling.

## Operational Tasks

- **Rotate API keys**: generate a new value, update `JIMINI_API_KEY`, and restart instances. Clients must present the new key immediately.
- **Rule updates**: edit `policy_rules.yaml`, run `jimini lint --rules policy_rules.yaml`, commit changes, and let hot reload pick them up.
- **Audit log backup**: copy `logs/audit.jsonl` to secure storage. Keep file ordering intact to preserve hash chains.
- **Telemetry export**: configure `WEBHOOK_URL` or OTEL endpoint environment variables; verify events via `/health/detailed` (`telemetry.forwarders`).

## Useful CLI Commands

```bash
# Validate a rules file before deployment
jimini lint --rules policy_rules.yaml

# Dry-run an example text
jimini test --rules policy_rules.yaml --text "SSN 123-45-6789" --format json

# Launch a local gateway using the CLI wrapper
jimini run-local --rules policy_rules.yaml --shadow

# Check telemetry counters (requires running gateway)
jimini telemetry counters

# View dead-letter queue stats if forwarders fail
jimini deadletter stats
```

## Maintenance Cadence

| Frequency | Task |
| --- | --- |
| Daily | Health check, audit verification, review block counts |
| Weekly | Backup `policy_rules.yaml`, `token_quotas.yaml`, and `logs/audit.jsonl` |
| Monthly | Review rule effectiveness and prune unused rules |
| Release | Run `ruff .` and `pytest -q`, then redeploy |

Document deviations, configuration changes, and notable incidents in your team tracker. Update this runbook whenever new operational endpoints or CLI commands land in the repository.