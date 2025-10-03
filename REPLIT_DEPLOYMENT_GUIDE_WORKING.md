# 🎯 **REPLIT DEPLOYMENT GUIDE - WORKING CONFIGURATION**

**Based on Successfully Deployed Jimini Security Gateway**

## ✅ **Confirmed Working Setup**

Your Jimini is **FULLY FUNCTIONAL** with this configuration. Follow this **exact setup** for Replit deployment.

## 📋 **Prerequisites**

1. **Replit Account** - [replit.com](https://replit.com)
2. **GitHub Repository** - `https://github.com/Jglowsoap/Jimini`

## 🚀 **Step 1: Import to Replit**

1. Go to [replit.com](https://replit.com)
2. Click **"Create Repl"**
3. Select **"Import from GitHub"**
4. Enter: `https://github.com/Jglowsoap/Jimini`
5. Choose **"Python"** template
6. Name: `jimini-security-gateway`
7. Click **"Import from GitHub"**

## ⚙️ **Step 2: Environment Configuration**

In Replit **Secrets** tab (🔒), add these **exact variables**:

```bash
# Core Configuration (REQUIRED)
API_KEY=changeme123
RULES_PATH=policy_rules.yaml
JIMINI_SHADOW=1

# Optional Features
AUDIT_LOG_PATH=logs/audit.jsonl
OPENAI_API_KEY=your-key-here
WEBHOOK_URL=https://your-webhook.com/alerts
```

**⚠️ Critical:** Use `API_KEY` and `RULES_PATH` (not `JIMINI_API_KEY`/`JIMINI_RULES_PATH`)

## 🔧 **Step 3: Replit Configuration**

### Create `.replit` file:
```toml
run = "uvicorn app.main:app --host 0.0.0.0 --port 5000"
modules = ["python-3.11"]

[nix]
channel = "stable-23.05"

[deployment]
run = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 5000
externalPort = 80

[env]
PYTHONPATH = "$REPL_HOME"
```

### Create `replit.nix` file:
```nix
{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.pip
  ];
}
```

## 📦 **Step 4: Dependencies**

The existing `requirements.txt` has all needed packages. In Replit terminal:

```bash
pip install -r requirements.txt
```

## 🌐 **Step 5: Run & Test**

### Start the Server:
Click **▶️ Run** button or:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

### Test Endpoints:
```bash
# Health Check
curl https://your-repl.repl.co/health

# Policy Test  
curl -X POST "https://your-repl.repl.co/v1/evaluate" \
  -H "Authorization: Bearer changeme123" \
  -H "Content-Type: application/json" \
  -d '{"text": "SSN: 123-45-6789", "endpoint": "/test"}'

# Expected Response:
{
  "decision": "block",
  "rule_ids": ["IL-AI-4.2"],
  "message": "Block any full SSN patterns"
}
```

## 📊 **Step 6: Available Features**

### **✅ Working Endpoints:**
- `GET /health` - Service status
- `POST /v1/evaluate` - Policy evaluation  
- `GET /v1/metrics` - Performance metrics
- `GET /v1/audit/verify` - Audit chain verification
- `GET /v1/audit/sarif` - SARIF export

### **✅ Policy Rule Packs:**
- **22 Active Rules** in `policy_rules.yaml`
- PII Detection (SSN, Email, Phone)
- Secrets Detection (API keys, tokens)
- CJIS Criminal Justice compliance
- HIPAA Healthcare compliance  
- Illinois AI Act compliance
- PCI Payment Card compliance

### **✅ Security Features:**
- JWT Authentication
- Audit logging with tamper-evidence
- Shadow mode for testing
- Prometheus metrics
- OpenTelemetry integration
- Circuit breaker resilience

## 🔑 **Step 7: Authentication**

All API calls need Authorization header:
```bash
Authorization: Bearer changeme123
```

Update the `API_KEY` secret in Replit for production use.

## 📈 **Step 8: Always-On Deployment**

### Enable 24/7 Operation:
1. Upgrade to **Replit Pro** ($7/month)
2. Go to repl **Settings** → **"Always On"**
3. Enable **"Always On"** feature
4. Your gateway runs continuously

### Production URLs:
- **API Base**: `https://your-repl-name.username.repl.co`
- **Health**: `https://your-repl-name.username.repl.co/health`
- **Dashboard**: Use your existing React/Flask dashboard

## 🔄 **Step 9: GitHub Sync Workflow**

### Update Process:
```bash
# In this codespace - make changes
git add .
git commit -m "Update policy rules"
git push origin main

# In Replit - pull changes
git pull origin main
# Restart: Click Stop → Run
```

## 🛡️ **Step 10: Connect Your PKI Systems**

Update your PKI platform to use Replit endpoint:

```python
# Your PKI platform configuration
JIMINI_GATEWAY_URL = "https://your-repl-name.username.repl.co"

def check_policy(data, endpoint):
    response = requests.post(
        f"{JIMINI_GATEWAY_URL}/v1/evaluate",
        headers={"Authorization": "Bearer changeme123"},
        json={"text": data, "endpoint": endpoint}
    )
    return response.json()
```

## ✅ **Deployment Checklist**

- [ ] Replit project imported from GitHub
- [ ] Environment variables set (`API_KEY`, `RULES_PATH`, `JIMINI_SHADOW`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Server runs on port 5000
- [ ] Health check returns `{"ok": true, "loaded_rules": 22}`
- [ ] Policy evaluation blocks SSN test
- [ ] Authentication works with API key
- [ ] Always On enabled (for 24/7 operation)
- [ ] PKI systems updated to use Replit URL

## 🎉 **Success Indicators**

Your deployment is successful when you see:

```bash
🛡️ Jimini Security Gateway
✅ Server running on port 5000
✅ 22 policy rules loaded successfully
✅ Shadow mode: enabled
✅ API endpoints responding
✅ Authentication working
✅ Audit logging active
```

## 🚨 **Important Notes**

1. **Port**: Uses 5000 (not 8000 as in briefing)
2. **Entry Point**: Direct `uvicorn app.main:app` (no wrapper main.py needed)
3. **Environment**: Uses `API_KEY`/`RULES_PATH` (original variable names)
4. **Rules**: Uses `policy_rules.yaml` (22 working rules included)
5. **Architecture**: FastAPI-only (React dashboard separate)

## 🆘 **Troubleshooting**

### Common Issues:
1. **Import errors**: Run `pip install -r requirements.txt`
2. **Port conflicts**: Ensure .replit uses port 5000
3. **Auth failures**: Check `API_KEY` secret is set
4. **Rules not loading**: Verify `RULES_PATH=policy_rules.yaml`

### Expected Warnings (Safe to Ignore):
- LSP import warnings (cosmetic only)
- OpenTelemetry connection errors (optional feature)

---

**🎯 This guide reflects your WORKING configuration. Follow it exactly for guaranteed success!**