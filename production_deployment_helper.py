"""
🚀 PRODUCTION DEPLOYMENT HELPER
===============================

This script helps you deploy your complete Jimini Platform integration
to production with proper configuration and security settings.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

class ProductionDeploymentHelper:
    """Helper for deploying Jimini Platform integration to production"""
    
    def __init__(self):
        self.config = {}
        
    def generate_production_config(self) -> Dict[str, Any]:
        """Generate production configuration"""
        
        config = {
            "jimini": {
                "url": "https://your-jimini-service.your-domain.com",
                "api_key": "${JIMINI_API_KEY}",  # Use environment variable
                "rules_path": "packs/government/production_v1.yaml",
                "shadow_mode": False,  # Disable shadow mode in production
                "timeout": 30,
                "retry_attempts": 3
            },
            "flask": {
                "host": "0.0.0.0",
                "port": 5001,
                "debug": False,  # Never debug in production
                "secret_key": "${FLASK_SECRET_KEY}",
                "cors_origins": [
                    "https://your-dashboard.your-domain.com",
                    "https://admin.your-domain.com"
                ]
            },
            "security": {
                "enable_rate_limiting": True,
                "max_requests_per_minute": 100,
                "require_api_keys": True,
                "audit_all_requests": True,
                "encrypt_audit_logs": True
            },
            "monitoring": {
                "webhook_url": "${SECURITY_WEBHOOK_URL}",
                "otel_endpoint": "${OTEL_ENDPOINT}",
                "log_level": "INFO",
                "metrics_enabled": True
            },
            "compliance": {
                "generate_sarif_reports": True,
                "audit_retention_days": 2555,  # 7 years for government
                "pii_encryption": True,
                "gdpr_compliant": True
            }
        }
        
        return config
    
    def generate_production_rules(self) -> str:
        """Generate production-ready government rules"""
        
        rules = {
            "rules": [
                {
                    "id": "SSN-PRODUCTION-BLOCK",
                    "title": "Social Security Number - Production Block",
                    "pattern": r"\b\d{3}-?\d{2}-?\d{4}\b",
                    "action": "block",
                    "severity": "critical",
                    "applies_to": ["*"],
                    "endpoints": ["/*"],
                    "tags": ["pii", "government", "ssn", "production"],
                    "shadow_override": "enforce",
                    "description": "Blocks all SSN patterns in production"
                },
                {
                    "id": "DRIVERS-LICENSE-PRODUCTION",
                    "title": "Driver's License - Production Flag",
                    "pattern": r"[A-Z]\d{7,9}",
                    "action": "flag",
                    "severity": "high", 
                    "applies_to": ["government", "dmv"],
                    "endpoints": ["/government/*", "/dmv/*"],
                    "tags": ["pii", "government", "license", "production"]
                },
                {
                    "id": "CREDIT-CARD-PRODUCTION",
                    "title": "Credit Card - Production Block",
                    "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
                    "action": "block",
                    "severity": "critical",
                    "applies_to": ["*"],
                    "endpoints": ["/*"],
                    "tags": ["pii", "financial", "production"],
                    "shadow_override": "enforce"
                },
                {
                    "id": "API-SECRETS-PRODUCTION",
                    "title": "API Secrets - Production Block",
                    "pattern": r"(?i)\b(?:api[_-]?key|token|secret|password)[\"\\s]*[:=][\"\\s]*[a-zA-Z0-9_-]{15,}",
                    "action": "block",
                    "severity": "critical",
                    "applies_to": ["*"],
                    "endpoints": ["/*"],
                    "tags": ["secret", "api", "production"],
                    "shadow_override": "enforce"
                },
                {
                    "id": "PHONE-PRODUCTION",
                    "title": "Phone Numbers - Production Flag",
                    "pattern": r"\(?\\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
                    "action": "flag",
                    "severity": "medium",
                    "applies_to": ["*"],
                    "endpoints": ["/*"],
                    "tags": ["pii", "contact", "production"]
                },
                {
                    "id": "EMAIL-PRODUCTION",
                    "title": "Email Addresses - Production Flag",
                    "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                    "action": "flag",
                    "severity": "low",
                    "applies_to": ["*"],
                    "endpoints": ["/*"],
                    "tags": ["pii", "contact", "production"]
                }
            ]
        }
        
        return yaml.dump(rules, default_flow_style=False)
    
    def generate_docker_compose(self) -> str:
        """Generate Docker Compose for production deployment"""
        
        compose = {
            "version": "3.8",
            "services": {
                "jimini-platform": {
                    "build": ".",
                    "ports": ["9000:9000"],
                    "environment": [
                        "JIMINI_API_KEY=${JIMINI_API_KEY}",
                        "JIMINI_RULES_PATH=packs/government/production_v1.yaml",
                        "JIMINI_SHADOW=0",
                        "WEBHOOK_URL=${SECURITY_WEBHOOK_URL}",
                        "OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_ENDPOINT}",
                        "AUDIT_LOG_PATH=/secure/logs/jimini-audit.jsonl"
                    ],
                    "volumes": [
                        "./packs:/app/packs:ro",
                        "audit-logs:/secure/logs"
                    ],
                    "restart": "unless-stopped",
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:9000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    }
                },
                "flask-gateway": {
                    "build": "./flask",
                    "ports": ["5001:5001"],
                    "depends_on": ["jimini-platform"],
                    "environment": [
                        "JIMINI_URL=http://jimini-platform:9000",
                        "JIMINI_API_KEY=${JIMINI_API_KEY}",
                        "FLASK_SECRET_KEY=${FLASK_SECRET_KEY}"
                    ],
                    "restart": "unless-stopped"
                },
                "nginx": {
                    "image": "nginx:alpine",
                    "ports": ["80:80", "443:443"],
                    "depends_on": ["flask-gateway"],
                    "volumes": [
                        "./nginx.conf:/etc/nginx/nginx.conf:ro",
                        "./ssl:/etc/ssl:ro"
                    ],
                    "restart": "unless-stopped"
                }
            },
            "volumes": {
                "audit-logs": {
                    "driver": "local",
                    "driver_opts": {
                        "type": "none",
                        "o": "bind",
                        "device": "/secure/audit-logs"
                    }
                }
            }
        }
        
        return yaml.dump(compose, default_flow_style=False)
    
    def generate_environment_template(self) -> str:
        """Generate .env template for production"""
        
        env_template = """# Jimini Platform Production Configuration
# Copy to .env and fill in your values

# Jimini Platform
JIMINI_API_KEY=your_secure_api_key_here
JIMINI_URL=https://your-jimini-service.your-domain.com

# Flask Gateway  
FLASK_SECRET_KEY=your_flask_secret_key_here

# Security & Monitoring
SECURITY_WEBHOOK_URL=https://your-security-alerts.your-domain.com/jimini
OTEL_ENDPOINT=https://your-tracing.your-domain.com

# Database (if needed)
DATABASE_URL=postgresql://user:password@localhost:5432/jimini_gov

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/your-cert.pem
SSL_KEY_PATH=/etc/ssl/private/your-key.pem

# Compliance
AUDIT_RETENTION_DAYS=2555
PII_ENCRYPTION_KEY=your_encryption_key_here

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=100
MAX_REQUESTS_PER_HOUR=1000
"""
        
        return env_template
    
    def generate_nginx_config(self) -> str:
        """Generate Nginx configuration for production"""
        
        nginx_config = """events {
    worker_connections 1024;
}

http {
    upstream flask_backend {
        server flask-gateway:5001;
    }
    
    upstream jimini_backend {
        server jimini-platform:9000;
    }

    server {
        listen 80;
        server_name your-dashboard.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-dashboard.your-domain.com;

        ssl_certificate /etc/ssl/certs/your-cert.pem;
        ssl_certificate_key /etc/ssl/private/your-key.pem;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
        
        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        limit_req zone=api burst=20 nodelay;
        
        # Flask Gateway (Government APIs)
        location /api/ {
            proxy_pass http://flask_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Security timeouts
            proxy_connect_timeout 10s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Direct Jimini access (admin only)
        location /jimini/ {
            # Restrict to admin IPs only
            allow 10.0.0.0/8;
            allow 172.16.0.0/12; 
            allow 192.168.0.0/16;
            deny all;
            
            proxy_pass http://jimini_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # Static files (React app)
        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
    }
}"""
        
        return nginx_config
    
    def save_all_configs(self, output_dir: str = "production_config"):
        """Save all production configuration files"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"🏗️ Generating production configuration in: {output_path}")
        
        # Save production config
        config = self.generate_production_config()
        with open(output_path / "production_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ production_config.json")
        
        # Save production rules
        rules = self.generate_production_rules()
        with open(output_path / "production_rules.yaml", 'w') as f:
            f.write(rules)
        print("✅ production_rules.yaml")
        
        # Save Docker Compose
        compose = self.generate_docker_compose()
        with open(output_path / "docker-compose.yml", 'w') as f:
            f.write(compose)
        print("✅ docker-compose.yml")
        
        # Save environment template
        env_template = self.generate_environment_template()
        with open(output_path / ".env.template", 'w') as f:
            f.write(env_template)
        print("✅ .env.template")
        
        # Save Nginx config
        nginx_config = self.generate_nginx_config()
        with open(output_path / "nginx.conf", 'w') as f:
            f.write(nginx_config)
        print("✅ nginx.conf")
        
        # Generate deployment instructions
        instructions = self.generate_deployment_instructions()
        with open(output_path / "DEPLOYMENT.md", 'w') as f:
            f.write(instructions)
        print("✅ DEPLOYMENT.md")
        
        print(f"\n🚀 Production configuration ready!")
        print(f"📂 Configuration saved in: {output_path.absolute()}")
        print(f"📖 Read DEPLOYMENT.md for next steps")
    
    def generate_deployment_instructions(self) -> str:
        """Generate deployment instructions"""
        
        instructions = """# 🚀 Jimini Platform Production Deployment Guide

## 📋 Prerequisites

- Docker & Docker Compose installed
- SSL certificates for HTTPS
- Domain names configured
- Government security clearances (if applicable)

## 🔧 Setup Steps

### 1. Environment Configuration
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your values
nano .env
```

### 2. SSL Certificates
```bash
# Create SSL directory
mkdir -p ssl/certs ssl/private

# Copy your certificates
cp your-cert.pem ssl/certs/
cp your-key.pem ssl/private/
chmod 600 ssl/private/your-key.pem
```

### 3. Rule Configuration
```bash
# Copy production rules to packs directory
mkdir -p packs/government
cp production_rules.yaml packs/government/production_v1.yaml

# Customize rules for your needs
nano packs/government/production_v1.yaml
```

### 4. Deploy Services
```bash
# Build and start all services
docker-compose up -d

# Verify deployment
docker-compose ps
curl -f https://your-dashboard.your-domain.com/api/jimini/health
```

### 5. Security Verification
```bash
# Test PII protection
curl -X POST https://your-dashboard.your-domain.com/api/jimini/evaluate \\
  -H "Content-Type: application/json" \\
  -d '{"text": "SSN: 123-45-6789", "endpoint": "/test", "user_id": "admin"}'

# Should return: {"decision": "BLOCK", ...}
```

## 🔒 Security Checklist

- [ ] SSL/TLS certificates valid and configured
- [ ] API keys are strong and secured
- [ ] Rate limiting configured
- [ ] Firewall rules restrict access
- [ ] Audit logging enabled
- [ ] Webhook notifications configured
- [ ] Backup strategy implemented
- [ ] Monitoring alerts set up

## 📊 Monitoring

### Health Checks
- Jimini Platform: `https://your-domain.com/jimini/health`
- Flask Gateway: `https://your-domain.com/api/jimini/health`

### Log Files
- Audit logs: `/secure/audit-logs/`
- Application logs: `docker-compose logs -f`

### Metrics
- Prometheus: Configure OTEL endpoint
- Grafana: Import Jimini dashboard
- Alerts: Configure webhook notifications

## 🏛️ Government Compliance

### Audit Requirements
- 7-year log retention configured
- Tamper-proof audit chains enabled
- SARIF reports generated automatically
- Access controls enforced

### Privacy Protection
- PII encryption at rest
- Audit trail for all PII access
- User justification required
- Supervisor notifications enabled

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs jimini-platform
docker-compose logs flask-gateway

# Restart services
docker-compose restart
```

### Rules Not Loading
```bash
# Verify rules file
docker-compose exec jimini-platform cat /app/packs/government/production_v1.yaml

# Force reload
curl -X POST https://your-domain.com/api/jimini/rules/reload
```

### Connection Issues
```bash
# Test internal connectivity
docker-compose exec flask-gateway curl -f http://jimini-platform:9000/health

# Check network
docker network ls
docker network inspect production_config_default
```

## 📞 Support

For production support:
- Check logs first: `docker-compose logs`
- Verify configuration: Review .env and YAML files
- Test connectivity: Use curl commands above
- Contact support with log excerpts and configuration details

## 🎯 Success Metrics

Your deployment is successful when:
- [ ] Health checks return 200 OK
- [ ] SSN detection blocks requests  
- [ ] Audit logs are being written
- [ ] SARIF reports generate successfully
- [ ] React dashboard loads and functions
- [ ] Government APIs respond correctly

🏛️ **Your government dashboard now has enterprise-grade AI policy governance!**
"""
        
        return instructions

def main():
    """Generate production deployment configuration"""
    print("🏭 JIMINI PLATFORM PRODUCTION DEPLOYMENT HELPER")
    print("=" * 55)
    
    helper = ProductionDeploymentHelper()
    helper.save_all_configs()
    
    print(f"\n🎉 Production deployment configuration complete!")
    print(f"📂 Review the generated files and customize for your environment")
    print(f"📖 Follow DEPLOYMENT.md for step-by-step instructions")

if __name__ == "__main__":
    main()