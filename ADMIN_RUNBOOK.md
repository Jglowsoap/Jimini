# Jimini AI Policy Gateway - Admin & Operations Runbook

## 🚀 **Quick Reference**

| Component | Status Command | Health Endpoint | Default Port |
|-----------|----------------|-----------------|--------------|
| **Main API** | `jimini health` | `GET /health` | 9000 |
| **Readiness** | `jimini ready` | `GET /ready` | 9000 |
| **Metrics** | `jimini metrics` | `GET /v1/metrics` | 9000 |
| **Audit Chain** | `jimini audit verify` | `GET /v1/audit/verify` | 9000 |

---

## 📋 **Daily Operations Checklist**

### **Morning Health Check**
```bash
# 1. Service Status
jimini health --format json
curl -s http://localhost:9000/health | jq .

# 2. Audit Chain Integrity
jimini audit verify --show-details
curl -s http://localhost:9000/v1/audit/verify | jq .

# 3. Circuit Breaker Status
curl -s http://localhost:9000/v1/resilience | jq .circuit_breakers

# 4. Configuration Validation
jimini config validate --env production
```

### **Performance Monitoring**
```bash
# Request metrics and throughput
curl -s http://localhost:9000/v1/metrics | jq '.totals, .recent[0:5]'

# Memory and resource usage
jimini admin metrics --system

# Dead letter queue status
curl -s http://localhost:9000/v1/resilience | jq .dead_letter_queue
```

---

## 🛡️ **Security Operations**

### **Access Management (RBAC)**
```bash
# Check current RBAC status
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:9000/admin/security

# Admin access verification
jimini rbac verify --user admin@company.com --role ADMIN

# Audit admin actions
jimini audit filter --event-type admin --last 24h
```

### **PII & Compliance Monitoring**
```bash
# PII redaction status and statistics
curl -s http://localhost:9000/admin/security | jq .redaction_summary

# Compliance validation
jimini compliance check --frameworks HIPAA,CJIS,PCI_DSS

# Data retention policy status
jimini audit retention-status --show-cleanup-schedule
```

### **Security Incident Response**
```bash
# 1. Security event investigation
jimini audit filter --action security --severity high --last 1h

# 2. Suspicious pattern detection
jimini analysis detect-anomalies --window 24h

# 3. Block/flag trend analysis
jimini metrics security-trends --period 7d

# 4. Emergency circuit breaker activation
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:9000/admin/circuit/openai/open
```

---

## 📊 **Monitoring & Alerting**

### **Key Performance Indicators (KPIs)**
```bash
# Decision latency (target: <100ms p95)
jimini metrics latency --percentiles 50,95,99

# Request throughput (target: >1000 req/min)
jimini metrics throughput --window 5m

# Error rates (target: <1%)
jimini metrics errors --groupby endpoint

# Audit chain integrity (target: 100% valid)
jimini audit verify --brief
```

### **Alert Conditions**
1. **Critical**: Audit chain integrity failure
2. **Critical**: Circuit breaker open for >5 minutes  
3. **Warning**: Request latency >200ms p95
4. **Warning**: Error rate >2%
5. **Info**: PII detection threshold exceeded

### **Prometheus Metrics Export**
```bash
# Enable Prometheus metrics
export JIMINI_PROMETHEUS_ENABLED=true
export JIMINI_PROMETHEUS_PORT=8090

# Custom metrics endpoints
curl http://localhost:8090/metrics | grep jimini_
```

---

## 🔧 **Troubleshooting Guide**

### **Common Issues & Solutions**

#### **1. High Request Latency**
```bash
# Symptoms: p95 latency >200ms
# Investigation:
jimini metrics latency --breakdown-by endpoint,rule
curl -s http://localhost:9000/v1/resilience | jq .circuit_breakers

# Solutions:
# - Check LLM service connectivity (OpenAI API)
# - Review rule complexity and regex patterns
# - Scale horizontal replicas if CPU bound
```

#### **2. Audit Chain Integrity Failure**  
```bash
# Symptoms: /v1/audit/verify returns valid: false
# Investigation:
jimini audit verify --verbose --show-break-point
jimini audit export --format json --output /tmp/audit_backup.json

# Solutions:
# - If tampered: investigate security breach, restore from backup
# - If corrupted: validate filesystem integrity, restore from backup
# - If malformed records: identify source, fix data ingestion
```

#### **3. Circuit Breaker Stuck Open**
```bash
# Symptoms: Persistent 503 errors for specific services
# Investigation:
curl -s http://localhost:9000/v1/resilience | jq .circuit_breakers.openai

# Solutions:
# - Check external service health (OpenAI API status)
# - Manually reset circuit breaker:
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:9000/admin/circuit/openai/close
```

#### **4. Memory/Resource Issues**
```bash
# Symptoms: OOM kills, high memory usage
# Investigation:
jimini admin resources --show-memory-breakdown
docker stats jimini-container

# Solutions:
# - Tune audit log retention: JIMINI_AUDIT_RETENTION_DAYS=30
# - Adjust worker processes: JIMINI_WORKERS=2
# - Enable log rotation: JIMINI_LOG_ROTATION=true
```

---

## 🚀 **Deployment Operations**

### **Production Deployment**
```bash
# 1. Pre-deployment validation
jimini config validate --env production --strict
jimini test integration --env production

# 2. Health check readiness
jimini ready --timeout 30s --retry 3

# 3. Rolling deployment verification
jimini deploy verify --check-audit-continuity

# 4. Post-deployment validation
jimini smoke-test --full-suite
```

### **Configuration Management**
```bash
# Environment-specific configs
export JIMINI_CONFIG_PROFILE=production
export JIMINI_RULES_PATH=/etc/jimini/policy_rules.yaml

# Configuration validation
jimini config diff --from dev --to production
jimini config secrets verify --vault-path /secret/jimini

# Hot-reload policy rules
jimini rules reload --validate-syntax
curl -X POST http://localhost:9000/admin/rules/reload
```

### **Backup & Recovery**
```bash
# Daily audit backup
jimini audit export --date $(date -d "yesterday" +%Y-%m-%d) \
  --format jsonl --output /backup/audit-$(date +%Y%m%d).jsonl

# Configuration backup
tar -czf /backup/jimini-config-$(date +%Y%m%d).tar.gz \
  /etc/jimini/ /app/packs/ /app/config/

# Recovery procedure
jimini audit import --file /backup/audit-20251001.jsonl --verify-chain
jimini config restore --backup /backup/jimini-config-20251001.tar.gz
```

---

## 🔒 **Security Hardening**

### **Production Security Checklist**
- [ ] **API Keys**: Rotate JIMINI_API_KEY monthly
- [ ] **JWT Secrets**: Rotate signing keys quarterly  
- [ ] **TLS**: Enable HTTPS with valid certificates
- [ ] **RBAC**: Audit user roles and permissions monthly
- [ ] **Audit Logs**: Verify tamper-evident chain integrity daily
- [ ] **Dependencies**: Update security patches weekly
- [ ] **Penetration Testing**: Quarterly security assessments

### **Security Monitoring**
```bash
# Failed authentication attempts
jimini audit filter --event-type security_auth_failure --last 24h

# Admin action audit
jimini audit filter --event-type admin --user-id "*" --last 7d

# Suspicious IP patterns
jimini analysis ip-patterns --threshold 100 --window 1h

# Policy violation trends
jimini metrics violations --groupby rule_id --period 7d
```

---

## 📞 **Emergency Procedures**

### **Security Incident Response**
1. **Immediate**: Enable emergency mode: `jimini emergency-mode enable`
2. **Containment**: Block suspicious IPs: `jimini firewall block-ip <ip>`
3. **Investigation**: Audit trail analysis: `jimini forensics analyze --incident-id <id>`
4. **Recovery**: Restore from backup: `jimini recovery restore --backup <path>`
5. **Post-incident**: Generate report: `jimini incident report --format pdf`

### **Service Recovery**
```bash
# Complete service restart with health verification
docker-compose down && docker-compose up -d
jimini wait-healthy --timeout 60s

# Database recovery
jimini audit rebuild-chain --from-backup /backup/audit-latest.jsonl

# Configuration reset
jimini config reset --to-defaults --keep-secrets
```

---

## 📈 **Performance Optimization**

### **Tuning Parameters**
```bash
# Worker processes (CPU cores * 2)
export JIMINI_WORKERS=4

# Request timeout (milliseconds)
export JIMINI_REQUEST_TIMEOUT=5000

# Circuit breaker settings
export JIMINI_CIRCUIT_FAILURE_THRESHOLD=10
export JIMINI_CIRCUIT_TIMEOUT=30

# Cache settings
export JIMINI_RULE_CACHE_TTL=300
export JIMINI_LLM_CACHE_SIZE=1000
```

### **Resource Monitoring**
```bash
# Real-time performance dashboard
jimini dashboard start --port 8080 --realtime

# Performance profiling
jimini profile --duration 60s --output /tmp/profile.prof

# Load testing validation
jimini loadtest --rps 100 --duration 60s --scenario production
```

---

## 📝 **Maintenance Schedule**

| **Task** | **Frequency** | **Command** |
|----------|---------------|-------------|
| Health Check | Daily | `jimini health --comprehensive` |
| Audit Verification | Daily | `jimini audit verify --full` |
| Performance Review | Weekly | `jimini metrics report --period 7d` |
| Security Scan | Weekly | `jimini security scan --full` |
| Backup Validation | Weekly | `jimini backup verify --all` |
| Configuration Audit | Monthly | `jimini config audit --compliance` |
| Dependency Updates | Monthly | `jimini update --security-only` |
| Full System Test | Quarterly | `jimini test --suite comprehensive` |

---

## 🆘 **Support Contacts**

| **Issue Type** | **Contact** | **Escalation** |
|----------------|-------------|----------------|
| **Security Incident** | security@jimini.ai | 🚨 Page on-call |
| **Service Outage** | ops@jimini.ai | 📱 Call +1-800-JIMINI |  
| **Performance Issues** | support@jimini.ai | 💬 Slack #jimini-ops |
| **Configuration Help** | docs@jimini.ai | 📖 docs.jimini.ai |

---

*Last Updated: October 2025 | Version: 0.2.0 | Status: Production Ready*