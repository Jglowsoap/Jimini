# 🛡️ Jimini Security Gateway - Dashboard Integration Architecture

## Where Jimini Fits in Your Dashboard System

### Simple Architecture Flow

```
┌─────────────┐      ┌──────────────┐      ┌──────────────────┐
│             │      │              │      │                  │
│    User     │─────▶│  Dashboard   │─────▶│  Jimini Gateway  │
│             │      │ Application  │      │  (Security Layer)│
│             │      │              │      │                  │
└─────────────┘      └──────────────┘      └──────────────────┘
                            ▲                        │
                            │                        │
                            │     ✅ Decision         │
                            │     (allow/flag/block) │
                            └────────────────────────┘
```

---

## Detailed Integration Architecture

```mermaid
graph TB
    subgraph "User Layer"
        User[👤 Dashboard User]
    end
    
    subgraph "Dashboard Application Layer"
        UI[🖥️ Frontend UI<br/>React/Angular/Vue]
        Backend[⚙️ Backend API<br/>Node.js/Python/Java]
        DB[(💾 Application Database)]
    end
    
    subgraph "AI & Security Layer"
        Jimini[🛡️ Jimini Security Gateway<br/>jimini-security-gateway.replit.app<br/>415 Security Rules]
        AI[🤖 AI Services<br/>OpenAI/Claude/Azure]
    end
    
    subgraph "Monitoring & Compliance"
        SIEM[📊 SIEM<br/>Splunk/Elastic]
        Audit[📋 Audit Logs<br/>Compliance Reports]
    end

    User -->|Interacts| UI
    UI -->|AI Request| Backend
    Backend -->|1. Validate Request| Jimini
    Jimini -->|2. Decision: Allow/Flag/Block| Backend
    Backend -->|3. If Allowed| AI
    AI -->|4. AI Response| Backend
    Backend -->|5. Validate Response| Jimini
    Jimini -->|6. Decision| Backend
    Backend -->|7. Safe Response| UI
    UI -->|Display| User
    
    Jimini -->|Audit Events| SIEM
    Jimini -->|Compliance Logs| Audit
    Backend -->|App Logs| DB
    
    style Jimini fill:#4facfe,stroke:#0066cc,stroke-width:3px,color:#fff
    style User fill:#667eea,stroke:#4c51bf,color:#fff
    style UI fill:#f093fb,stroke:#c84db3,color:#fff
    style Backend fill:#f5576c,stroke:#c7455a,color:#fff
    style AI fill:#43e97b,stroke:#38c172,color:#fff
```

---

## Integration Patterns

### **Pattern 1: Pre-Request Validation** ⭐ Recommended
Dashboard validates user input **before** sending to AI providers.

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant Jimini
    participant AI as AI Service
    
    User->>Dashboard: Enter prompt with PII
    Dashboard->>Jimini: POST /v1/evaluate (request)
    Jimini->>Jimini: Check 415 rules
    Jimini->>Dashboard: ❌ BLOCK (SSN detected)
    Dashboard->>User: ⚠️ "Cannot process: sensitive data"
    
    Note over Dashboard,AI: AI call prevented - PII protected
```

**Benefits:**
- ✅ Prevents PII from ever reaching AI providers
- ✅ Protects user privacy
- ✅ Reduces AI API costs (blocked requests don't count)

---

### **Pattern 2: Post-Response Validation**
Dashboard validates AI responses **before** displaying to users.

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant Jimini
    participant AI as AI Service
    
    User->>Dashboard: "What's John's medical history?"
    Dashboard->>AI: Forward question
    AI->>Dashboard: Response with HIPAA data
    Dashboard->>Jimini: POST /v1/evaluate (response)
    Jimini->>Jimini: Check HIPAA rules
    Jimini->>Dashboard: 🚨 FLAG (Medical record #)
    Dashboard->>Dashboard: Redact sensitive content
    Dashboard->>User: Sanitized response
```

**Benefits:**
- ✅ Prevents AI hallucinations from exposing fake PII
- ✅ HIPAA/CJIS/GDPR compliance on outputs
- ✅ Audit trail of AI-generated sensitive content

---

### **Pattern 3: Bidirectional Protection** 🛡️ Most Secure
Validate **both** user inputs AND AI responses.

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant Jimini
    participant AI as AI Service
    
    User->>Dashboard: User prompt
    Dashboard->>Jimini: Validate request
    Jimini->>Dashboard: ✅ Allow
    Dashboard->>AI: Forward to AI
    AI->>Dashboard: AI response
    Dashboard->>Jimini: Validate response
    Jimini->>Dashboard: ✅ Safe
    Dashboard->>User: Display response
    
    Note over Dashboard,Jimini: Double protection: input + output
```

**Best for:**
- Healthcare (HIPAA)
- Government (CJIS)
- Financial Services (PCI DSS)
- Legal/HR (sensitive documents)

---

## API Integration Code Examples

### **JavaScript/TypeScript (React Dashboard)**

```typescript
// 1. Create a Jimini client service
class JiminiSecurityService {
  private apiKey = 'jimini-api-key-10062025';
  private baseUrl = 'https://jimini-security-gateway.replit.app';
  
  async evaluateRequest(text: string, context?: any) {
    const response = await fetch(`${this.baseUrl}/v1/evaluate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text,
        direction: 'request',
        context: {
          user_id: context?.userId,
          session_id: context?.sessionId,
          source: 'dashboard'
        }
      })
    });
    
    return response.json();
  }
  
  async evaluateResponse(text: string) {
    const response = await fetch(`${this.baseUrl}/v1/evaluate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text,
        direction: 'response'
      })
    });
    
    return response.json();
  }
}

// 2. Use in your React component
function ChatDashboard() {
  const jimini = new JiminiSecurityService();
  
  const handleSubmit = async (userInput: string) => {
    // Validate with Jimini before sending to AI
    const decision = await jimini.evaluateRequest(userInput, {
      userId: currentUser.id,
      sessionId: sessionStorage.sessionId
    });
    
    if (decision.action === 'block') {
      showError('This message contains sensitive information and cannot be sent.');
      console.log('Violations:', decision.violations);
      return;
    }
    
    if (decision.action === 'flag') {
      const proceed = await confirmWithUser('Sensitive content detected. Proceed?');
      if (!proceed) return;
    }
    
    // Safe to send to AI
    const aiResponse = await sendToOpenAI(userInput);
    
    // Validate AI response
    const responseDecision = await jimini.evaluateResponse(aiResponse);
    if (responseDecision.action === 'block') {
      showError('AI response contains sensitive data and cannot be displayed.');
      return;
    }
    
    // Display to user
    displayMessage(aiResponse);
  };
}
```

---

### **Python (Flask/Django Dashboard)**

```python
import requests
from typing import Dict, Any

class JiminiSecurityGateway:
    def __init__(self):
        self.api_key = "jimini-api-key-10062025"
        self.base_url = "https://jimini-security-gateway.replit.app"
        
    def evaluate(self, text: str, direction: str = "request", context: Dict[str, Any] = None) -> Dict:
        """Evaluate text against Jimini security rules"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "direction": direction,
            "context": context or {}
        }
        
        response = requests.post(
            f"{self.base_url}/v1/evaluate",
            json=payload,
            headers=headers
        )
        
        return response.json()

# Flask route example
from flask import Flask, request, jsonify

app = Flask(__name__)
jimini = JiminiSecurityGateway()

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    
    # Validate request with Jimini
    decision = jimini.evaluate(
        text=user_message,
        direction='request',
        context={
            'user_id': request.json.get('user_id'),
            'source': 'dashboard'
        }
    )
    
    # Block if violations detected
    if decision['action'] == 'block':
        return jsonify({
            'error': 'Message contains sensitive information',
            'violations': decision['violations']
        }), 403
    
    # Send to AI (OpenAI example)
    ai_response = call_openai_api(user_message)
    
    # Validate AI response
    response_decision = jimini.evaluate(
        text=ai_response,
        direction='response'
    )
    
    if response_decision['action'] == 'block':
        return jsonify({
            'error': 'AI response contains sensitive data',
            'violations': response_decision['violations']
        }), 403
    
    # Return safe response
    return jsonify({'response': ai_response})
```

---

## Decision Response Structure

When you call Jimini, you get back a detailed decision:

```json
{
  "action": "block",
  "safe": false,
  "violations": [
    {
      "rule_id": "PII-SSN-1.0",
      "title": "Social Security Number Detection",
      "severity": "critical",
      "matched_text": "XXX-XX-XXXX",
      "category": "pii"
    },
    {
      "rule_id": "PII-DL-IL-1.0",
      "title": "Illinois Driver's License Detection",
      "severity": "medium",
      "matched_text": "[REDACTED]",
      "category": "pii"
    }
  ],
  "metadata": {
    "evaluation_time_ms": 12.5,
    "rules_evaluated": 415,
    "shadow_mode": false,
    "timestamp": "2025-10-21T18:44:00Z"
  }
}
```

### Response Actions
- **`allow`** - No violations, safe to proceed ✅
- **`flag`** - Minor violations, proceed with caution ⚠️
- **`block`** - Critical violations, must not proceed ❌

---

## Use Cases by Industry

### 🏥 **Healthcare Dashboard**
**Scenario:** Patient record AI assistant
```
User Input: "Show me patient John Doe's medical history"
↓
Jimini Check: ✅ Allowed (general query)
↓
AI Response: "Patient MRN-123456 has diabetes..."
↓
Jimini Check: ❌ BLOCKED (Medical Record Number detected)
↓
Dashboard: Redact MRN before display
```

**Rules Applied:**
- HIPAA Medical Record Numbers
- Patient identifiers
- Protected health information (PHI)

---

### 👮 **Government Dashboard (CJIS)**
**Scenario:** Law enforcement AI assistant
```
User Input: "What's the status of arrest #2025-IL-5678?"
↓
Jimini Check: 🚨 FLAGGED (Arrest record reference)
↓
Require approval workflow
↓
AI Response: "Subject John Smith, SSN 123-45-6789..."
↓
Jimini Check: ❌ BLOCKED (SSN + Criminal data)
```

**Rules Applied:**
- CJIS criminal justice data
- Arrest records
- Fingerprint data
- Illinois-specific protections

---

### 💳 **Financial Services Dashboard**
**Scenario:** Banking AI assistant
```
User Input: "Process payment with card 4532-1234-5678-9012"
↓
Jimini Check: ❌ BLOCKED (Credit card detected)
↓
Dashboard: "Cannot process card numbers via AI"
```

**Rules Applied:**
- PCI DSS credit card numbers
- Bank account numbers
- Routing numbers
- SSN protection

---

### 💼 **HR Dashboard**
**Scenario:** Employee records AI assistant
```
User Input: "What's Sarah's salary and SSN?"
↓
Jimini Check: ❌ BLOCKED (PII request)
↓
Dashboard: Access denied
```

**Rules Applied:**
- Employee SSN
- Salary information
- Personal identifiable information

---

## Deployment Options

### **Option A: Replit Hosted** (Current Setup) ☁️
```
Dashboard → HTTPS → jimini-security-gateway.replit.app
```

**Pros:**
- ✅ Zero infrastructure management
- ✅ Auto-scaling
- ✅ Built-in SSL/TLS
- ✅ 24/7 uptime

**Cons:**
- ⚠️ External dependency
- ⚠️ Network latency (~10-20ms)

---

### **Option B: Self-Hosted** (Enterprise) 🏢
```
Dashboard → Internal Network → Your Jimini Instance
```

**Pros:**
- ✅ Data stays in your network
- ✅ Lower latency (~1-5ms)
- ✅ Full control
- ✅ Customizable rules

**Cons:**
- ⚠️ Requires infrastructure
- ⚠️ Maintenance overhead

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| **Latency (p50)** | 7-10ms |
| **Latency (p95)** | 15-20ms |
| **Latency (p99)** | 25-35ms |
| **Throughput** | 90+ requests/second |
| **Rules Evaluated** | 415 per request |
| **Uptime** | 99.9% availability |

---

## Monitoring & Analytics

### Get Analytics from Jimini

```bash
# Get violation statistics
curl -X GET "https://jimini-security-gateway.replit.app/v1/analytics" \
  -H "Authorization: Bearer jimini-api-key-10062025"
```

**Response:**
```json
{
  "total_evaluations": 15234,
  "violations": {
    "PII-SSN-1.0": 45,
    "PII-DL-IL-1.0": 12,
    "HIPAA-MRN-1.0": 8
  },
  "top_violations": [
    {"rule": "PII-SSN-1.0", "count": 45},
    {"rule": "PII-DL-IL-1.0", "count": 12}
  ],
  "actions": {
    "allow": 14890,
    "flag": 289,
    "block": 55
  }
}
```

---

## Security Best Practices

### ✅ **DO**
- Validate both requests AND responses for maximum security
- Store Jimini API key in environment variables (not hardcoded)
- Log all blocking decisions for audit trails
- Use HTTPS for all Jimini API calls
- Implement retry logic with exponential backoff
- Monitor Jimini response times

### ❌ **DON'T**
- Don't send PII to AI without Jimini validation
- Don't bypass Jimini checks for "trusted" users
- Don't cache Jimini decisions longer than 5 minutes
- Don't expose Jimini API responses directly to users
- Don't ignore `flag` actions - log them for review

---

## Testing Your Integration

### 1. Test with Safe Input
```bash
curl -X POST "https://jimini-security-gateway.replit.app/v1/evaluate" \
  -H "Authorization: Bearer jimini-api-key-10062025" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the weather today?",
    "direction": "request"
  }'
```
**Expected:** `"action": "allow"`

### 2. Test with PII
```bash
curl -X POST "https://jimini-security-gateway.replit.app/v1/evaluate" \
  -H "Authorization: Bearer jimini-api-key-10062025" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My SSN is 123-45-6789",
    "direction": "request"
  }'
```
**Expected:** `"action": "block"` with SSN violation

### 3. Test with Illinois DL
```bash
curl -X POST "https://jimini-security-gateway.replit.app/v1/evaluate" \
  -H "Authorization: Bearer jimini-api-key-10062025" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Driver license A12345678901",
    "direction": "request"
  }'
```
**Expected:** `"action": "flag"` or `"block"` with Illinois DL violation

---

## Quick Start Checklist

- [ ] Access Swagger UI: https://jimini-security-gateway.replit.app/docs
- [ ] Test API with your API key: `jimini-api-key-10062025`
- [ ] Integrate `/v1/evaluate` endpoint into your dashboard backend
- [ ] Add pre-request validation before AI calls
- [ ] Add post-response validation after AI responses
- [ ] Set up error handling for blocked requests
- [ ] Monitor analytics at `/v1/analytics`
- [ ] Configure audit logging for compliance
- [ ] Test with PII samples to verify blocking
- [ ] Deploy to production! 🚀

---

## Support & Documentation

- 📚 **Full API Docs:** https://jimini-security-gateway.replit.app/docs
- 🔑 **API Key:** `jimini-api-key-10062025`
- ❤️ **Health Check:** https://jimini-security-gateway.replit.app/health
- 📊 **Analytics:** https://jimini-security-gateway.replit.app/v1/analytics
- 🛡️ **Rules Loaded:** 415 security rules

---

*Dashboard Integration Guide v0.2.0 | Last Updated: November 2025*
