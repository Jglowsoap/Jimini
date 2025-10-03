# 🛡️ Jimini Policy Gateway

## Enterprise PKI Security Gateway & Policy Engine

Jimini is a comprehensive security gateway that sits in front of all PKI-connected systems (LDAP, Entrust IDG, UMS, DB2, ServiceNow) as the filter of record for inbound and outbound traffic. It provides PII masking, policy enforcement, decision logging, and LLM guardrails for government and enterprise environments.

### 🎯 **Key Features**

- **Policy Enforcement**: Inbound schema validation, authorization checks, injection detection
- **PII Protection**: Outbound DLP/PII masking, secrets scrubbing, policy citations
- **LLM Guardrails**: Content masking/pseudonymization before LLM services
- **Decision Logging**: Structured logs for every decision with rule IDs and citations
- **Rule Lifecycle**: Validate → Dry-run → Publish with versioning and modes
- **PKI Integration**: Adapters for LDAP, Entrust IDG, UMS, DB2, ServiceNow

### 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React/Flask   │────│  Jimini Gateway │────│   PKI Systems   │
│   Dashboard     │    │                 │    │                 │
└─────────────────┘    │  • Policy Engine│    │ • LDAP          │
                       │  • PII Masking  │    │ • Entrust IDG   │
                       │  • Rule Engine  │    │ • UMS           │
                       │  • Audit Log    │    │ • DB2           │
                       └─────────────────┘    │ • ServiceNow    │
                                              └─────────────────┘
```

### 🚀 **Quick Start**

#### Prerequisites
- Python 3.9+
- Docker & Docker Compose (for production)
- Node.js 18+ (for React dashboard)

#### Development Setup

1. **Clone and install dependencies**:
```bash
git clone <repository>
cd Jimini
pip install -r requirements.txt
```

2. **Start Jimini Gateway**:
```bash
# Option 1: Direct start
python jimini_gateway.py

# Option 2: Using deployment manager
python deploy_jimini.py
# Choose option 2: Start development environment
```

3. **Verify installation**:
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API with proper headers
curl -H "X-Tenant-Id: gov-agency-a" -H "X-Session-Id: test-session" \
     http://localhost:8000/api/v1/rules
```

4. **Run integration tests**:
```bash
python test_jimini_integration.py
```

#### Production Deployment

1. **Create deployment configuration**:
```bash
python deploy_jimini.py
# Choose option 1: Create deployment files
# Choose option 3: Start production environment
```

2. **Using Docker Compose**:
```bash
docker-compose up -d
```

3. **Using systemd** (Linux servers):
```bash
# Copy service file
sudo cp jimini-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jimini-gateway
sudo systemctl start jimini-gateway
```

### 📡 **API Endpoints**

#### Core APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/rules` | GET | Get all rules |
| `/api/v1/rules/validate` | POST | Validate rule syntax |
| `/api/v1/rules/dryrun` | POST | Test rule against content |
| `/api/v1/rules/publish` | POST | Publish rule to active set |
| `/api/v1/decisions` | GET | Get filterable decisions |
| `/api/v1/decisions/{id}` | GET | Get specific decision |
| `/api/v1/coverage` | GET | Get coverage metrics |

#### Policy Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/policies/proposals` | GET | Get policy proposals |
| `/api/v1/policies/proposals/{id}/approve` | POST | Approve proposal |
| `/api/v1/policies/proposals/{id}/decline` | POST | Decline proposal |

#### Break-Glass Access

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/reveal` | POST | Reveal masked field (audit logged) |

#### Required Headers
- `X-Tenant-Id`: Tenant identifier (e.g., `gov-agency-a`)
- `X-Session-Id`: Session identifier for tracking

### 🔧 **Configuration**

#### Environment Variables

```bash
# Gateway Configuration
JIMINI_ENVIRONMENT=production
JIMINI_HOST=0.0.0.0
JIMINI_PORT=8000
JIMINI_LOG_LEVEL=info
JIMINI_WORKERS=4

# Database
DATABASE_URL=postgresql://jimini:password@db:5432/jimini_prod

# Redis
REDIS_URL=redis://redis:6379/0

# PKI System Integration
LDAP_BIND_PASSWORD=secure_password
ENTRUST_API_KEY=your_api_key
UMS_AUTH_TOKEN=your_token
DB2_CONNECTION_STRING=your_connection_string
SNOW_USERNAME=username
SNOW_PASSWORD=password
```

#### Rule Configuration

Rules are defined in YAML format with the following structure:

```yaml
id: "PII-SSN-1"
name: "Social Security Number Detection"
pattern: "\\b\\d{3}-?\\d{2}-?\\d{4}\\b"
action: "block"  # allow, flag, block
severity: "critical"  # low, medium, high, critical
system_scope: ["llm", "service_now"]
enabled: true
citations:
  - doc: "Data Protection Policy"
    section: "3.1.2"
    url: "sharepoint://policies/data#3.1.2"
```

#### Masking Configuration

```yaml
mode: enforce  # shadow, assist, enforce
llm:
  enabled: true
  mask_before_send: true
masking:
  strategy: deterministic_pseudo
  secret_fields: ["api_key", "token", "authorization"]
  deny_fields: ["user.ssn", "user.dob"]
  allow_fields: ["ticket.id", "ticket.status"]
```

### 🔌 **PKI System Integration**

#### LDAP Integration
```python
from pki_adapters import LDAPAdapter

adapter = LDAPAdapter("ldap://ldap.agency.gov", engine)
result = await adapter.search(
    base_dn="ou=users,dc=agency,dc=gov",
    search_filter="(cn=john*)",
    attributes=["cn", "mail"],
    tenant_id="gov-agency-a",
    session_id="session_001"
)
```

#### ServiceNow Integration
```python
from pki_adapters import ServiceNowAdapter

adapter = ServiceNowAdapter("https://agency.service-now.com", "user", "pass", engine)
incident = await adapter.create_incident({
    "short_description": "System issue",
    "description": "User needs assistance",
    "priority": "Medium"
}, tenant_id="gov-agency-a", session_id="session_001")
```

### 📊 **React Dashboard Integration**

The React dashboard provides a complete interface for managing policies and monitoring decisions:

```jsx
import JiminiGovernmentDashboard from './react_jimini_dashboard';

// In your React app
function App() {
  return <JiminiGovernmentDashboard />;
}
```

#### Dashboard Features
- **Coverage Metrics**: Real-time policy enforcement statistics
- **Decision Logs**: Filterable audit trail with break-glass access
- **Rule Management**: Create, test, and publish policy rules
- **System Monitoring**: Per-system breakdown of activity

### 🛡️ **Security Features**

#### PII Protection
- **Deterministic Pseudonymization**: HMAC-SHA256 with tenant+session salt
- **Format-Preserving Masking**: Show partial data (e.g., `***-**-1234`)
- **One-Way Redaction**: Irreversible masking for secrets
- **Field-Level Control**: Configurable allow/deny lists

#### Decision Logging Schema
```json
{
  "ts": "2025-10-02T14:05:01Z",
  "direction": "outbound",
  "system": "service_now",
  "endpoint": "/tickets/create",
  "decision": "FLAG",
  "rule_ids": ["PII-TICKETS-1"],
  "masked_fields": ["ticket.description","user.email"],
  "citations": [{
    "doc": "Data Retention Policy",
    "section": "1.2.3",
    "url": "sharepoint://policies/data#1.2.3"
  }],
  "latency_ms": 28.7,
  "tenant": "gov-agency-a",
  "request_id": "req_abc123"
}
```

### 🧪 **Testing**

#### Unit Tests
```bash
# Run comprehensive test suite
python test_jimini_integration.py

# Test specific functionality
pytest tests/ -v
```

#### Integration Testing
The test suite covers:
- ✅ API endpoint functionality
- ✅ PKI adapter integration
- ✅ PII masking accuracy
- ✅ Rule engine behavior
- ✅ Decision logging
- ✅ Performance benchmarks

#### Test Scenarios
- **Government Citizen Lookup**: LDAP → UMS → DB2 integration
- **ServiceNow Incident Creation**: PII detection and masking
- **LLM Integration**: Content filtering and pseudonymization

### 📈 **Performance & Monitoring**

#### Metrics
- **Coverage Rate**: Percentage of requests with policy decisions
- **Response Time**: Per-endpoint latency tracking
- **System Breakdown**: Activity by PKI system
- **Rule Effectiveness**: Matches per rule over time

#### Health Checks
```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "healthy",
  "service": "jimini-gateway",
  "version": "1.0.0",
  "timestamp": "2025-10-02T22:03:07Z",
  "active_rules": 4,
  "total_decisions": 156,
  "mode": "enforce"
}
```

### 🔄 **Rule Lifecycle Management**

#### 1. Validate
```bash
curl -X POST -H "X-Tenant-Id: gov-agency-a" -H "X-Session-Id: session" \
     -H "Content-Type: application/json" \
     -d '{"id": "TEST-1", "name": "Test Rule", "pattern": "\\btest\\b", "action": "flag", "severity": "low", "system_scope": ["llm"], "enabled": true}' \
     http://localhost:8000/api/v1/rules/validate
```

#### 2. Dry-Run
```bash
curl -X POST -H "X-Tenant-Id: gov-agency-a" -H "X-Session-Id: session" \
     -H "Content-Type: application/json" \
     -d '{"id": "TEST-1", "name": "Test Rule", "pattern": "\\btest\\b", "action": "flag", "severity": "low", "system_scope": ["llm"], "enabled": true, "test_content": "This is test content"}' \
     http://localhost:8000/api/v1/rules/dryrun
```

#### 3. Publish
```bash
curl -X POST -H "X-Tenant-Id: gov-agency-a" -H "X-Session-Id: session" \
     -H "Content-Type: application/json" \
     -d '{"id": "TEST-1", "name": "Test Rule", "pattern": "\\btest\\b", "action": "flag", "severity": "low", "system_scope": ["llm"], "enabled": true}' \
     http://localhost:8000/api/v1/rules/publish
```

### 🚨 **Troubleshooting**

#### Common Issues

**Gateway not starting**:
```bash
# Check port availability
sudo netstat -tlnp | grep 8000

# Check Python dependencies
pip install -r requirements.txt

# View detailed logs
python jimini_gateway.py --log-level debug
```

**API returning 401 Unauthorized**:
- Ensure `X-Tenant-Id` and `X-Session-Id` headers are included
- Verify tenant ID format (e.g., `gov-agency-a`)

**Rules not enforcing**:
- Check mode setting (shadow/assist/enforce)
- Verify rule system_scope matches target system
- Test rule pattern with dry-run endpoint

**PKI adapter connection issues**:
- Verify environment variables for system credentials
- Check network connectivity to target systems
- Review adapter configuration in deployment files

### 📚 **Additional Resources**

- **API Documentation**: http://localhost:8000/docs (when running)
- **Government Compliance**: Built for HIPAA, PII Protection standards
- **Enterprise Support**: Contact for production deployment assistance

### 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### 📄 **License**

Enterprise Government License - Contact for licensing terms.

---

**🛡️ Jimini - Protecting Government Data at Scale**