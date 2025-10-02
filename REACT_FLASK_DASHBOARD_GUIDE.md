# Jimini React/Flask Dashboard Integration Guide

## 🎯 Overview

Your React/Flask dashboard is designed to integrate with the **full Jimini Platform** for enterprise-grade PII protection. This guide explains how to ensure your integration is working correctly.

## 🏗️ Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   React Frontend    │────▶│   Flask Gateway      │────▶│  Jimini Platform    │
│   (Your App)        │     │   (Port 5001)        │     │   (Port 9000)       │
│                     │     │                      │     │                     │
│ • User Interface    │     │ • API Gateway        │     │ • Rule Engine       │
│ • Form Validation   │     │ • Government APIs    │     │ • PII Detection     │
│ • Real-time PII     │     │ • Jimini Client      │     │ • Audit Chain       │
│ • Dashboard Views   │     │ • Request Routing    │     │ • Hot Reload        │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
```

## ✅ Quick Status Check

To verify your Jimini integration is working:

```bash
python check_jimini_status.py
```

This will tell you:
- ✅ Is Jimini Platform running?
- ✅ Are rules loaded correctly?
- ✅ Is Flask Gateway connected?
- ✅ Can API calls be made successfully?

## 🚀 Starting Services

### Automated (Recommended)

Use the service manager script to start everything:

```bash
# Start with default settings (policy_rules.yaml)
python start_jimini_services.py

# Start with shadow mode enabled (safe testing)
python start_jimini_services.py --shadow

# Start with custom rules
python start_jimini_services.py --rules packs/government/v1.yaml

# Start on custom port
python start_jimini_services.py --port 9001
```

### Manual

If you prefer to start services manually:

```bash
# 1. Set environment variables
export JIMINI_RULES_PATH=policy_rules.yaml
export JIMINI_API_KEY=changeme
export JIMINI_SHADOW=0  # Set to 1 for shadow mode

# 2. Start Jimini Platform
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000

# 3. In another terminal, start Flask Gateway (optional)
python flask_jimini_platform_integration.py
```

## 🔍 Verifying Integration

### 1. Check Jimini Health

```bash
curl http://localhost:9000/health | jq
```

Expected response:
```json
{
  "status": "ok",
  "shadow_mode": false,
  "loaded_rules": 26,
  "version": "0.2.0"
}
```

**⚠️ Important:** If `loaded_rules` is 0, your rules aren't loading properly!

### 2. Test PII Detection

```bash
curl -X POST http://localhost:9000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "changeme",
    "agent_id": "test",
    "text": "My SSN is 123-45-6789",
    "direction": "outbound",
    "endpoint": "/test"
  }' | jq
```

Expected response (with shadow mode OFF):
```json
{
  "action": "block",
  "rule_ids": ["IL-AI-4.2"],
  "message": "Evaluation completed. Decision: BLOCK"
}
```

Expected response (with shadow mode ON):
```json
{
  "action": "allow",
  "rule_ids": ["IL-AI-4.2"],
  "message": "Evaluation completed. Decision: ALLOW"
}
```

Note: In shadow mode, the decision is "allow" but `rule_ids` still shows what would have been blocked!

### 3. Test Flask Gateway (if running)

```bash
curl http://localhost:5001/api/jimini/health | jq
```

Expected response:
```json
{
  "status": "healthy",
  "jimini_connected": true,
  "jimini_url": "http://localhost:9000",
  "service": "jimini-platform-integration",
  "version": "enterprise-1.0.0"
}
```

## 📊 Understanding Shadow Mode

**Shadow Mode** is a safety feature that allows you to test Jimini without blocking anything:

| Setting | Behavior | Use Case |
|---------|----------|----------|
| `JIMINI_SHADOW=0` | **ENFORCE** - Actually blocks/flags content | Production deployment |
| `JIMINI_SHADOW=1` | **OBSERVE** - Logs what would be blocked but allows everything | Testing and validation |

**Key Point:** Even in shadow mode, all rule matches are logged to `rule_ids` so you can see what would happen!

## 🔧 Common Issues & Solutions

### Issue: "0 rules loaded"

**Symptoms:**
- `/health` endpoint shows `loaded_rules: 0`
- No PII is being detected

**Solutions:**
1. Verify rules file exists:
   ```bash
   ls -la policy_rules.yaml
   ```

2. Check environment variable:
   ```bash
   echo $JIMINI_RULES_PATH
   ```

3. Verify YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('policy_rules.yaml'))"
   ```

4. Check logs for errors:
   ```bash
   tail -f /tmp/jimini.log
   ```

### Issue: "Connection refused"

**Symptoms:**
- `curl http://localhost:9000/health` fails
- Flask gateway can't connect

**Solutions:**
1. Check if Jimini is running:
   ```bash
   ps aux | grep uvicorn
   ```

2. Check if port is in use:
   ```bash
   lsof -i :9000
   ```

3. Start Jimini:
   ```bash
   python start_jimini_services.py
   ```

### Issue: "Everything is ALLOW"

**Symptoms:**
- All evaluations return "allow"
- No blocking/flagging occurs

**Solutions:**
1. Check shadow mode:
   ```bash
   curl http://localhost:9000/health | jq .shadow_mode
   ```

2. Disable shadow mode:
   ```bash
   export JIMINI_SHADOW=0
   # Restart Jimini
   ```

3. Verify rules are loading:
   ```bash
   curl http://localhost:9000/health | jq .loaded_rules
   ```

## 📡 React Dashboard Integration

Your React components should make API calls like this:

```javascript
// Direct to Jimini Platform
const response = await fetch('http://localhost:9000/v1/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    api_key: 'changeme',
    agent_id: 'react_dashboard',
    text: userInput,
    direction: 'outbound',
    endpoint: '/dashboard/query'
  })
});

const result = await response.json();
console.log('Decision:', result.action);
console.log('Rules triggered:', result.rule_ids);
```

Or through Flask Gateway:

```javascript
// Through Flask Gateway
const response = await fetch('http://localhost:5001/api/jimini/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: userInput,
    user_id: currentUser.id,
    endpoint: '/dashboard/query'
  })
});

const result = await response.json();
console.log('Decision:', result.decision);
console.log('Enterprise features:', result.jimini_version);
```

## 🎯 Production Deployment Checklist

Before deploying to production:

- [ ] Shadow mode is **disabled** (`JIMINI_SHADOW=0`)
- [ ] Rules file is correct and tested
- [ ] Health endpoint returns `loaded_rules > 0`
- [ ] Test evaluations detect PII correctly
- [ ] API key is changed from default
- [ ] Audit logs are being written
- [ ] Monitoring/alerting is configured
- [ ] Backup/disaster recovery planned

## 📚 Additional Resources

- **API Documentation:** See `README.md` for complete API reference
- **Rule Configuration:** See `policy_rules.yaml` for rule examples
- **Rule Packs:** See `packs/` directory for pre-built rule sets
- **Flask Integration:** See `flask_jimini_platform_integration.py`

## 🆘 Getting Help

If you're still having issues:

1. Run the health check:
   ```bash
   python check_jimini_status.py
   ```

2. Check the logs:
   ```bash
   tail -100 /tmp/jimini.log
   ```

3. Verify rules loading:
   ```bash
   python -c "from app.rules_loader import load_rules, rules_store; load_rules('policy_rules.yaml'); print(f'Loaded {len(rules_store)} rules')"
   ```

4. Test a simple API call:
   ```bash
   curl -X POST http://localhost:9000/v1/evaluate \
     -H "Content-Type: application/json" \
     -d '{"api_key":"changeme","agent_id":"test","text":"hello","direction":"outbound","endpoint":"/test"}' | jq
   ```

## ✅ Success Indicators

Your integration is working correctly when:

- ✅ `check_jimini_status.py` shows all green checkmarks
- ✅ `/health` endpoint returns `loaded_rules > 0`
- ✅ Test API calls with PII trigger appropriate rules
- ✅ React dashboard can successfully evaluate user input
- ✅ Audit logs are being created in `logs/audit.jsonl`
- ✅ Metrics show decision counts increasing

**You're all set! Your React/Flask dashboard now has enterprise-grade AI policy protection! 🛡️**
