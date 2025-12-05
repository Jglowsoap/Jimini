# 🎯 Jimini Quick Reference - Enterprise Features

**Version:** 0.2.0  
**Last Updated:** December 5, 2025

## One-Liner: What is Jimini?
Lightweight AI policy gateway with **Einstein Trust Layer** capabilities - PII detection, risk scoring, semantic caching, and token quotas at **76-87% lower cost** than Azure APIM.

---

## 🚀 Quick Start (30 seconds)

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

---

## 📊 Enterprise Features

### 1. Trust Layer (Einstein-Inspired)
**30+ pre-built rules in `packs/einstein-trust/v1.yaml`**

| Category | Rules | Example |
|----------|-------|---------|
| **PII Detection** | SSN, credit cards, emails, phones | `PII-SSN-1.0`, `PII-CREDIT-CARD-1.0` |
| **Secret Scanning** | AWS keys, GitHub tokens, OpenAI keys | `SECRET-AWS-KEY-1.0`, `SECRET-GITHUB-TOKEN-1.0` |
| **Injection Defense** | Jailbreaks, role-playing exploits | `INJECT-JAILBREAK-1.0`, `INJECT-ROLE-PLAY-1.0` |
| **Toxicity** | Hate speech, violence, NSFW | `TOXIC-HATE-1.0`, `TOXIC-VIOLENCE-1.0` |
| **Hallucination** | Missing citations, overconfidence | `HALLUC-1.0`, `HALLUC-OVERCONFIDENT-1.0` |

**NEW:** Risk indicator rules in `packs/einstein-trust/risk_indicators.yaml`
- Velocity detection, off-hours access, privilege escalation, obfuscation

### 2. Adaptive Risk Scoring
**Behavioral profiling with 6 risk levels**

```python
from app.intelligence.risk_scoring import RiskScoringEngine

engine = RiskScoringEngine()
assessment = engine.assess_risk(request, response, user_id="user123")

# Risk levels: very_low, low, medium, high, very_high, critical
# Behavior patterns: normal, suspicious, anomalous, malicious
```

**Features:**
- SQLite-backed user/endpoint profiles (`logs/risk_history.db`)
- Anomaly detection (time, endpoint deviation, text length)
- Trust scores with adaptive thresholds
- Automatic violation tracking

### 3. Semantic Caching
**Vector similarity caching for LLM responses**

```yaml
# jimini.config.yaml
semantic_cache:
  enabled: true
  redis_url: "redis://localhost:6379"
  similarity_threshold: 0.95  # 95% similarity = cache hit
  ttl_seconds: 3600           # 1 hour cache
```

**Cost Savings:**
- $0.02 per cache hit (avoids GPT-4 call)
- 45% hit rate typical = **$2.40/day savings** on 120 requests

### 4. Token Rate Limiting
**Prevent runaway LLM costs**

```yaml
# token_quotas.yaml
default:
  tokens_per_minute: 10000
  tokens_per_hour: 500000
  tokens_per_day: 10000000

tiers:
  premium:  # 50K TPM
  basic:    # 5K TPM
  free:     # 1K TPM
  dev:      # 100K TPM (no limits)
```

**Features:**
- Pre-calculation before LLM calls
- `tiktoken` integration for GPT-4
- Per-API-key quotas

---

## 📈 Monitoring Endpoints

### Quick Dashboard
```bash
curl http://localhost:9000/v1/dashboard
```

**Returns:** Single JSON with all metrics (requests, risk scoring, cache, quotas, top rules)
**Use Case:** Grafana, Datadog, custom dashboards

### Health Checks
```bash
# Basic health
curl http://localhost:9000/health

# Detailed diagnostics
curl http://localhost:9000/health/detailed

# Resilience status
curl http://localhost:9000/v1/resilience
```

### Prometheus Metrics
```bash
curl http://localhost:9000/v1/metrics
```

---

## 🎯 Common Use Cases

### 1. Block PII in Production
```yaml
- id: PII-SSN-1.0
  action: block
  shadow_override: enforce  # Block even in shadow mode
```

### 2. Flag Suspicious Behavior
```yaml
- id: RISK-PRIVILEGE-ESCALATION-1.0
  action: flag  # Log but allow
  severity: critical
```

### 3. Cache Expensive LLM Calls
```yaml
- id: CACHE-COMMON-QUERY-1.0
  action: allow
  # Semantic cache auto-matches similar queries
```

### 4. Enforce Token Quotas
```bash
# Set quota for API key
export JIMINI_TOKEN_QUOTA_TIER=basic  # 5K TPM
```

---

## 🔧 CLI Tools

```bash
# Lint rules
jimini lint --rules packs/einstein-trust/v1.yaml

# Test rule packs
jimini test --rule-pack einstein-trust --text "My email is test@example.com"

# Verify audit chain
jimini verify-audit

# Run local server
jimini run-local --rules policy_rules.yaml --port 9000 --shadow
```

---

## 📚 Documentation

- **TRUST_LAYER.md** - Einstein Trust Layer guide (578 lines)
- **PLATFORM_COMPARISON.md** - Azure APIM competitive analysis (755 lines)
- **IMPROVEMENT_ROADMAP.md** - Future priorities (1314 lines)
- **ADMIN_RUNBOOK.md** - Operations playbook

---

## 🆚 vs. Enterprise Platforms

| Feature | Jimini | Azure APIM | Salesforce Einstein | AWS Bedrock |
|---------|--------|-----------|---------------------|-------------|
| **PII Detection** | ✅ 30+ rules | ✅ Basic | ✅ Advanced | ✅ Advanced |
| **Risk Scoring** | ✅ Adaptive | ❌ None | ✅ Advanced | ✅ Basic |
| **Semantic Cache** | ✅ Vector | ✅ Basic | ❌ None | ❌ None |
| **Token Quotas** | ✅ TPM/hour/day | ✅ TPM only | ❌ None | ✅ TPM only |
| **Cost (1M requests)** | **$100** | $700 | $2,500+ | $1,200 |
| **Open Source** | ✅ MIT | ❌ Proprietary | ❌ Proprietary | ❌ Proprietary |

**Cost Savings:** 76-87% vs Azure, 90%+ vs Salesforce

---

## 🚨 Common Issues

### "Rules not loading"
```bash
# Check path
export JIMINI_RULES_PATH=packs/einstein-trust/v1.yaml
```

### "Semantic cache unavailable"
```bash
# Install dependencies
pip install numpy redis sentence-transformers
```

### "Token limiter disabled"
```bash
# Install tiktoken
pip install tiktoken
```

### "Risk scoring failing"
```bash
# Check database
ls -la logs/risk_history.db
```

---

## 🎓 Learning Path

1. **Start:** Basic rule evaluation (`policy_rules.yaml`)
2. **Add:** Trust Layer rules (`packs/einstein-trust/v1.yaml`)
3. **Enable:** Risk scoring (automatic behavioral profiling)
4. **Optimize:** Semantic caching (cost savings)
5. **Scale:** Token quotas + monitoring dashboard

---

## 📞 Support

- **GitHub Issues:** https://github.com/Jglowsoap/Jimini
- **Documentation:** `README.md`, `TRUST_LAYER.md`
- **CLI Help:** `jimini --help`

---

**Pro Tip:** Start with `--shadow` mode to test rules without blocking production traffic!
