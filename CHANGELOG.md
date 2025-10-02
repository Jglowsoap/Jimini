# Changelog

All notable changes to Jimini will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-16

### Added
- **Security & Compliance Infrastructure (Phase 4C)**
  - PII redaction system with 7 rule types (email, tokens, UUIDs, SSN, phone, IP, credit cards)
  - RBAC (Role-Based Access Control) with JWT authentication
  - 4-tier role hierarchy: ADMIN → REVIEWER → SUPPORT → USER
  - Admin security endpoints with role protection
  - Enhanced audit records with compliance fields
  
- **Configuration & Secrets Management (Phase 4A)**
  - Typed Pydantic configuration system with fail-fast validation
  - Environment variable merging with `python-dotenv` support
  - Secret masking for security compliance
  - Conditional validation for integration configs
  
- **Robust Error Handling (Phase 4B)**
  - Circuit breaker pattern with three states (CLOSED/OPEN/HALF_OPEN)
  - Dead letter queue for failed events with replay capability
  - Resilient forwarder base class with exponential backoff
  - Thread-safe circuit breaker manager
  
- **Professional Packaging (Phase 4D)**
  - Modern `pyproject.toml` with SemVer 0.2.0
  - Console scripts: `jimini`, `jimini-server`, `jimini-admin`
  - Optional dependencies for server, dev, security, monitoring
  - Version management with `app/__version__.py`
  - Enhanced package metadata for PyPI readiness

### Enhanced
- **FastAPI Application**
  - Added RBAC-protected admin endpoints
  - Enhanced error handling with circuit breakers
  - PII-safe telemetry and event logging
  - Shadow mode logic with per-rule overrides
  
- **CLI Tools**
  - Added `jimini-admin` with comprehensive system management
  - Enhanced telemetry commands (counters, flush)
  - Circuit breaker management (status, reset)
  - Configuration validation and display
  
- **Audit System**
  - SHA-3 256 tamper-evident chain
  - PII redaction integration
  - Enhanced audit record structure
  - Chain verification endpoints

### Technical Improvements
- Type annotations throughout codebase
- Comprehensive test coverage for security features
- Development tools configuration (pytest, ruff, black, mypy)
- Security scanning tools (bandit, safety, pip-audit)
- Package data inclusion for policy packs

### Dependencies
- Added `PyJWT>=2.8.0` for authentication
- Added `python-dotenv>=1.0.0` for configuration
- Enhanced optional dependencies structure
- Development and security dependency groups

## [0.1.0] - 2024-12-XX

### Added
- Initial Jimini AI Policy Gateway implementation
- FastAPI-based REST API with `/v1/evaluate` endpoint
- YAML-based policy rules engine
- Regex, character count, and LLM-based policy checks
- Audit logging with JSONL format
- Basic telemetry and metrics
- CLI tools for rule testing and validation
- Shadow mode support
- OpenTelemetry integration support
- Webhook notifications
- Multi-forwarder support (Splunk, Elastic, JSONL)

### Core Features
- Policy rule evaluation with precedence (block > flag > allow)
- Hot-reloading of YAML rule files
- API key authentication
- Endpoint-specific rule filtering
- Request/response direction support
- Rule suppression logic (API-1.0 when specific secrets match)

---

### Version History
- **v0.2.0** - Security & Compliance Enterprise Features
- **v0.1.0** - Initial AI Policy Gateway Release

### Upgrade Notes
When upgrading from v0.1.0 to v0.2.0:
1. Update `pyproject.toml` dependencies
2. Review new configuration options in `config/loader.py`
3. Enable PII redaction if handling sensitive data
4. Configure RBAC if using admin endpoints
5. Test circuit breaker functionality with your forwarders