# 🚀 Jimini Deployment Guide

## Quick Replit Deployment (Recommended)

**✅ STORAGE OPTIMIZED - Under 100MB total deployment size**

### 1-Click Replit Setup:

1. **Fork this repo** to your Replit account
2. **Click "Run"** - that's it! 

The deployment script automatically:
- ✅ Installs only lightweight dependencies (`requirements_deploy.txt`)
- ✅ Skips heavy ML packages (torch, transformers, spacy, streamlit)
- ✅ Starts FastAPI server on port 8080
- ✅ Provides your API endpoint URL

### Your Jimini API will be available at:
```
https://your-repl-name.your-username.repl.co/v1/evaluate
```

### Test your deployment:
```bash
curl https://your-repl-name.your-username.repl.co/health
```

---

## 📦 Deployment Size Comparison

| Package Type | Size | Status |
|-------------|------|--------|
| **Lightweight** (`requirements_deploy.txt`) | ~60MB | ✅ Replit Compatible |
| Full with ML (`requirements.txt`) | ~2.5GB | ❌ Exceeds Replit quota |

---

## 🔧 Configuration

Set these in Replit Secrets or environment variables:

```bash
JIMINI_API_KEY=your-secure-api-key
OPENAI_API_KEY=sk-your-openai-key  # Optional, for LLM rules
JIMINI_RULES_PATH=policy_rules.yaml
JIMINI_SHADOW=0  # Set to 1 for shadow mode
```

---

## 🛡️ What's Included in Lightweight Deployment

✅ **Core Features (Available):**
- Full policy rule engine (415+ rules)
- API key/secret detection
- PII protection (SSN, credit cards, etc.)
- Real-time evaluation API
- Audit logging with tamper-evident chains
- SARIF export for security tools
- OpenAI integration for LLM-based rules
- Metrics and health monitoring

❌ **Advanced Features (Require Full Install):**
- Streamlit dashboard UI
- Advanced NLP with spaCy/transformers
- Local ML model processing
- Regulatory document parsing

---

## 🏗️ Other Deployment Options

### Docker Deployment
```bash
# Lightweight
docker build -f Dockerfile.lightweight .

# Full features
docker build -f Dockerfile .
```

### Local Development
```bash
# Lightweight (fast)
pip install -r requirements_deploy.txt
python replit_run.py

# Full features (requires ~2GB)
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

### Cloud Providers

**Replit** (Recommended for demos):
- ✅ Use `requirements_deploy.txt`
- ✅ 60MB total size
- ✅ 1-click deployment

**Heroku/Railway**:
- ✅ Use `requirements_deploy.txt` 
- ✅ Fits in free tier

**AWS Lambda**:
- ✅ Use `requirements_deploy.txt`
- ✅ Under 500MB limit

**Azure/GCP**:
- ✅ Either requirements file works
- ✅ Full ML features available

---

## 🧪 Testing Your Deployment

### Health Check
```bash
curl https://your-deployment-url/health
```

### Evaluate Text
```bash
curl -X POST https://your-deployment-url/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My API key is sk-1234567890abcdef",
    "api_key": "your-api-key"
  }'
```

### Expected Response
```json
{
  "action": "block",
  "rule_ids": ["OPENAI-KEY-1.0"],
  "message": "Evaluation completed. Decision: block"
}
```

---

## 🔄 Upgrading to Full Features

If you need dashboard UI and advanced ML features:

1. **Switch to full requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Enable intelligence features:**
   ```bash
   pip install spacy transformers
   python -m spacy download en_core_web_sm
   ```

3. **Run with dashboard:**
   ```bash
   streamlit run jimini_gui_dashboard.py
   ```

**Note:** Full install requires ~2.5GB and may not work on storage-constrained platforms.

---

## 🆘 Troubleshooting

### "Disk quota exceeded" during deployment:
- ✅ Use `requirements_deploy.txt` instead of `requirements.txt`
- ✅ Verify Replit config uses `replit_run.py`

### "Intelligence features not available" warning:
- ✅ This is normal for lightweight deployments
- ✅ Core policy engine still works fully

### API returns 401 "Invalid API key":
- ✅ Set `JIMINI_API_KEY` in Replit Secrets
- ✅ Use same key in your API requests

---

## 🎯 Production Deployment Checklist

- [ ] Set secure `JIMINI_API_KEY` (not "changeme")
- [ ] Configure `OPENAI_API_KEY` for LLM rules
- [ ] Set up audit log retention
- [ ] Configure webhook alerts (optional)
- [ ] Test all API endpoints
- [ ] Set up monitoring/health checks
- [ ] Review and customize policy rules

**Your Jimini Policy Gateway is ready to protect your applications! 🛡️**