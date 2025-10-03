# 🤖 Replit AI Age### **Port**: 5000 (FastAPI serves everything)
- **Entry Point**: Direct `uvicorn app.main:app` (no wrapper needed) Briefing: Jimini Security Gateway

**CRITICAL INSTRUCTIONS FOR REPLIT AI AGENT**

## 🎯 Project Overview

**Jimini** is a **security gateway/policy engine** that sits between PKI systems and external services. It is **NOT** a government service simulator - it's a security filter that prevents PII/sensitive data leaks.

```
PKI Systems → Jimini Gateway → External APIs
(LDAP, Entrust IDG, UMS, DB2, ServiceNow)
```

## 🏗️ Architecture Requirements

### **CRITICAL: This is FastAPI, NOT Flask/Django**
- **Backend**: FastAPI application (Python)
- **Frontend**: React components served BY FastAPI (not separate Node server)
- **Port**: 8000 (FastAPI serves everything)
- **Entry Point**: `main.py` → imports `app/main.py`

### **Project Structure (MUST MATCH)**
```
jimini-security-gateway/
├── main.py                    # Replit entry point (REQUIRED)
├── requirements.txt           # Python deps
├── .replit                   # Replit config
├── replit.nix               # Environment
├── app/                     # FastAPI application
│   ├── __init__.py
│   ├── main.py             # FastAPI app instance
│   ├── config.py
│   ├── enforcement.py      # Policy engine
│   ├── models.py          # Pydantic models
│   ├── audit.py           # Audit logging
│   └── rules_loader.py    # YAML rule loader
├── frontend/              # React components
│   ├── index.html
│   └── components/
├── packs/                 # Policy rule packs
│   └── government/
│       └── v1_fixed.yaml  # REQUIRED rules file
└── logs/                  # Audit logs
    └── audit.jsonl
```

## 🔧 Critical Dependencies

**USE EXISTING requirements.txt (WORKING VERSIONS):**
```txt
fastapi>=0.95.0
uvicorn>=0.21.1
pydantic>=2.0.0
pyyaml>=6.0
cryptography>=41.0.0
opentelemetry-api>=1.19.0
prometheus_client>=0.17.0
structlog>=23.1.0
# Plus additional dependencies in requirements.txt
```

## 🌐 Required API Endpoints

**These endpoints MUST work or the gateway fails:**

### Core Security API
- `POST /v1/evaluate` - **PRIMARY ENDPOINT** - Policy evaluation
- `GET /v1/decisions` - Decision history  
- `POST /v1/rules` - Rule management
- `GET /v1/policies` - Policy listing

### System Endpoints  
- `GET /health` - Health check (MUST return 200)
- `GET /` - Root redirect to dashboard
- `GET /dashboard` - React dashboard UI

### Expected Request/Response
```bash
# Test command (MUST work)
curl -X POST "https://your-repl.repl.co/v1/evaluate" \
  -H "Authorization: Bearer changeme123" \
  -H "Content-Type: application/json" \
  -d '{"text": "SSN: 123-45-6789", "endpoint": "/test"}'

# Expected response
{
  "decision": "block",
  "rule_ids": ["IL-AI-4.2"],
  "message": "Block any full SSN patterns",
  "audit_id": "audit_123456"
}
```

## 🔒 Environment Variables (Secrets Tab)

**REQUIRED in Replit Secrets (EXACT NAMES):**
```bash
API_KEY=changeme123
RULES_PATH=policy_rules.yaml
JIMINI_SHADOW=1
```

**Optional:**
```bash
AUDIT_LOG_PATH=logs/audit.jsonl
WEBHOOK_URL=https://your-alerts.com/jimini
OPENAI_API_KEY=your-key-here
```

## 🚨 CRITICAL MISTAKES TO AVOID

### ❌ **DO NOT DO THESE:**
1. **Don't use Flask** - This is FastAPI only
2. **Don't create separate Node.js server** - React served by FastAPI  
3. **Don't change entry point structure** - Must be `main.py` → `app/main.py`
4. **Don't skip rule files** - Gateway won't work without `packs/government/v1_fixed.yaml`
5. **Don't use different ports** - FastAPI on 8000, serves everything
6. **Don't modify core dependencies** - Versions are locked for compatibility

### ✅ **MUST DO THESE:**
1. **Use exact file structure shown above**
2. **Import FastAPI app correctly in main.py**
3. **Set all required environment variables**
4. **Test `/health` endpoint first**
5. **Verify `/v1/evaluate` works with test data**

## 📝 Entry Point Template

**Create exactly this `main.py` in root:**
```python
#!/usr/bin/env python3
"""
Jimini Security Gateway - Replit Deployment
==========================================
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Set environment variables for Replit
os.environ.setdefault("JIMINI_API_KEY", "changeme123")
os.environ.setdefault("JIMINI_RULES_PATH", "packs/government/v1_fixed.yaml")
os.environ.setdefault("JIMINI_SHADOW", "0")
os.environ.setdefault("AUDIT_LOG_PATH", "logs/audit.jsonl")

def main():
    print("🛡️ Starting Jimini Security Gateway on Replit...")
    
    # Import the FastAPI app from app/main.py
    from main import app
    
    # Get port from Replit environment  
    port = int(os.getenv("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
```

## 🧪 Testing Checklist

**After deployment, verify these work:**

1. **Health Check**: `GET /health` → Returns 200
2. **Dashboard**: `GET /dashboard` → Shows React UI  
3. **Policy Test**: `POST /v1/evaluate` with SSN → Returns "block"
4. **Rules Loading**: Check logs for "Rules loaded successfully"

## 🔍 Debugging Guide

### **If service won't start:**
- Check `requirements.txt` is exactly as specified
- Verify `JIMINI_RULES_PATH` points to existing file
- Check Python path in `main.py`

### **If endpoints return 404:**
- Verify FastAPI app is imported correctly
- Check `app/main.py` exists and has `app = FastAPI()` 
- Ensure all route decorators are present

### **If policy evaluation fails:**
- Check rule files exist in `packs/government/`
- Verify YAML syntax is valid
- Check environment variables in Secrets

## 🎯 Success Criteria

**Deployment is successful when:**
- ✅ Replit shows "🛡️ Starting Jimini Security Gateway"
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Dashboard loads at `/dashboard`
- ✅ Policy test blocks SSN data
- ✅ No import errors in console

## 📞 Emergency Contacts

If you encounter issues:
1. **Check the deployment guide**: `REPLIT_DEPLOYMENT_GUIDE.md`
2. **Verify file structure matches exactly**  
3. **Test with provided curl commands**
4. **Check Replit console logs for errors**

---

**🚨 REMEMBER: Jimini is a security gateway that filters PKI system traffic. It's not a government service - it protects government services by filtering their API calls.**