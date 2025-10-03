# 🚀 Jimini Platform Production Deployment Guide

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
curl -X POST https://your-dashboard.your-domain.com/api/jimini/evaluate \
  -H "Content-Type: application/json" \
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
