# 🚀 Jimini Replit Deployment Guide

Complete instructions to deploy your Jimini Security Gateway to Replit for 24/7 operation.

## 📋 Prerequisites

1. **Replit Account** - Sign up at [replit.com](https://replit.com)
2. **GitHub Account** - For code repository integration
3. **Your Jimini Code** - From this codespace

## 🎯 Step 1: Create Replit Project

### Option A: Import from GitHub (Recommended)
1. Go to [replit.com](https://replit.com)
2. Click **"Create Repl"**
3. Select **"Import from GitHub"**
4. Enter your repository URL: `https://github.com/Jglowsoap/Jimini`
5. Choose **"Python"** as the language
6. Name your repl: `jimini-security-gateway`
7. Click **"Import from GitHub"**

### Option B: Create New Project
1. Click **"Create Repl"**
2. Select **"Python"** template
3. Name: `jimini-security-gateway`
4. Click **"Create Repl"**

## 📁 Step 2: Project Structure Setup

Copy these files from your codespace to Replit:

```
jimini-security-gateway/
├── main.py              # Entry point (we'll create)
├── requirements.txt     # Python dependencies
├── .replit             # Replit configuration
├── replit.nix          # Environment setup
├── package.json        # Frontend dependencies
├── app/                # Jimini Gateway code
│   ├── __init__.py
│   ├── main.py         # FastAPI app
│   ├── config.py
│   ├── enforcement.py
│   ├── models.py
│   ├── audit.py
│   └── rules_loader.py
├── frontend/           # React Dashboard
│   ├── index.html
│   ├── app.js
│   └── components/
├── packs/             # Rule packs
│   └── government/
├── logs/              # Audit logs
└── config/            # Configuration files
```

## 🔧 Step 3: Configuration Files

### Create `.replit` file:
```toml
run = "python main.py"
modules = ["python-3.11", "nodejs-20"]

[nix]
channel = "stable-23.05"

[deployment]
run = ["python", "main.py"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 8000
externalPort = 80

[[ports]]
localPort = 3000
externalPort = 3000

[env]
PYTHONPATH = "$REPL_HOME"
```

### Create `replit.nix` file:
```nix
{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.nodejs_20
    pkgs.nodePackages.npm
    pkgs.python311Packages.pip
  ];
}
```

### Create `main.py` (Replit entry point):
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
os.environ.setdefault("JIMINI_API_KEY", "your-secure-api-key-here")
os.environ.setdefault("JIMINI_RULES_PATH", "packs/government/v1_fixed.yaml")
os.environ.setdefault("JIMINI_SHADOW", "0")  # Enforce mode
os.environ.setdefault("AUDIT_LOG_PATH", "logs/audit.jsonl")

def main():
    print("🛡️ Starting Jimini Security Gateway on Replit...")
    
    # Import the FastAPI app
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

### Create `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pyyaml==6.0.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
aiofiles==23.2.1
structlog==23.2.0
prometheus-client==0.19.0
```

### Create `package.json` (for frontend):
```json
{
  "name": "jimini-dashboard",
  "version": "1.0.0",
  "description": "Jimini Security Gateway Dashboard",
  "main": "frontend/app.js",
  "scripts": {
    "build": "echo 'Frontend build complete'",
    "start": "echo 'Frontend served by FastAPI'"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@babel/core": "^7.23.0",
    "@babel/preset-react": "^7.22.0"
  }
}
```

## 🌍 Step 4: Environment Variables Setup

In Replit, go to **Secrets** tab (🔒 icon) and add:

```bash
# Required
JIMINI_API_KEY=your-super-secure-api-key-change-this
JIMINI_RULES_PATH=packs/government/v1_fixed.yaml
JIMINI_SHADOW=0

# Optional
AUDIT_LOG_PATH=logs/audit.jsonl
WEBHOOK_URL=https://your-webhook-url.com/jimini-alerts
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-monitoring-service.com

# Database (if using)
DATABASE_URL=postgresql://user:pass@host:port/db

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
```

## 🚀 Step 5: Deploy to Replit

1. **Upload Files**: Copy all your Jimini files to the Replit project
2. **Install Dependencies**: 
   ```bash
   pip install -r requirements.txt
   npm install
   ```
3. **Test Locally**: Click **"Run"** button in Replit
4. **Enable Always On**: 
   - Go to your repl settings
   - Enable **"Always On"** (requires Replit Pro)
5. **Get Public URL**: Replit provides automatic HTTPS URL

## 🔗 Step 6: Configure Public Access

### Get Your Jimini URLs:
- **API Base**: `https://your-repl-name.username.repl.co`
- **Dashboard**: `https://your-repl-name.username.repl.co/dashboard`
- **Health Check**: `https://your-repl-name.username.repl.co/health`

### Test Your Deployment:
```bash
# Health check
curl https://your-repl-name.username.repl.co/health

# API test
curl -X POST "https://your-repl-name.username.repl.co/v1/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"text": "Test message", "endpoint": "/test"}'
```

## 🛡️ Step 7: Security Configuration

### Update API Keys:
1. Change default API key in Secrets
2. Update JWT secret
3. Configure webhook URLs
4. Set up proper CORS origins

### Enable HTTPS Only:
```python
# In your FastAPI app
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

## 📊 Step 8: Connect Your PKI Systems

Update your PKI platform configuration to use Replit URLs:

```python
# Example: Connect from your PKI platform
JIMINI_GATEWAY_URL = "https://your-repl-name.username.repl.co"

# All API calls now go through Jimini
import requests

def protected_api_call(data):
    response = requests.post(
        f"{JIMINI_GATEWAY_URL}/v1/evaluate",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"text": data, "endpoint": "/pki/certificate"}
    )
    return response.json()
```

## 🔄 Step 9: Continuous Deployment

### Auto-Deploy from GitHub:
1. Connect your Replit to GitHub repository
2. Enable auto-deployment on push
3. Set up branch protection rules

### Manual Updates:
1. Update code in Replit editor
2. Click **"Run"** to restart
3. Test endpoints

## 📈 Step 10: Monitoring & Maintenance

### Check Service Health:
- Visit: `https://your-repl-name.username.repl.co/health`
- Monitor logs in Replit console
- Set up webhook alerts

### View Audit Logs:
- Access: `https://your-repl-name.username.repl.co/v1/decisions`
- Download logs via API
- Configure log retention

## 🆘 Troubleshooting

### Common Issues:

1. **Port Conflicts**:
   - Replit uses port 8000 by default
   - Update `main.py` if needed

2. **Environment Variables**:
   - Double-check Secrets tab
   - Restart repl after changes

3. **Module Import Errors**:
   - Verify `requirements.txt`
   - Check Python path in `main.py`

4. **Always On Not Working**:
   - Requires Replit Pro subscription
   - Alternative: Use external monitoring service

### Getting Help:
- Replit Discord: [discord.gg/replit](https://discord.gg/replit)
- Jimini GitHub Issues: Create issue in your repo
- Check Replit logs: Console tab in editor

## ✅ Final Checklist

- [ ] Replit project created
- [ ] All files uploaded
- [ ] Dependencies installed
- [ ] Environment variables set
- [ ] Service running successfully
- [ ] Health check passes
- [ ] API endpoints responding
- [ ] Dashboard accessible
- [ ] PKI systems configured
- [ ] Monitoring enabled
- [ ] Always On activated (optional)

## 🎉 Success!

Your Jimini Security Gateway is now running 24/7 on Replit! 

**Next Steps:**
1. Update your PKI platform to use the Replit URLs
2. Configure rule packs for your specific use case
3. Set up monitoring and alerting
4. Train your team on the dashboard

Your Jimini gateway will now protect all traffic between your PKI systems and external services with enterprise-grade security policies!
