# Jimini Security & Compliance Documentation

## Overview

Jimini is designed as an enterprise-grade AI policy gateway with comprehensive security and compliance features. This document outlines the security controls, compliance capabilities, and operational procedures for production deployment.

## Security Architecture

### Authentication & Authorization

#### Role-Based Access Control (RBAC)
- **Roles**: ADMIN, REVIEWER, SUPPORT, USER with hierarchical permissions
- **JWT Tokens**: HS256 signed tokens with configurable expiration
- **API Key Authentication**: Configurable keys for service-to-service communication
- **Fail-Safe Defaults**: System defaults to USER role when RBAC is disabled

#### Configuration
```yaml
security:
  rbac_enabled: true
  jwt_secret: "${RBAC_JWT_SECRET}"
```

### Data Protection

#### PII Redaction System
Comprehensive PII detection and redaction supporting:
- **Social Security Numbers**: xxx-xx-xxxx, xxxxxxxxx patterns
- **Phone Numbers**: US/International formats with various delimiters  
- **Email Addresses**: RFC 5322 compliant patterns
- **Credit Card Numbers**: Visa, MasterCard, AmEx, Discover, Diners Club
- **IP Addresses**: IPv4 addresses with optional CIDR notation
- **API Keys & Tokens**: Common API key patterns, JWT tokens, SSH keys
- **Generic Identifiers**: Driver licenses, employee IDs, tax IDs

#### Redaction Configuration
```python
from app.pii_redactor import PIIRedactor

redactor = PIIRedactor()
redacted_text = redactor.redact(sensitive_text, preserve_structure=False)
pii_types_found = redactor.detect_pii_types(text)
```

### Audit & Compliance

#### Tamper-Evident Audit Logging
- **Chain Integrity**: SHA3-256 hash chains prevent tampering
- **Comprehensive Records**: All policy decisions with metadata
- **Retention Policies**: Configurable retention with automatic rotation
- **Compliance Fields**: HIPAA, CJIS, PCI DSS tracking

#### Audit Record Schema
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_12345",
  "action": "block|flag|allow",
  "direction": "request|response", 
  "endpoint": "/v1/evaluate",
  "rule_ids": ["RULE-1.0"],
  "text_hash": "sha256_hash",
  "previous_hash": "previous_record_hash",
  "pii_redacted": true,
  "compliance_flags": ["HIPAA", "CJIS"],
  "retention_class": "standard|extended|legal_hold"
}
```

### Security Headers & Input Validation

#### HTTP Security Headers
All responses include comprehensive security headers:
- **X-Content-Type-Options**: `nosniff`
- **X-Frame-Options**: `DENY`
- **X-XSS-Protection**: `1; mode=block`
- **Strict-Transport-Security**: `max-age=31536000; includeSubDomains`
- **Content-Security-Policy**: Restrictive CSP for web interfaces
- **Referrer-Policy**: `strict-origin-when-cross-origin`

#### Input Sanitization
- **XSS Prevention**: Script tag and JavaScript protocol detection
- **SQL Injection Protection**: Common SQL injection pattern blocking
- **Command Injection Protection**: Shell metacharacter filtering
- **Path Traversal Protection**: Directory traversal attempt detection
- **Size Limits**: Configurable payload size restrictions

### Error Handling & Resilience

#### Circuit Breaker Pattern
- **Per-Service Protection**: Individual breakers for OpenAI, Slack, etc.
- **Configurable Thresholds**: Failure counts and recovery timeouts
- **Half-Open Testing**: Gradual recovery with success thresholds
- **Monitoring Integration**: Health status exposed via `/v1/resilience`

#### Retry Logic & Dead Letter Queue
- **Exponential Backoff**: Configurable base delay and maximum attempts
- **Jitter**: Random delays to prevent thundering herd problems
- **Failed Message Handling**: Dead letter queue for analysis
- **Circuit Breaker Integration**: Respects breaker states during retries

## Compliance Framework

### HIPAA Compliance

#### Technical Safeguards
- **Access Control**: RBAC with role-based endpoint protection
- **Audit Controls**: Comprehensive logging with integrity verification
- **Integrity**: Hash chains prevent audit log tampering
- **Person or Entity Authentication**: JWT tokens with expiration
- **Transmission Security**: HTTPS with security headers

#### Administrative Safeguards
- **Security Officer**: Designated through RBAC ADMIN role
- **Workforce Training**: Documented in security procedures
- **Information System Activity Review**: Audit log analysis tools
- **Contingency Plan**: Circuit breakers and graceful degradation

#### Physical Safeguards
- **Facility Access Controls**: Cloud deployment with provider controls
- **Workstation Use**: Secure configuration management
- **Device and Media Controls**: Audit log retention and disposal

### CJIS Compliance (Criminal Justice Information Services)

#### Security Areas
- **Information Security**: Comprehensive audit logging
- **Personnel Security**: RBAC role management
- **Physical Protection**: Cloud security controls
- **Technical Security**: Encryption in transit, secure protocols
- **Mobile Device Security**: API key management for mobile access

### PCI DSS Compliance (Payment Card Industry)

#### Requirements Coverage
- **Secure Network**: Security headers and input validation
- **Cardholder Data Protection**: PII redaction for credit cards
- **Vulnerability Management**: Regular security updates
- **Access Control**: RBAC with least privilege
- **Network Monitoring**: Audit logging and analysis
- **Information Security Policy**: Documented procedures

## Operational Security

### Environment Configuration

#### Production Security Settings
```yaml
app:
  env: prod
  shadow_mode: false
  use_pii: false  # Disable PII processing if not needed

security:
  rbac_enabled: true
  
notifiers:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    
siem:
  jsonl:
    enabled: true
    file_path: "/secure/audit/audit.jsonl"
    retention_days: 2555  # 7 years for compliance
```

#### Secret Management
- **Environment Variables**: All secrets via environment variables
- **No Defaults in Production**: Fail-fast validation prevents default keys
- **Rotation Support**: JWT secrets and API keys support rotation
- **Masking**: Secrets masked in health endpoints and logs

### Monitoring & Alerting

#### Health Endpoints
- **`/health`**: Basic service health check
- **`/ready`**: Readiness with configuration and dependencies
- **`/v1/resilience`**: Circuit breaker and error handling status
- **`/admin/metrics`**: Comprehensive metrics (RBAC protected)

#### Alert Conditions
- **Circuit Breaker Open**: Service degradation notifications
- **Policy Violations**: Block and flag decisions
- **Authentication Failures**: Invalid JWT or API key attempts
- **System Errors**: Unhandled exceptions and service failures

### Incident Response

#### Security Incident Categories
1. **Authentication Bypass**: Unauthorized access attempts
2. **Data Breach**: Potential PII exposure
3. **System Compromise**: Malicious code execution
4. **Denial of Service**: Resource exhaustion attacks
5. **Configuration Error**: Misconfigured security controls

#### Response Procedures
1. **Detection**: Monitor alerts and audit logs
2. **Containment**: Circuit breakers and rate limiting
3. **Eradication**: Remove malicious content or fix vulnerabilities
4. **Recovery**: Restore services with additional monitoring
5. **Lessons Learned**: Update security controls and procedures

## Deployment Security

### Container Security
```dockerfile
# Use minimal base image
FROM python:3.12-slim

# Run as non-root user
RUN useradd --create-home --shell /bin/bash jimini
USER jimini

# Security headers middleware enabled
ENV JIMINI_ENV=prod
ENV SECURITY_HEADERS_ENABLED=true
```

### Network Security
- **HTTPS Only**: No HTTP endpoints in production
- **API Gateway**: Rate limiting and DDoS protection
- **VPC Deployment**: Private subnets for sensitive components
- **WAF Integration**: Web application firewall for additional protection

### Data Security
- **Encryption in Transit**: TLS 1.2+ for all connections
- **Encryption at Rest**: Encrypted storage for audit logs
- **Key Management**: HSM or cloud key management service
- **Data Retention**: Automated deletion per retention policies

## Testing & Validation

### Security Testing
Run comprehensive security validation:
```bash
# Configuration validation
python scripts/test_phase_4a.py

# Resilience testing  
python -m pytest tests/test_phase_4b_resilience.py -v

# Security and compliance testing
python scripts/test_phase_4c.py

# Complete Phase 4 validation
python scripts/phase_4_summary.py
```

### Penetration Testing
Regular security assessments should include:
- **API Security**: Authentication bypass, injection attacks
- **Input Validation**: XSS, SQL injection, command injection
- **Configuration Security**: Default credentials, misconfigurations
- **Business Logic**: Policy bypass attempts

## Compliance Validation

### Audit Procedures
1. **Access Reviews**: Quarterly RBAC role assignments
2. **Configuration Audits**: Monthly security settings review
3. **Log Analysis**: Weekly audit log integrity verification
4. **Incident Review**: Post-incident security control assessment

### Documentation Requirements
- **Security Policies**: Documented security procedures
- **Risk Assessment**: Annual security risk evaluation
- **Business Associate Agreements**: For HIPAA covered entities
- **Incident Reports**: Security incident documentation

## Contact Information

- **Security Issues**: security@jimini.ai
- **Compliance Questions**: compliance@jimini.ai
- **Technical Support**: support@jimini.ai

---

*This document is updated with each major release. For the latest version, see: https://github.com/jimini-ai/jimini/blob/main/docs/security-compliance.md*