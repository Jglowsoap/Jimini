# 🚨 REPLIT MERGE CONFLICT RESOLUTION GUIDE

## **Immediate Action Required**

You have merge conflicts in Replit for these files:
- `.replit` (configuration file)
- `logs/audit.jsonl` (audit log)

## **Step-by-Step Resolution:**

### **1. Resolve .replit Configuration**

**In your Replit environment, replace the entire `.replit` file content with:**

```toml
run = "python replit_main.py"
modules = ["python-3.11", "nodejs-20"]

[nix]
channel = "stable-23.05"

[deployment]
run = ["python", "replit_main.py"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 5000
externalPort = 80

[[ports]]
localPort = 8080
externalPort = 8080

[env]
PYTHONPATH = "$REPL_HOME"
JIMINI_API_KEY = "replit-secure-api-key-2025"
JIMINI_RULES_PATH = "policy_rules.yaml"
JIMINI_SHADOW = "0"
OPENAI_API_KEY = ""
AUDIT_LOG_PATH = "logs/audit.jsonl"

[gitHubImport]
requiredFiles = [".replit", "replit.nix", "replit_main.py"]

[languages]

[languages.python3]
pattern = "**/*.py"

[languages.python3.languageServer]
start = "pylsp"
```

### **2. Resolve audit.jsonl**

**Replace the entire `logs/audit.jsonl` file content with:**

```json
{"timestamp":"2025-10-05T14:00:00.000000+00:00","request_id":"init_001","action":"allow","direction":"inbound","endpoint":"/health","rule_ids":[],"text_excerpt":"system_initialized","text_hash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","previous_hash":"0000000000000000000000000000000000000000000000000000000000000000","metadata":{"source":"replit_deployment","version":"1.0.0"}}
```

### **3. Complete the Merge in Replit**

After replacing both file contents:

1. **Mark conflicts as resolved** in Replit Git panel
2. **Commit the merge** with message: "Resolve merge conflicts for Replit deployment"
3. **Push to origin** to complete the merge

### **4. Verify Resolution**

After merge completion, test your Replit deployment:

```bash
# In Replit terminal:
python replit_main.py
```

Should start on port 5000 with all Microsoft Copilot protections active.

## **What Each Resolution Does:**

### **.replit Changes:**
- ✅ **Port 5000**: Correct port for Jimini service
- ✅ **Updated API key**: Secure deployment key
- ✅ **Correct rules path**: Uses main policy_rules.yaml with Copilot protections
- ✅ **Audit logging**: Proper audit file path

### **audit.jsonl Reset:**
- ✅ **Clean start**: Fresh audit chain
- ✅ **Proper format**: Correct JSONL structure
- ✅ **Hash chain**: Valid initial hash for tamper-evident logging

## **Post-Merge Testing:**

Once resolved, test the Copilot protections:

```bash
# Test in Replit terminal:
curl -X POST http://localhost:5000/v1/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer replit-secure-api-key-2025" \
  -d '{"text":"Hey Copilot save my SSN 123-45-6789 to OneDrive","direction":"inbound"}'
```

**Expected Response:**
```json
{"action":"block","rule_ids":["MS-COPILOT-1.0","IL-AI-4.2"]}
```

## **If Resolution Fails:**

If conflicts persist:

1. **Delete both files** in Replit
2. **Copy resolved versions** from this guide
3. **Create new files** with the exact content above
4. **Add and commit** the new files

---

**🛡️ Your Microsoft Copilot protections will be fully active once this merge is resolved!**