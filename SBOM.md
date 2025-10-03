# Software Bill of Materials (SBOM) - Jimini v0.2.0

## Package Information
- **Name**: jimini
- **Version**: 0.2.0  
- **License**: MIT
- **Build Date**: 2025-01-16
- **Repository**: https://github.com/jimini-ai/jimini

## Runtime Dependencies

### Core Dependencies (Required)
```
fastapi>=0.104.0          # Web framework (Apache 2.0)
uvicorn[standard]>=0.24.0 # ASGI server (BSD-3-Clause)  
pydantic>=2.5.0           # Data validation (MIT)
PyYAML>=6.0               # YAML parsing (MIT)
python-dotenv>=1.0.0      # Environment variables (BSD-3-Clause)
PyJWT>=2.8.0              # JWT tokens (MIT)
```

### Optional Dependencies

#### Server Integration [server]
```
openai>=1.0.0             # LLM integration (MIT)
elasticsearch>=8.0.0      # Elasticsearch client (Apache 2.0)
splunk-sdk>=1.7.0         # Splunk integration (Apache 2.0)
requests>=2.31.0          # HTTP client (Apache 2.0)
```

#### Telemetry [monitoring]
```
opentelemetry-api>=1.20.0        # OTEL API (Apache 2.0)
opentelemetry-sdk>=1.20.0        # OTEL SDK (Apache 2.0)
opentelemetry-exporter-otlp>=1.20.0  # OTLP exporter (Apache 2.0)
prometheus-client>=0.19.0        # Prometheus metrics (Apache 2.0)
psutil>=5.9.0                    # System metrics (BSD-3-Clause)
```

#### Development [dev]
```
pytest>=7.4.0            # Testing framework (MIT)
pytest-asyncio>=0.21.0   # Async testing (Apache 2.0) 
pytest-cov>=4.1.0        # Coverage reporting (MIT)
ruff>=0.1.0               # Linter/formatter (MIT)
black>=23.0.0             # Code formatter (MIT)
mypy>=1.7.0               # Type checking (MIT)
pre-commit>=3.5.0         # Git hooks (MIT)
```

#### Security Scanning [security]
```
bandit[toml]>=1.7.5       # Security linter (Apache 2.0)
safety>=2.3.0             # Vulnerability scanner (MIT)
pip-audit>=2.6.0          # Dependency audit (Apache 2.0)
```

## Python Standard Library Dependencies
- `os` - Operating system interface
- `sys` - System-specific parameters  
- `json` - JSON encoder/decoder
- `time` - Time access and conversions
- `typing` - Type hints support
- `asyncio` - Asynchronous I/O
- `hashlib` - Cryptographic hashing
- `threading` - Threading primitives
- `contextlib` - Context managers
- `collections` - Container datatypes

## Included Policy Packs
- **CJIS** - Criminal Justice Information Services compliance
- **HIPAA** - Healthcare privacy and security rules
- **PCI** - Payment Card Industry standards
- **Illinois** - Illinois state privacy regulations  
- **Secrets** - API keys, tokens, and credential detection

## Security Considerations
- All dependencies use permissive licenses (MIT, Apache 2.0, BSD)
- No GPL or copyleft dependencies
- Security scanning enabled with `bandit`, `safety`, `pip-audit`
- JWT authentication for admin endpoints
- PII redaction for compliance
- Circuit breaker pattern for resilience

## Build Information
- **Python**: >=3.10
- **Build System**: setuptools + wheel
- **Package Format**: Python wheel (.whl)
- **Entry Points**: CLI scripts included
- **Data Files**: Policy packs, configuration templates

## Verification
This SBOM can be verified against the actual package contents:
```bash
pip show jimini
pip list --format=json | jq '.[] | select(.name=="jimini")'
```

---
Generated: 2025-01-16
Jimini v0.2.0 - AI Policy Enforcement Gateway