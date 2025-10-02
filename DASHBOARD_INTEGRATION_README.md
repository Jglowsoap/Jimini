# React/Flask Dashboard Integration - Quick Start

## ✅ Integration Status: COMPLETE

Your React/Flask dashboard is now fully integrated with the Jimini Platform!

## 🚀 Quick Start

### 1. Start Services (One Command)
```bash
python start_jimini_services.py
```

This starts:
- ✅ Jimini Platform on port 9000 (26 rules loaded)
- ✅ Flask Gateway on port 5001 (connected to Jimini)

### 2. Verify Everything Works
```bash
python check_jimini_status.py
```

Expected output:
```
✅ PASS: Jimini Platform (26 rules loaded)
✅ PASS: Flask Gateway (Connected)
✅ PASS: Evaluation (Working)
✅ PASS: Metrics (Available)
```

### 3. Your React Dashboard Can Now Call:

**Option A: Direct to Jimini (Simple)**
```javascript
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
```

**Option B: Through Flask Gateway (Recommended)**
```javascript
const response = await fetch('http://localhost:5001/api/jimini/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: userInput,
    user_id: currentUser.id,
    endpoint: '/dashboard/query'
  })
});
```

## 📚 Documentation

| File | Description |
|------|-------------|
| **INTEGRATION_COMPLETE.md** | Summary of what was fixed and how to use it |
| **REACT_FLASK_DASHBOARD_GUIDE.md** | Complete integration guide with troubleshooting |
| **REACT_INTEGRATION_EXAMPLES.jsx** | Working React component examples |

## 🛡️ What's Protected

Your dashboard now automatically detects and protects:
- ✅ Social Security Numbers (BLOCK)
- ✅ Email Addresses (FLAG)
- ✅ Phone Numbers (FLAG)
- ✅ Driver's Licenses (BLOCK)
- ✅ GitHub Tokens (BLOCK)
- ✅ AWS Keys (BLOCK)
- ✅ +20 more types of PII

## 🔍 Testing

Test with sample data:
```bash
# Safe text (should ALLOW)
curl -X POST http://localhost:9000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"api_key":"changeme","agent_id":"test","text":"Hello world","direction":"outbound","endpoint":"/test"}'

# SSN (should detect - currently in shadow mode)
curl -X POST http://localhost:9000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"api_key":"changeme","agent_id":"test","text":"SSN: 123-45-6789","direction":"outbound","endpoint":"/test"}'
```

## 🎯 Key Features

- ✅ **Real-time PII Detection** - SSN, email, phone, tokens, etc.
- ✅ **Tamper-proof Audit Chain** - SHA3-256 hash chain for compliance
- ✅ **Hot-reloadable Rules** - Update policies without restart
- ✅ **Shadow Mode** - Test without blocking (currently enabled)
- ✅ **SARIF Reports** - Government compliance reporting
- ✅ **Enterprise Analytics** - Metrics and monitoring

## 🔧 Troubleshooting

### Services Won't Start
```bash
# Check if ports are in use
lsof -i :9000
lsof -i :5001

# View logs
tail -f /tmp/jimini.log
```

### Rules Not Loading (0 rules)
```bash
# Verify rules file exists
ls -la policy_rules.yaml

# Test rules loading
python -c "from app.rules_loader import load_rules, rules_store; load_rules('policy_rules.yaml'); print(f'{len(rules_store)} rules loaded')"
```

### API Calls Failing
```bash
# Test Jimini health
curl http://localhost:9000/health | jq

# Test Flask gateway
curl http://localhost:5001/api/jimini/health | jq
```

## 📖 More Information

See `INTEGRATION_COMPLETE.md` for:
- What was fixed
- Complete API documentation
- React integration examples
- Production deployment guide
- Common issues & solutions

## ✨ You're All Set!

Your React/Flask dashboard is now protected by enterprise-grade AI policy enforcement! 🎉
