# Jimini Quick Reference

Version: 0.2.0  
Last Updated: December 5, 2025

## Overview

Jimini is a lightweight AI policy gateway providing PII detection, risk scoring, semantic caching, and token quotas. It offers comparable capabilities to Salesforce Einstein Trust Layer and Azure APIM at significantly lower cost.

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Run with Trust Layer
jimini run-local --rules packs/einstein-trust/v1.yaml --port 9000

# 3. Test PII detection
curl -X POST http://localhost:9000/v1/evaluate \
  -H "x-api-key: changeme" \
  -d '{"text": "My SSN is 123-45-6789", "endpoint": "/api/chat"}'
```


## Enterprise Features

### Trust Layer

30+ pre-built rules in `packs/einstein-trust/v1.yaml`

| Category | Coverage | Example Rules |
|----------|----------|---------------|
| PII Detection | SSN, credit cards, emails, phones | PII-SSN-1.0, PII-CREDIT-CARD-1.0 |
| Secret Scanning | AWS keys, GitHub tokens, OpenAI keys | SECRET-AWS-KEY-1.0, SECRET-GITHUB-TOKEN-1.0 |
| Injection Defense | Jailbreaks, role-playing exploits | INJECT-JAILBREAK-1.0, INJECT-ROLE-PLAY-1.0 |
| Toxicity | Hate speech, violence, NSFW | TOXIC-HATE-1.0, TOXIC-VIOLENCE-1.0 |
| Hallucination | Missing citations, overconfidence | HALLUC-1.0, HALLUC-OVERCONFIDENT-1.0 |

Additional risk indicator rules available in `packs/einstein-trust/risk_indicators.yaml` for velocity detection, off-hours access, privilege escalation, and obfuscation attempts.

### Adaptive Risk Scoring

Behavioral profiling with 6 risk levels (very_low, low, medium, high, very_high, critical) and 4 behavior patterns (normal, suspicious, anomalous, malicious).

```python
from app.intelligence.risk_scoring import RiskScoringEngine

engine = RiskScoringEngine()
assessment = engine.assess_risk(request, response, user_id="user123")
```

Features:
- SQLite-backed user and endpoint profiles (logs/risk_history.db)
- Anomaly detection for time, endpoint deviation, and text length
- Trust scores with adaptive thresholds
- Automatic violation tracking

### Semantic Caching

Vector similarity caching for LLM responses reduces costs by avoiding redundant API calls.

```yaml
# jimini.config.yaml
semantic_cache:
  enabled: true
  redis_url: "redis://localhost:6379"
  similarity_threshold: 0.95
  ttl_seconds: 3600
```

Typical savings: $0.02 per cache hit with 45% hit rate averaging $2.40/day on 120 requests.

### Token Rate Limiting

Per-API-key quotas prevent runaway LLM costs with configurable limits.

```yaml
# token_quotas.yaml
default:
  tokens_per_minute: 10000
  tokens_per_hour: 500000
  tokens_per_day: 10000000

tiers:
  premium: { tokens_per_minute: 50000 }
  basic: { tokens_per_minute: 5000 }
  free: { tokens_per_minute: 1000 }
  dev: { tokens_per_minute: 100000 }
```

## Monitoring Endpoints

### Dashboard
```bash
curl http://localhost:9000/v1/dashboard
```

Returns aggregated metrics including requests, risk scoring, cache statistics, token quotas, and top rules. Suitable for Grafana, Datadog, and custom dashboards.

### Health Checks
```bash
curl http://localhost:9000/health                # Basic health
curl http://localhost:9000/health/detailed       # Detailed diagnostics
curl http://localhost:9000/v1/resilience         # Resilience status
```

### Prometheus Metrics
```bash
curl http://localhost:9000/v1/metrics
```

## Common Use Cases

Block PII in production:
```yaml
- id: PII-SSN-1.0
  action: block
  shadow_override: enforce
```

Flag suspicious behavior:
```yaml
- id: RISK-PRIVILEGE-ESCALATION-1.0
  action: flag
  severity: critical
```

Cache expensive LLM calls:
```yaml
- id: CACHE-COMMON-QUERY-1.0
  action: allow
```

Enforce token quotas:
```bash
export JIMINI_TOKEN_QUOTA_TIER=basic  # 5K TPM
```

## CLI Tools

```bash
jimini lint --rules packs/einstein-trust/v1.yaml
jimini test --rule-pack einstein-trust --text "My email is test@example.com"
jimini verify-audit
jimini run-local --rules policy_rules.yaml --port 9000 --shadow
```

## Documentation

- TRUST_LAYER.md - Einstein Trust Layer guide
- PLATFORM_COMPARISON.md - Azure APIM competitive analysis
- IMPROVEMENT_ROADMAP.md - Future priorities
- ADMIN_RUNBOOK.md - Operations playbook

## Platform Comparison

| Feature | Jimini | Azure APIM | Salesforce Einstein | AWS Bedrock |
|---------|--------|-----------|---------------------|-------------|
| PII Detection | 30+ rules | Basic | Advanced | Advanced |
| Risk Scoring | Adaptive | None | Advanced | Basic |
| Semantic Cache | Vector-based | Basic | None | None |
| Token Quotas | TPM/hour/day | TPM only | None | TPM only |
| Cost (1M requests) | $100 | $700 | $2,500+ | $1,200 |
| License | MIT | Proprietary | Proprietary | Proprietary |

Cost reduction: 76-87% vs Azure, 90%+ vs Salesforce.

## Troubleshooting

Rules not loading:
```bash
export JIMINI_RULES_PATH=packs/einstein-trust/v1.yaml
```

Semantic cache unavailable:
```bash
pip install numpy redis sentence-transformers
```

Token limiter disabled:
```bash
pip install tiktoken
```

Risk scoring failing:
```bash
ls -la logs/risk_history.db
```

## Recommended Learning Path

1. Basic rule evaluation (policy_rules.yaml)
2. Trust Layer rules (packs/einstein-trust/v1.yaml)
3. Risk scoring (automatic behavioral profiling)
4. Semantic caching (cost optimization)
5. Token quotas and monitoring dashboard

## Support

- GitHub Issues: https://github.com/Jglowsoap/Jimini
- Documentation: README.md, TRUST_LAYER.md
- CLI Help: jimini --help

Note: Start with shadow mode (`--shadow`) to test rules without blocking production traffic.
